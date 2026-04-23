"""add refresh family lifetime cap

Revision ID: 20260423_02
Revises: 20260423_01
Create Date: 2026-04-23 12:00:00

Introduces an absolute lifetime cap on each refresh-token family. Prior
behaviour extended expiry with every rotation, so a leaked token could be
refreshed indefinitely. ``family_started_at`` is the immutable creation
time of the family; ``family_expires_at`` is the hard ceiling the
rotation logic now enforces.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260423_02"
down_revision: Union[str, None] = "20260423_01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "auth_refresh_sessions",
        sa.Column("family_started_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "auth_refresh_sessions",
        sa.Column("family_expires_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Backfill: a family's start is the earliest issued_at across its members;
    # cap is +30 days from that start, matching the new default.
    op.execute(
        """
        UPDATE auth_refresh_sessions AS a
        SET family_started_at = sub.min_issued
        FROM (
            SELECT family_id, MIN(issued_at) AS min_issued
            FROM auth_refresh_sessions
            GROUP BY family_id
        ) AS sub
        WHERE a.family_id = sub.family_id
        """
    )
    op.execute(
        """
        UPDATE auth_refresh_sessions
        SET family_expires_at = family_started_at + INTERVAL '30 days'
        WHERE family_expires_at IS NULL
        """
    )

    op.alter_column(
        "auth_refresh_sessions",
        "family_started_at",
        nullable=False,
    )
    op.alter_column(
        "auth_refresh_sessions",
        "family_expires_at",
        nullable=False,
    )
    op.create_index(
        "ix_auth_refresh_sessions_family_expires_at",
        "auth_refresh_sessions",
        ["family_expires_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_auth_refresh_sessions_family_expires_at",
        table_name="auth_refresh_sessions",
    )
    op.drop_column("auth_refresh_sessions", "family_expires_at")
    op.drop_column("auth_refresh_sessions", "family_started_at")
