"""Add passenger_profiles table.

Revision ID: 0011_add_passenger_profile
Revises: 0010_add_otp_verification_fields
Create Date: 2026-06-05 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0011_add_passenger_profile"
down_revision: Union[str, None] = "0010_add_otp_verification_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "passenger_profiles",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=True),
        sa.Column("phone", sa.String(), nullable=True),
        sa.Column("preferred_routes", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("preferred_stops", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column(
            "notify_on_arrival", sa.Boolean(), nullable=False, server_default="true"
        ),
        sa.Column(
            "notify_on_delay", sa.Boolean(), nullable=False, server_default="true"
        ),
        sa.Column(
            "total_trips_recorded", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index("ix_passenger_profiles_user_id", "passenger_profiles", ["user_id"])
    op.create_index(
        "ix_passenger_profiles_tenant_id", "passenger_profiles", ["tenant_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_passenger_profiles_tenant_id", table_name="passenger_profiles")
    op.drop_index("ix_passenger_profiles_user_id", table_name="passenger_profiles")
    op.drop_table("passenger_profiles")
