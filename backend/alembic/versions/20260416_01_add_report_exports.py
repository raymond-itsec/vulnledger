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


def _has_index(inspector, table_name: str, index_name: str) -> bool:
    return any(index["name"] == index_name for index in inspector.get_indexes(table_name))


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    table_names = set(inspector.get_table_names())

    if "clients" not in table_names:
        op.create_table(
            "clients",
            sa.Column("client_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("company_name", sa.String(length=255), nullable=False),
            sa.Column("primary_contact_name", sa.String(length=255), nullable=True),
            sa.Column("primary_contact_email", sa.String(length=255), nullable=True),
            sa.Column(
                "metadata",
                postgresql.JSONB(astext_type=sa.Text()),
                server_default=sa.text("'{}'::jsonb"),
                nullable=False,
            ),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.PrimaryKeyConstraint("client_id"),
            sa.UniqueConstraint("company_name"),
        )
        table_names.add("clients")

    if "users" not in table_names:
        op.create_table(
            "users",
            sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("username", sa.String(length=100), nullable=False),
            sa.Column("password_hash", sa.String(length=255), nullable=False),
            sa.Column("full_name", sa.String(length=255), nullable=True),
            sa.Column("company_name", sa.String(length=255), nullable=True),
            sa.Column("email", sa.String(length=255), nullable=False),
            sa.Column("role", sa.String(length=20), nullable=False),
            sa.Column("linked_client_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.CheckConstraint(
                "role != 'client_user' OR linked_client_id IS NOT NULL",
                name="ck_client_user_has_client",
            ),
            sa.ForeignKeyConstraint(["linked_client_id"], ["clients.client_id"]),
            sa.PrimaryKeyConstraint("user_id"),
            sa.UniqueConstraint("email"),
            sa.UniqueConstraint("username"),
        )
        table_names.add("users")

    if "reviewed_assets" not in table_names:
        op.create_table(
            "reviewed_assets",
            sa.Column("asset_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("client_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("asset_name", sa.String(length=255), nullable=False),
            sa.Column("asset_type", sa.String(length=50), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column(
                "metadata",
                postgresql.JSONB(astext_type=sa.Text()),
                server_default=sa.text("'{}'::jsonb"),
                nullable=False,
            ),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(["client_id"], ["clients.client_id"]),
            sa.PrimaryKeyConstraint("asset_id"),
        )
        table_names.add("reviewed_assets")

    if "review_sessions" not in table_names:
        op.create_table(
            "review_sessions",
            sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("asset_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("review_name", sa.String(length=255), nullable=False),
            sa.Column("review_date", sa.Date(), nullable=False),
            sa.Column("reviewer_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("status", sa.String(length=30), nullable=False),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(["asset_id"], ["reviewed_assets.asset_id"]),
            sa.ForeignKeyConstraint(["reviewer_id"], ["users.user_id"]),
            sa.PrimaryKeyConstraint("session_id"),
        )
        table_names.add("review_sessions")

    if "findings" not in table_names:
        op.create_table(
            "findings",
            sa.Column("finding_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("title", sa.String(length=500), nullable=False),
            sa.Column("description", sa.Text(), nullable=False),
            sa.Column("risk_level", sa.String(length=20), nullable=False),
            sa.Column("impact", sa.Text(), nullable=True),
            sa.Column("recommendation", sa.Text(), nullable=True),
            sa.Column("remediation_status", sa.String(length=30), nullable=False),
            sa.Column("references", postgresql.ARRAY(sa.String()), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(["session_id"], ["review_sessions.session_id"]),
            sa.PrimaryKeyConstraint("finding_id"),
        )
        table_names.add("findings")

    if "finding_history" not in table_names:
        op.create_table(
            "finding_history",
            sa.Column("history_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("finding_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("changed_by", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column(
                "changed_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.Column("field_name", sa.String(length=100), nullable=False),
            sa.Column("old_value", sa.Text(), nullable=True),
            sa.Column("new_value", sa.Text(), nullable=True),
            sa.ForeignKeyConstraint(["changed_by"], ["users.user_id"]),
            sa.ForeignKeyConstraint(["finding_id"], ["findings.finding_id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("history_id"),
        )
        table_names.add("finding_history")

    if "finding_attachments" not in table_names:
        op.create_table(
            "finding_attachments",
            sa.Column("attachment_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("finding_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("file_name", sa.String(length=255), nullable=False),
            sa.Column("storage_key", sa.String(length=500), nullable=False),
            sa.Column("content_type", sa.String(length=100), nullable=True),
            sa.Column("size_bytes", sa.BigInteger(), nullable=True),
            sa.Column("uploaded_by", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column(
                "uploaded_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(["finding_id"], ["findings.finding_id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["uploaded_by"], ["users.user_id"]),
            sa.PrimaryKeyConstraint("attachment_id"),
        )
        table_names.add("finding_attachments")

    if "finding_templates" not in table_names:
        op.create_table(
            "finding_templates",
            sa.Column("template_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("stable_id", sa.String(length=100), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("category", sa.String(length=100), nullable=True),
            sa.Column("is_builtin", sa.Boolean(), nullable=False),
            sa.Column("title", sa.String(length=500), nullable=True),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("risk_level", sa.String(length=20), nullable=True),
            sa.Column("impact", sa.Text(), nullable=True),
            sa.Column("recommendation", sa.Text(), nullable=True),
            sa.Column("references", postgresql.ARRAY(sa.String()), nullable=True),
            sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(["created_by"], ["users.user_id"]),
            sa.PrimaryKeyConstraint("template_id"),
            sa.UniqueConstraint("stable_id"),
        )
        table_names.add("finding_templates")

    if "report_exports" not in table_names:
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
            sa.Column(
                "exported_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(["created_by"], ["users.user_id"]),
            sa.ForeignKeyConstraint(
                ["session_id"], ["review_sessions.session_id"], ondelete="CASCADE"
            ),
            sa.PrimaryKeyConstraint("export_id"),
        )
        table_names.add("report_exports")
        inspector = sa.inspect(bind)

    if not _has_index(inspector, "report_exports", "ix_report_exports_session_id"):
        op.create_index("ix_report_exports_session_id", "report_exports", ["session_id"])
    if not _has_index(inspector, "report_exports", "ix_report_exports_exported_at"):
        op.create_index("ix_report_exports_exported_at", "report_exports", ["exported_at"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    table_names = set(inspector.get_table_names())

    if "report_exports" in table_names:
        if _has_index(inspector, "report_exports", "ix_report_exports_exported_at"):
            op.drop_index("ix_report_exports_exported_at", table_name="report_exports")
        if _has_index(inspector, "report_exports", "ix_report_exports_session_id"):
            op.drop_index("ix_report_exports_session_id", table_name="report_exports")
        op.drop_table("report_exports")

    for table_name in (
        "finding_attachments",
        "finding_history",
        "finding_templates",
        "findings",
        "review_sessions",
        "reviewed_assets",
        "users",
        "clients",
    ):
        if table_name in table_names:
            op.drop_table(table_name)
