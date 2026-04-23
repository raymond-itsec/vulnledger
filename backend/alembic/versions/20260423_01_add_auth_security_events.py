"""add auth security events

Revision ID: 20260423_01
Revises: 20260417_02
Create Date: 2026-04-23 11:00:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260423_01"
down_revision: Union[str, None] = "20260417_02"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "auth_security_events",
        sa.Column("security_event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("family_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("refresh_session_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.String(length=512), nullable=True),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.user_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("security_event_id"),
    )
    op.create_index(
        "ix_auth_security_events_user_id_occurred_at",
        "auth_security_events",
        ["user_id", "occurred_at"],
        unique=False,
    )
    op.create_index(
        "ix_auth_security_events_event_type",
        "auth_security_events",
        ["event_type"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_auth_security_events_event_type", table_name="auth_security_events")
    op.drop_index("ix_auth_security_events_user_id_occurred_at", table_name="auth_security_events")
    op.drop_table("auth_security_events")
