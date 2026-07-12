"""Add journey rounds cap to vehicles (planned_loops / completed_loops).

Revision ID: 0018_vehicle_journey_loops
Revises: 0017_drop_vehicle_capacity
Create Date: 2026-07-12
"""

import sqlalchemy as sa
from alembic import op

revision = "0018_vehicle_journey_loops"
down_revision = "0017_drop_vehicle_capacity"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # planned_loops is the target number of route loops for the current journey
    # (NULL = uncapped); completed_loops counts loops finished so far.
    op.add_column(
        "vehicles",
        sa.Column("planned_loops", sa.Integer(), nullable=True),
    )
    op.add_column(
        "vehicles",
        sa.Column(
            "completed_loops",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )


def downgrade() -> None:
    op.drop_column("vehicles", "completed_loops")
    op.drop_column("vehicles", "planned_loops")
