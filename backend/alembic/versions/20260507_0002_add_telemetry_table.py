"""Add telemetry table.

Revision ID: 0002_add_telemetry_table
Revises: 0001_initial_schema
Create Date: 2026-05-07 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0002_add_telemetry_table"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "telemetry",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("vehicle_id", sa.String(), nullable=False),
        sa.Column("lat", sa.Float(), nullable=False),
        sa.Column("lng", sa.Float(), nullable=False),
        sa.Column("speed", sa.Integer(), nullable=False),
        sa.Column("heading", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_telemetry_tenant_id"), "telemetry", ["tenant_id"])
    op.create_index(op.f("ix_telemetry_vehicle_id"), "telemetry", ["vehicle_id"])
    op.create_index(
        "idx_telemetry_tenant_vehicle_timestamp",
        "telemetry",
        ["tenant_id", "vehicle_id", "timestamp"],
    )


def downgrade() -> None:
    op.drop_index("idx_telemetry_tenant_vehicle_timestamp", table_name="telemetry")
    op.drop_index(op.f("ix_telemetry_vehicle_id"), table_name="telemetry")
    op.drop_index(op.f("ix_telemetry_tenant_id"), table_name="telemetry")
    op.drop_table("telemetry")
