"""Concurrency contract for the invite redemption flow (VL-2026-017).

Two truly concurrent redemption attempts against the same invite must
serialize at the invite row, not race into a downstream UNIQUE-
constraint collision via `users.email`. The first request claims the
invite + creates the user; the second blocks on the row lock until
the first commits, sees `claimed_at != NULL`, and rejects with a
401 'Invite verification required' error.

Closes #41.
"""

import asyncio
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from app.api.onboarding import _resolve_active_invite
from app.models.invite import Invite
from app.models.user import User
from app.services.onboarding import create_onboarding_token


@pytest.mark.asyncio
async def test_concurrent_resolve_with_lock_serializes_at_invite_row(test_engine):
    """Two parallel _resolve_active_invite(lock=True) calls against
    the same invite must NOT both succeed when the first has marked
    claimed_at. The row lock serializes them; the second sees
    claimed_at != NULL and raises HTTPException(401)."""
    maker = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    invite_id = uuid4()
    email = "racetest@example.com"
    code = "DEV-RACE-INVITE"

    # Seed an active invite directly.
    async with maker() as session:
        session.add(
            Invite(
                invite_id=invite_id,
                code=code,
                email=email,
                expires_at=datetime.now(timezone.utc) + timedelta(days=1),
            )
        )
        await session.commit()

    # Both concurrent calls use the same onboarding token signed for
    # this invite. Each runs in its own AsyncSession (mirrors what
    # FastAPI does per request via Depends(get_db)).
    raw_token = create_onboarding_token(invite_id, email, code)

    async def _redeem(idx: int):
        async with maker() as session:
            try:
                invite = await _resolve_active_invite(
                    session, raw_token, lock=True
                )
            except HTTPException as exc:
                return ("rejected", exc.status_code, str(exc.detail))

            # Simulate the redemption write: mark claimed_at and create
            # the user record. We do not run the full complete_onboarding
            # flow here - the contract is just "the row lock prevents
            # both from passing the claimed_at check."
            invite.claimed_at = datetime.now(timezone.utc)
            session.add(
                User(
                    username=f"racer-{idx}-{uuid4().hex[:6]}",
                    password_hash="not-used-in-test",
                    email=invite.email if idx == 1 else f"unique-{idx}@example.com",
                    role="reviewer",
                    is_active=True,
                )
            )
            await session.commit()
            return ("ok", None, None)

    results = await asyncio.gather(_redeem(1), _redeem(2))
    statuses = [r[0] for r in results]

    # Exactly one ok, exactly one rejected. Never two oks (would be
    # the bug); never two rejected (test setup error).
    assert statuses.count("ok") == 1, (
        f"Expected exactly one redemption to succeed, got: {results}"
    )
    assert statuses.count("rejected") == 1, (
        f"Expected the loser to receive a controlled rejection, got: {results}"
    )
    rejected = next(r for r in results if r[0] == "rejected")
    assert rejected[1] == 401, (
        f"Loser must surface 401 'Invite verification required', got status {rejected[1]}"
    )

    # And the DB shows exactly one user row tied to this email.
    async with maker() as session:
        users = (
            await session.execute(
                select(User).where(User.email == email)
            )
        ).scalars().all()
        assert len(users) == 1, (
            f"Expected exactly one user row for {email}; got {len(users)}."
        )

        # The invite is claimed exactly once.
        invite = (
            await session.execute(
                select(Invite).where(Invite.invite_id == invite_id)
            )
        ).scalar_one()
        assert invite.claimed_at is not None, "Winner must have set claimed_at"


@pytest.mark.asyncio
async def test_state_lookup_does_not_lock(db_session):
    """Sanity check: _resolve_active_invite(lock=False) returns the
    invite without acquiring a row lock. Used by the state endpoint
    so a tab polling 'is my invite still valid' never blocks
    parallel pollers from other tabs / clients."""
    invite_id = uuid4()
    email = "statetest@example.com"
    code = "DEV-STATE-INVITE"

    db_session.add(
        Invite(
            invite_id=invite_id,
            code=code,
            email=email,
            expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        )
    )
    await db_session.commit()

    raw_token = create_onboarding_token(invite_id, email, code)
    invite = await _resolve_active_invite(db_session, raw_token)  # lock=False default
    assert invite.email == email
    assert invite.claimed_at is None
