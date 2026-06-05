"""Add seating_capacity and current_occupancy to vehicles.

Revision ID: 0013_add_vehicle_capacity_fields
Revises: 0012_add_boarding_records
Create Date: 2026-06-06
"""

from alembic import op
import sqlalchemy as sa

revision = "0013_add_vehicle_capacity_fields"
down_revision = "0012_add_boarding_records"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "vehicles",
        sa.Column(
            "seating_capacity",
            sa.Integer(),
            nullable=False,
            server_default="45",
        ),
    )
    op.add_column(
        "vehicles",
        sa.Column(
            "current_occupancy",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )


def downgrade() -> None:
    op.drop_column("vehicles", "current_occupancy")
    op.drop_column("vehicles", "seating_capacity")
