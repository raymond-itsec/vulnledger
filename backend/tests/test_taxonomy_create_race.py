"""Concurrency contract for create_taxonomy_version.

Two admins creating taxonomy versions concurrently both compute
`max(version_number) + 1` from their snapshots and try to insert the
same value. The unique constraint rejects the loser. Closes #48.

These tests assert the race-handling shape: two concurrent calls
either both complete with distinct version numbers, or the loser
receives a controlled TaxonomyConflictError (which the API layer maps
to HTTP 409). They never produce an unhandled IntegrityError.
"""

import asyncio

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from app.models.taxonomy import TaxonomyVersion
from app.services.taxonomy import (
    TaxonomyConflictError,
    create_taxonomy_version,
)


def _payload(domain_value: str = "info"):
    """Smallest valid `domains=` payload accepted by the validator.

    Each created version needs every required taxonomy domain; we use a
    single trivial entry per domain so the focus stays on the version-
    number race rather than payload validation.
    """
    from app.schemas.taxonomy import TaxonomyEntryInput

    entry = TaxonomyEntryInput(
        value=domain_value,
        label=domain_value.capitalize(),
        sort_order=0,
        color="#000000",
        is_active=True,
    )
    return {
        "risk_level": [entry],
        "remediation_status": [entry],
        "session_status": [entry],
        "asset_type": [entry],
    }


@pytest.mark.asyncio
async def test_concurrent_creates_produce_distinct_version_numbers_or_clean_conflict(test_engine):
    """Two simultaneous create_taxonomy_version calls must both succeed
    OR the loser raises TaxonomyConflictError. No IntegrityError leaks.

    Each call gets its own AsyncSession (mirrors what the API does per
    request via Depends(get_db)). asyncio.gather drives the two calls
    concurrently against the same engine.
    """
    maker = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    async def _create(idx: int):
        async with maker() as session:
            try:
                bundle = await create_taxonomy_version(
                    session,
                    description=f"concurrent-{idx}",
                    domains=_payload(),
                    make_current=False,
                )
                return ("ok", bundle.version.version_number)
            except TaxonomyConflictError as exc:
                return ("conflict", str(exc))

    results = await asyncio.gather(_create(1), _create(2))

    statuses = [r[0] for r in results]

    # Both succeeding with distinct version numbers is the happy path.
    if statuses.count("ok") == 2:
        version_numbers = sorted(r[1] for r in results)
        assert version_numbers[0] != version_numbers[1], (
            "Both concurrent creates 'succeeded' with the same version_number; "
            "the unique constraint must be enforced."
        )
        return

    # If one lost the race, it must be a controlled conflict error
    # (NOT an unhandled IntegrityError - that's the bug being fixed).
    assert statuses.count("ok") == 1, (
        f"Expected at least one create to succeed, got: {results}"
    )
    assert statuses.count("conflict") == 1, (
        f"Expected the loser to raise TaxonomyConflictError, got: {results}"
    )


@pytest.mark.asyncio
async def test_serial_creates_get_consecutive_version_numbers(db_session):
    """Sanity check the non-racy path: two serial creates yield 1 and 2."""
    bundle1 = await create_taxonomy_version(
        db_session,
        description="serial-1",
        domains=_payload(),
        make_current=False,
    )
    bundle2 = await create_taxonomy_version(
        db_session,
        description="serial-2",
        domains=_payload(),
        make_current=False,
    )
    assert bundle1.version.version_number == 1
    assert bundle2.version.version_number == 2

    rows = (
        await db_session.execute(
            select(TaxonomyVersion).order_by(TaxonomyVersion.version_number)
        )
    ).scalars().all()
    assert [r.version_number for r in rows] == [1, 2]
