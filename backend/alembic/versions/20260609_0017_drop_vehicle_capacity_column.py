"""Drop redundant capacity column from vehicles; seating_capacity is authoritative.

Revision ID: 0017_drop_vehicle_capacity
Revises: 0016_boarding_route_id
Create Date: 2026-06-09
"""

import sqlalchemy as sa
from alembic import op

revision = "0017_drop_vehicle_capacity"
down_revision = "0016_boarding_route_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Preserve intent: copy capacity → seating_capacity where seating_capacity
    # still holds the default (45) but capacity was set to something different.
    op.execute(
        "UPDATE vehicles SET seating_capacity = capacity "
        "WHERE seating_capacity = 45 AND capacity <> 45"
    )
    op.drop_column("vehicles", "capacity")


def downgrade() -> None:
    op.add_column(
        "vehicles",
        sa.Column("capacity", sa.Integer(), nullable=False, server_default="45"),
    )
    op.execute("UPDATE vehicles SET capacity = seating_capacity")
