"""Add boarding_records table.

Revision ID: 0012_add_boarding_records
Revises: 0011_add_passenger_profile
Create Date: 2026-06-05
"""

from alembic import op
import sqlalchemy as sa

revision = "0012_add_boarding_records"
down_revision = "0011_add_passenger_profile"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "boarding_records",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("trip_id", sa.String(), nullable=True),
        sa.Column("stop_id", sa.String(), nullable=False),
        sa.Column("passenger_id", sa.String(), nullable=True),
        sa.Column(
            "event_type",
            sa.Enum("boarded", "alighted", name="boarding_event_type_enum"),
            nullable=False,
        ),
        sa.Column("count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "recorded_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("occupancy_after", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["passenger_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["stop_id"], ["stops.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["trip_id"], ["trips.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_boarding_tenant", "boarding_records", ["tenant_id"])
    op.create_index("idx_boarding_stop", "boarding_records", ["stop_id"])
    op.create_index("idx_boarding_trip", "boarding_records", ["trip_id"])
    op.create_index("idx_boarding_passenger", "boarding_records", ["passenger_id"])
    op.create_index("idx_boarding_recorded_at", "boarding_records", ["recorded_at"])


def downgrade() -> None:
    op.drop_index("idx_boarding_recorded_at", table_name="boarding_records")
    op.drop_index("idx_boarding_passenger", table_name="boarding_records")
    op.drop_index("idx_boarding_trip", table_name="boarding_records")
    op.drop_index("idx_boarding_stop", table_name="boarding_records")
    op.drop_index("idx_boarding_tenant", table_name="boarding_records")
    op.drop_table("boarding_records")
    op.execute("DROP TYPE IF EXISTS boarding_event_type_enum")
