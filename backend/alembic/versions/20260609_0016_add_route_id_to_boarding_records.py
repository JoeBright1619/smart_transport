"""Add route_id to boarding_records for direct route lookup.

Revision ID: 0016_add_route_id_to_boarding_records
Revises: 0015_add_notification_threshold
Create Date: 2026-06-09
"""

import sqlalchemy as sa
from alembic import op

revision = "0016_boarding_route_id"
down_revision = "0015_add_notification_threshold"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "boarding_records",
        sa.Column("route_id", sa.String(), sa.ForeignKey("routes.id"), nullable=True),
    )
    op.create_index(
        "idx_boarding_route", "boarding_records", ["route_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index("idx_boarding_route", table_name="boarding_records")
    op.drop_column("boarding_records", "route_id")
