"""Add occupancy tables

Revision ID: be9989e72aa2
Revises: dbef00630ff8
Create Date: 2026-10-23 09:08:17.903288+00:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "be9989e72aa2"
down_revision: Union[str, None] = "dbef00630ff8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Native enum type must exist before the table that uses it.
    boarding_event_type = postgresql.ENUM(
        "boarded", "alighted", name="boarding_event_type", create_type=False
    )
    boarding_event_type.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "occupancy_events",
        sa.Column("id", sa.String(), primary_key=True, nullable=False),
        sa.Column(
            "tenant_id",
            sa.String(),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "vehicle_id",
            sa.String(),
            sa.ForeignKey("vehicles.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("stop_id", sa.String(), nullable=False),
        sa.Column("route_id", sa.String(), nullable=False),
        sa.Column("arrival_sequence", sa.Integer(), nullable=False),
        sa.Column("boardings", sa.Integer(), nullable=False),
        sa.Column("alightings", sa.Integer(), nullable=False),
        sa.Column("onboard", sa.Integer(), nullable=False),
        sa.Column("idempotency_key", sa.String(), nullable=False, unique=True),
        sa.Column("position_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("service_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "revenue_delta",
            sa.Numeric(10, 2),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "arrival_sequence >= 0", name="ck_occ_events_arrival_seq_nonneg"
        ),
        sa.CheckConstraint("boardings >= 0", name="ck_occ_events_boardings_nonneg"),
        sa.CheckConstraint("alightings >= 0", name="ck_occ_events_alightings_nonneg"),
        sa.CheckConstraint("onboard >= 0", name="ck_occ_events_onboard_nonneg"),
        sa.CheckConstraint("revenue_delta >= 0", name="ck_occ_events_revenue_nonneg"),
    )
    op.create_index(
        "ix_occupancy_events_vehicle_id_arrival_sequence",
        "occupancy_events",
        ["vehicle_id", "arrival_sequence"],
        unique=False,
    )
    op.create_index(
        "ix_occupancy_events_tenant_id_position_timestamp",
        "occupancy_events",
        ["tenant_id", "position_timestamp"],
        unique=False,
    )

    op.create_table(
        "boarding_passenger_events",
        sa.Column("id", sa.String(), primary_key=True, nullable=False),
        sa.Column(
            "occupancy_event_id",
            sa.String(),
            sa.ForeignKey("occupancy_events.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "passenger_id",
            sa.String(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "event_type",
            boarding_event_type,
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_boarding_passenger_events_occupancy_event_id",
        "boarding_passenger_events",
        ["occupancy_event_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_boarding_passenger_events_occupancy_event_id",
        table_name="boarding_passenger_events",
    )
    op.drop_table("boarding_passenger_events")

    op.drop_index(
        "ix_occupancy_events_tenant_id_position_timestamp",
        table_name="occupancy_events",
    )
    op.drop_index(
        "ix_occupancy_events_vehicle_id_arrival_sequence",
        table_name="occupancy_events",
    )
    op.drop_table("occupancy_events")

    postgresql.ENUM(name="boarding_event_type").drop(op.get_bind(), checkfirst=True)
