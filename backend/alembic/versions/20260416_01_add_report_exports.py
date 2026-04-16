"""add report exports

Revision ID: 20260416_01
Revises: None
Create Date: 2026-04-16 21:40:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260416_01"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "report_exports",
        sa.Column("export_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("storage_key", sa.String(length=500), nullable=False),
        sa.Column("report_format", sa.String(length=20), nullable=False),
        sa.Column("content_type", sa.String(length=100), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("exported_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.user_id"]),
        sa.ForeignKeyConstraint(["session_id"], ["review_sessions.session_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("export_id"),
    )
    op.create_index("ix_report_exports_session_id", "report_exports", ["session_id"])
    op.create_index("ix_report_exports_exported_at", "report_exports", ["exported_at"])


def downgrade() -> None:
    op.drop_index("ix_report_exports_exported_at", table_name="report_exports")
    op.drop_index("ix_report_exports_session_id", table_name="report_exports")
    op.drop_table("report_exports")
