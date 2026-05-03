"""Business metric collector.

Runs `SELECT COUNT` queries on each `/metrics` scrape and updates the
gauges in `app.middleware.metrics`. At our row counts (single-digit
thousands), each query is sub-millisecond. If we ever scale to millions
of rows, replace with a periodic background refresh that writes into a
cache; the gauges then expose the cached value on each scrape.

Gauges with labels (e.g., findings by risk_level) are RESET each scrape
so a label combination that disappears (no users with role X anymore)
correctly drops to 0 in the next observation rather than staying at the
stale prior value.
"""
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.middleware.metrics import (
    ASSETS_COUNT,
    ATTACHMENTS_COUNT,
    CLIENTS_COUNT,
    FINDINGS_COUNT,
    INVITES_PENDING_COUNT,
    REPORT_EXPORTS_COUNT,
    SESSIONS_COUNT,
    USERS_COUNT,
)
from app.models.client import Client
from app.models.finding import Finding
from app.models.finding_attachment import FindingAttachment
from app.models.invite import Invite
from app.models.report_export import ReportExport
from app.models.review_session import ReviewSession
from app.models.reviewed_asset import ReviewedAsset
from app.models.user import User


async def collect_business_metrics(db: AsyncSession) -> None:
    """Update all business gauges from a single async DB session.

    Each gauge update is independent; we issue 8 small queries.
    """
    # Simple counts (no labels)
    CLIENTS_COUNT.set(await _count(db, Client))
    ASSETS_COUNT.set(await _count(db, ReviewedAsset))
    SESSIONS_COUNT.set(await _count(db, ReviewSession))
    ATTACHMENTS_COUNT.set(await _count(db, FindingAttachment))

    # Pending invites = not yet claimed and not yet revoked. Expiry
    # check via `expires_at IS NULL OR expires_at > NOW()` would be
    # more accurate but the column is nullable in practice; the
    # claimed/revoked check is the practical "still actionable" filter.
    pending = await db.execute(
        select(func.count())
        .select_from(Invite)
        .where(Invite.claimed_at.is_(None))
        .where(Invite.revoked_at.is_(None))
    )
    INVITES_PENDING_COUNT.set(pending.scalar() or 0)

    # Findings by risk_level. `clear()` so empty buckets correctly
    # disappear instead of carrying stale values forward.
    FINDINGS_COUNT.clear()
    rows = await db.execute(
        select(Finding.risk_level, func.count())
        .group_by(Finding.risk_level)
    )
    for risk_level, count in rows.all():
        FINDINGS_COUNT.labels(risk_level=str(risk_level or "unknown")).set(count)

    # Users by role + active state.
    USERS_COUNT.clear()
    rows = await db.execute(
        select(User.role, User.is_active, func.count())
        .group_by(User.role, User.is_active)
    )
    for role, is_active, count in rows.all():
        USERS_COUNT.labels(
            role=str(role or "unknown"),
            is_active=str(bool(is_active)).lower(),
        ).set(count)

    # Report exports by format.
    REPORT_EXPORTS_COUNT.clear()
    rows = await db.execute(
        select(ReportExport.report_format, func.count())
        .group_by(ReportExport.report_format)
    )
    for fmt, count in rows.all():
        REPORT_EXPORTS_COUNT.labels(format=str(fmt or "unknown")).set(count)


async def _count(db: AsyncSession, model) -> int:
    result = await db.execute(select(func.count()).select_from(model))
    return result.scalar() or 0


__all__ = ["collect_business_metrics"]
