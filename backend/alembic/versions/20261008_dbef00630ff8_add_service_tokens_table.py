"""add service_tokens table

Revision ID: dbef00630ff8
Revises: d7ef32e5127d
Create Date: 2026-10-08

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "dbef00630ff8"
down_revision: Union[str, None] = "d7ef32e5127d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "service_tokens",
        sa.Column("id", sa.String(), primary_key=True, nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("token_prefix", sa.String(), nullable=False),
        sa.Column("token_hash", sa.String(), nullable=False),
        sa.Column("scopes", sa.String(), nullable=False, server_default=""),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["tenant_id"], ["tenants.id"], name="fk_service_tokens_tenant_id"
        ),
    )
    op.create_index(
        "ix_service_tokens_tenant_id",
        "service_tokens",
        ["tenant_id"],
    )
    op.create_index(
        "ix_service_tokens_token_hash",
        "service_tokens",
        ["token_hash"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_service_tokens_token_hash", table_name="service_tokens")
    op.drop_index("ix_service_tokens_tenant_id", table_name="service_tokens")
    op.drop_table("service_tokens")
