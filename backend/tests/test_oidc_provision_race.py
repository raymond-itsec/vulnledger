"""Concurrency contract for OIDC auto-provision.

Two callbacks for the same first-time (issuer, subject) arriving
concurrently both pass the lookup and both try to insert a User. The
unique constraints (composite `oidc_issuer + oidc_subject`, plus
`username` and `email`) reject the loser. Closes #47.

These tests assert that the loser recovers gracefully: rollback, re-
read by (issuer, subject), and return the winner's user. Both
concurrent callers end up with the same user_id, no IntegrityError
leaks to the API layer.
"""

import asyncio

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from app.api.oidc import _resolve_or_create_user
from app.models.user import User


@pytest.mark.asyncio
async def test_concurrent_first_time_callbacks_resolve_to_same_user(test_engine):
    """Two simultaneous _resolve_or_create_user calls for the same
    new (issuer, subject) must both return a User with the same
    user_id. No IntegrityError leaks.
    """
    maker = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    issuer = "https://idp.example.com"
    subject = "abc-123-shared-subject"
    email = "racetest@example.com"
    userinfo = {"name": "Race Test", "preferred_username": "racetest"}

    async def _provision():
        async with maker() as session:
            return await _resolve_or_create_user(
                session,
                issuer=issuer,
                subject=subject,
                email=email,
                userinfo=userinfo,
            )

    user_a, user_b = await asyncio.gather(_provision(), _provision())

    assert user_a.user_id == user_b.user_id, (
        "Concurrent first-time OIDC callbacks for the same identity must "
        "resolve to a single user_id; got two distinct ids "
        f"({user_a.user_id} vs {user_b.user_id})."
    )
    assert user_a.oidc_issuer == issuer
    assert user_a.oidc_subject == subject

    # And only ONE row exists in the DB for that identity.
    async with maker() as session:
        rows = (
            await session.execute(
                select(User).where(
                    User.oidc_issuer == issuer,
                    User.oidc_subject == subject,
                )
            )
        ).scalars().all()
        assert len(rows) == 1, (
            f"Expected exactly one user row for ({issuer}, {subject}); "
            f"got {len(rows)}."
        )


@pytest.mark.asyncio
async def test_serial_lookup_after_provision_returns_existing(db_session):
    """Sanity check the non-racy path: a lookup right after provision
    returns the same user, no second insert."""
    issuer = "https://idp.example.com"
    subject = "xyz-456-serial"
    email = "serial@example.com"
    userinfo = {"name": "Serial Test"}

    user1 = await _resolve_or_create_user(
        db_session,
        issuer=issuer,
        subject=subject,
        email=email,
        userinfo=userinfo,
    )
    user2 = await _resolve_or_create_user(
        db_session,
        issuer=issuer,
        subject=subject,
        email=email,
        userinfo=userinfo,
    )
    assert user1.user_id == user2.user_id
