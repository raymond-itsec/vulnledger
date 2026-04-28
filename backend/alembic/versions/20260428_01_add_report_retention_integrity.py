"""add report export retention and integrity metadata

Revision ID: 20260428_01
Revises: 20260423_03
Create Date: 2026-04-28 12:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260428_01"
down_revision: Union[str, None] = "20260423_03"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("report_exports", sa.Column("sha256", sa.String(length=64), nullable=True))
    op.add_column(
        "report_exports",
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "report_exports",
        sa.Column("retention_expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_report_exports_retention_expires_at",
        "report_exports",
        ["retention_expires_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_report_exports_retention_expires_at", table_name="report_exports")
    op.drop_column("report_exports", "retention_expires_at")
    op.drop_column("report_exports", "locked_until")
    op.drop_column("report_exports", "sha256")
