"""Add analytics table.

Revision ID: 0003_add_analytics_table
Revises: 0002_add_telemetry_table
Create Date: 2026-05-21 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0003_add_analytics_table"
down_revision: Union[str, None] = "0002_add_telemetry_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "analytics",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("total_fuel_consumption", sa.Float(), nullable=False),
        sa.Column("total_revenue", sa.Float(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_analytics_tenant_date",
        "analytics",
        ["tenant_id", "date"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("idx_analytics_tenant_date", table_name="analytics")
    op.drop_table("analytics")
