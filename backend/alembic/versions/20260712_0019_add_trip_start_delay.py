"""Add departure delay (start_delay) to trips.

Revision ID: 0019_trip_start_delay
Revises: 0018_vehicle_journey_loops
Create Date: 2026-07-12
"""

import sqlalchemy as sa
from alembic import op

revision = "0019_trip_start_delay"
down_revision = "0018_vehicle_journey_loops"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Signed minutes between actual and scheduled start, recorded when a trip activates.
    op.add_column(
        "trips",
        sa.Column(
            "start_delay",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )


def downgrade() -> None:
    op.drop_column("trips", "start_delay")
