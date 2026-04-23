"""add oidc issuer/subject identity

Revision ID: 20260423_03
Revises: 20260423_02
Create Date: 2026-04-23 16:05:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260423_03"
down_revision: Union[str, None] = "20260423_02"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("oidc_issuer", sa.String(length=255), nullable=True))
    op.add_column("users", sa.Column("oidc_subject", sa.String(length=255), nullable=True))
    op.create_unique_constraint(
        "uq_users_oidc_identity",
        "users",
        ["oidc_issuer", "oidc_subject"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_users_oidc_identity", "users", type_="unique")
    op.drop_column("users", "oidc_subject")
    op.drop_column("users", "oidc_issuer")
