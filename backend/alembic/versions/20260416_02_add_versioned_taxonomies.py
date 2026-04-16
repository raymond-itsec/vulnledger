"""add versioned taxonomies

Revision ID: 20260416_02
Revises: 20260416_01
Create Date: 2026-04-16 22:45:00

"""

from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260416_02"
down_revision: Union[str, None] = "20260416_01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


DEFAULT_TAXONOMY = {
    "risk_level": [
        {"value": "critical", "label": "Critical", "sort_order": 0, "color": "#dc2626"},
        {"value": "high", "label": "High", "sort_order": 1, "color": "#ea580c"},
        {"value": "medium", "label": "Medium", "sort_order": 2, "color": "#d97706"},
        {"value": "low", "label": "Low", "sort_order": 3, "color": "#2563eb"},
        {"value": "informational", "label": "Informational", "sort_order": 4, "color": "#6b7280"},
    ],
    "remediation_status": [
        {"value": "open", "label": "Open", "sort_order": 0, "color": "#dc2626"},
        {"value": "in_progress", "label": "In Progress", "sort_order": 1, "color": "#ca8a04"},
        {"value": "resolved", "label": "Resolved", "sort_order": 2, "color": "#16a34a"},
        {"value": "accepted_risk", "label": "Accepted Risk", "sort_order": 3, "color": "#6b7280"},
        {"value": "false_positive", "label": "False Positive", "sort_order": 4, "color": "#9333ea"},
    ],
    "session_status": [
        {"value": "planned", "label": "Planned", "sort_order": 0, "color": "#6b7280"},
        {"value": "in_progress", "label": "In Progress", "sort_order": 1, "color": "#ca8a04"},
        {"value": "completed", "label": "Completed", "sort_order": 2, "color": "#16a34a"},
        {"value": "cancelled", "label": "Cancelled", "sort_order": 3, "color": "#dc2626"},
    ],
    "asset_type": [
        {"value": "repository", "label": "Source Code Repository", "sort_order": 0, "color": None},
        {"value": "browser_extension", "label": "Browser Extension", "sort_order": 1, "color": None},
        {"value": "web_application", "label": "Web Application", "sort_order": 2, "color": None},
        {"value": "api", "label": "API", "sort_order": 3, "color": None},
        {"value": "mobile_app", "label": "Mobile App", "sort_order": 4, "color": None},
        {"value": "other", "label": "Other", "sort_order": 5, "color": None},
    ],
}


def upgrade() -> None:
    op.create_table(
        "taxonomy_versions",
        sa.Column("taxonomy_version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_current", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("taxonomy_version_id"),
        sa.UniqueConstraint("version_number"),
    )
    op.create_table(
        "taxonomy_entries",
        sa.Column("taxonomy_entry_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("taxonomy_version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("domain", sa.String(length=50), nullable=False),
        sa.Column("value", sa.String(length=100), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("color", sa.String(length=32), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["taxonomy_version_id"],
            ["taxonomy_versions.taxonomy_version_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("taxonomy_entry_id"),
        sa.UniqueConstraint(
            "taxonomy_version_id", "domain", "value", name="uq_taxonomy_entry_value"
        ),
    )

    default_version_id = uuid.uuid4()
    taxonomy_entry_rows = []
    for domain, entries in DEFAULT_TAXONOMY.items():
        for entry in entries:
            taxonomy_entry_rows.append(
                {
                    "taxonomy_entry_id": uuid.uuid4(),
                    "taxonomy_version_id": default_version_id,
                    "domain": domain,
                    "value": entry["value"],
                    "label": entry["label"],
                    "sort_order": entry["sort_order"],
                    "color": entry["color"],
                    "is_active": True,
                }
            )

    taxonomy_versions = sa.table(
        "taxonomy_versions",
        sa.column("taxonomy_version_id", postgresql.UUID(as_uuid=True)),
        sa.column("version_number", sa.Integer()),
        sa.column("description", sa.Text()),
        sa.column("is_current", sa.Boolean()),
    )
    taxonomy_entries = sa.table(
        "taxonomy_entries",
        sa.column("taxonomy_entry_id", postgresql.UUID(as_uuid=True)),
        sa.column("taxonomy_version_id", postgresql.UUID(as_uuid=True)),
        sa.column("domain", sa.String()),
        sa.column("value", sa.String()),
        sa.column("label", sa.String()),
        sa.column("sort_order", sa.Integer()),
        sa.column("color", sa.String()),
        sa.column("is_active", sa.Boolean()),
    )

    op.bulk_insert(
        taxonomy_versions,
        [
            {
                "taxonomy_version_id": default_version_id,
                "version_number": 1,
                "description": "System default taxonomy",
                "is_current": True,
            }
        ],
    )
    op.bulk_insert(taxonomy_entries, taxonomy_entry_rows)

    op.add_column(
        "report_exports",
        sa.Column("taxonomy_version_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.execute(
        sa.text(
            "UPDATE report_exports SET taxonomy_version_id = :taxonomy_version_id "
            "WHERE taxonomy_version_id IS NULL"
        ).bindparams(taxonomy_version_id=default_version_id)
    )
    op.alter_column("report_exports", "taxonomy_version_id", nullable=False)
    op.create_foreign_key(
        "fk_report_exports_taxonomy_version_id",
        "report_exports",
        "taxonomy_versions",
        ["taxonomy_version_id"],
        ["taxonomy_version_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_report_exports_taxonomy_version_id", "report_exports", type_="foreignkey"
    )
    op.drop_column("report_exports", "taxonomy_version_id")
    op.drop_table("taxonomy_entries")
    op.drop_table("taxonomy_versions")
