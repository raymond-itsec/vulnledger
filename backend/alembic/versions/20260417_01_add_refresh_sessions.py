"""add refresh sessions

Revision ID: 20260417_01
Revises: 20260416_02
Create Date: 2026-04-17 22:15:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260417_01"
down_revision: Union[str, None] = "20260416_02"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "auth_refresh_sessions",
        sa.Column("refresh_session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("family_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("parent_session_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("replaced_by_session_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_ip", sa.String(length=64), nullable=True),
        sa.Column("created_user_agent", sa.String(length=512), nullable=True),
        sa.Column("last_used_ip", sa.String(length=64), nullable=True),
        sa.Column("last_used_user_agent", sa.String(length=512), nullable=True),
        sa.Column("revoke_reason", sa.String(length=64), nullable=True),
        sa.ForeignKeyConstraint(
            ["parent_session_id"],
            ["auth_refresh_sessions.refresh_session_id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["replaced_by_session_id"],
            ["auth_refresh_sessions.refresh_session_id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.user_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("refresh_session_id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index(
        "ix_auth_refresh_sessions_user_id",
        "auth_refresh_sessions",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_auth_refresh_sessions_family_id",
        "auth_refresh_sessions",
        ["family_id"],
        unique=False,
    )
    op.create_index(
        "ix_auth_refresh_sessions_expires_at",
        "auth_refresh_sessions",
        ["expires_at"],
        unique=False,
    )
    op.create_index(
        "ix_auth_refresh_sessions_revoked_at",
        "auth_refresh_sessions",
        ["revoked_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_auth_refresh_sessions_revoked_at", table_name="auth_refresh_sessions")
    op.drop_index("ix_auth_refresh_sessions_expires_at", table_name="auth_refresh_sessions")
    op.drop_index("ix_auth_refresh_sessions_family_id", table_name="auth_refresh_sessions")
    op.drop_index("ix_auth_refresh_sessions_user_id", table_name="auth_refresh_sessions")
    op.drop_table("auth_refresh_sessions")
