"""Add notification_threshold_minutes to passenger_profiles.

Revision ID: 0015_add_notification_threshold
Revises: 0014_add_capacity_alert_type
Create Date: 2026-06-08
"""

import sqlalchemy as sa
from alembic import op

revision = "0015_add_notification_threshold"
down_revision = "0014_add_capacity_alert_type"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "passenger_profiles",
        sa.Column(
            "notification_threshold_minutes",
            sa.Integer(),
            nullable=False,
            server_default="10",
        ),
    )


def downgrade() -> None:
    op.drop_column("passenger_profiles", "notification_threshold_minutes")
