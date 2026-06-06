"""Add capacity to alert_type_enum.

Revision ID: 0014_add_capacity_alert_type
Revises: 0013_add_vehicle_capacity_fields
Create Date: 2026-06-06
"""

from alembic import op

revision = "0014_add_capacity_alert_type"
down_revision = "0013_add_vehicle_capacity_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE alert_type_enum ADD VALUE IF NOT EXISTS 'capacity'")


def downgrade() -> None:
    # PostgreSQL does not support removing enum values; downgrade is a no-op.
    pass
