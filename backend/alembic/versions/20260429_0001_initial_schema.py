"""Create initial backend schema.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-04-29 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    subscription_tier_enum = postgresql.ENUM(
        "starter", "pro", "enterprise", name="subscription_tier_enum", create_type=False
    )
    subscription_status_enum = postgresql.ENUM(
        "active", "past_due", "cancelled", "trialing", name="subscription_status_enum", create_type=False
    )
    user_role_enum = postgresql.ENUM(
        "superadmin", "admin", "operator", "dispatcher", "passenger", name="user_role_enum", create_type=False
    )
    vehicle_status_enum = postgresql.ENUM(
        "active", "idle", "maintenance", "offline", name="vehicle_status_enum", create_type=False
    )
    engine_status_enum = postgresql.ENUM("good", "warning", "critical", name="engine_status_enum", create_type=False)
    driver_status_enum = postgresql.ENUM(
        "available", "on-trip", "off-duty", name="driver_status_enum", create_type=False
    )
    trip_status_enum = postgresql.ENUM(
        "scheduled", "active", "completed", "cancelled", name="trip_status_enum", create_type=False
    )
    maintenance_type_enum = postgresql.ENUM(
        "routine", "repair", "inspection", name="maintenance_type_enum", create_type=False
    )
    maintenance_status_enum = postgresql.ENUM(
        "scheduled", "in-progress", "completed", name="maintenance_status_enum", create_type=False
    )
    alert_type_enum = postgresql.ENUM(
        "delay", "breakdown", "maintenance", "geofence", "speeding", "info", name="alert_type_enum", create_type=False
    )
    alert_severity_enum = postgresql.ENUM(
        "low", "medium", "high", "critical", name="alert_severity_enum", create_type=False
    )
    audit_action_type_enum = postgresql.ENUM(
        "create", "update", "soft_delete", "login", "impersonate", name="audit_action_type_enum", create_type=False
    )

    bind = op.get_bind()
    for enum_type in (
        subscription_tier_enum,
        subscription_status_enum,
        user_role_enum,
        vehicle_status_enum,
        engine_status_enum,
        driver_status_enum,
        trip_status_enum,
        maintenance_type_enum,
        maintenance_status_enum,
        alert_type_enum,
        alert_severity_enum,
        audit_action_type_enum,
    ):
        enum_type.create(bind, checkfirst=True)

    op.create_table(
        "tenants",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("contact_email", sa.String(), nullable=False),
        sa.Column("billing_email", sa.String(), nullable=True),
        sa.Column("subscription_tier", subscription_tier_enum, nullable=False),
        sa.Column("vehicle_limit", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("trial_ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "routes",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("number", sa.String(), nullable=False),
        sa.Column("distance", sa.Float(), nullable=False),
        sa.Column("duration", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("color", sa.String(), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_routes_tenant_id", "routes", ["tenant_id"])

    op.create_table(
        "stops",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("lat", sa.Float(), nullable=False),
        sa.Column("lng", sa.Float(), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_stops_tenant_id"), "stops", ["tenant_id"])

    op.create_table(
        "subscriptions",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("tier", subscription_tier_enum, nullable=False),
        sa.Column("status", subscription_status_enum, nullable=False),
        sa.Column("current_period_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("external_billing_id", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_subscriptions_tenant_id"), "subscriptions", ["tenant_id"])

    op.create_table(
        "users",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=True),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column("full_name", sa.String(), nullable=False),
        sa.Column("role", user_role_enum, nullable=False),
        sa.Column("phone", sa.String(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_tenant_id"), "users", ["tenant_id"])

    op.create_table(
        "vehicles",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("registration_number", sa.String(), nullable=False),
        sa.Column("model", sa.String(), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=False),
        sa.Column("status", vehicle_status_enum, nullable=False),
        sa.Column("lat", sa.Float(), nullable=True),
        sa.Column("lng", sa.Float(), nullable=True),
        sa.Column("speed", sa.Integer(), nullable=True),
        sa.Column("heading", sa.Integer(), nullable=True),
        sa.Column("fuel", sa.Integer(), nullable=True),
        sa.Column("engine_status", engine_status_enum, nullable=False),
        sa.Column("route_id", sa.String(), nullable=True),
        sa.Column("driver_id", sa.String(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_vehicles_tenant_id", "vehicles", ["tenant_id"])
    op.create_index("idx_vehicles_status", "vehicles", ["status"])

    op.create_table(
        "drivers",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("license_number", sa.String(), nullable=False),
        sa.Column("phone", sa.String(), nullable=False),
        sa.Column("rating", sa.Float(), nullable=False),
        sa.Column("total_trips", sa.Integer(), nullable=False),
        sa.Column("status", driver_status_enum, nullable=False),
        sa.Column("vehicle_id", sa.String(), nullable=True),
        sa.Column("certification_expiry", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_drivers_tenant_id", "drivers", ["tenant_id"])

    op.create_foreign_key("fk_vehicles_route_id_routes", "vehicles", "routes", ["route_id"], ["id"])
    op.create_foreign_key("fk_vehicles_driver_id_drivers", "vehicles", "drivers", ["driver_id"], ["id"])
    op.create_foreign_key("fk_drivers_vehicle_id_vehicles", "drivers", "vehicles", ["vehicle_id"], ["id"])

    op.create_table(
        "route_stops",
        sa.Column("route_id", sa.String(), nullable=False),
        sa.Column("stop_id", sa.String(), nullable=False),
        sa.Column("stop_order", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["route_id"], ["routes.id"]),
        sa.ForeignKeyConstraint(["stop_id"], ["stops.id"]),
        sa.PrimaryKeyConstraint("route_id", "stop_id"),
    )

    op.create_table(
        "trips",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("vehicle_id", sa.String(), nullable=False),
        sa.Column("route_id", sa.String(), nullable=False),
        sa.Column("driver_id", sa.String(), nullable=False),
        sa.Column("scheduled_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actual_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scheduled_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actual_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", trip_status_enum, nullable=False),
        sa.Column("passengers", sa.Integer(), nullable=False),
        sa.Column("delay", sa.Integer(), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["driver_id"], ["drivers.id"]),
        sa.ForeignKeyConstraint(["route_id"], ["routes.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_trips_tenant_id", "trips", ["tenant_id"])
    op.create_index("idx_trips_status", "trips", ["status"])

    op.create_table(
        "maintenance_records",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("vehicle_id", sa.String(), nullable=False),
        sa.Column("type", maintenance_type_enum, nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("scheduled_date", sa.Date(), nullable=False),
        sa.Column("completed_date", sa.Date(), nullable=True),
        sa.Column("cost", sa.Float(), nullable=False),
        sa.Column("status", maintenance_status_enum, nullable=False),
        sa.Column("next_due", sa.Date(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_maintenance_records_tenant_id", "maintenance_records", ["tenant_id"])

    op.create_table(
        "alerts",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("type", alert_type_enum, nullable=False),
        sa.Column("severity", alert_severity_enum, nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("vehicle_id", sa.String(), nullable=True),
        sa.Column("driver_id", sa.String(), nullable=True),
        sa.Column("is_acknowledged", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["driver_id"], ["drivers.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_alerts_tenant_id", "alerts", ["tenant_id"])
    op.create_index("idx_alerts_is_acknowledged", "alerts", ["is_acknowledged"])

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=True),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("entity_type", sa.String(), nullable=False),
        sa.Column("entity_id", sa.String(), nullable=False),
        sa.Column("action_type", audit_action_type_enum, nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_audit_logs_tenant_id", "audit_logs", ["tenant_id"])


def downgrade() -> None:
    op.drop_index("idx_audit_logs_tenant_id", table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_index("idx_alerts_is_acknowledged", table_name="alerts")
    op.drop_index("idx_alerts_tenant_id", table_name="alerts")
    op.drop_table("alerts")
    op.drop_index("idx_maintenance_records_tenant_id", table_name="maintenance_records")
    op.drop_table("maintenance_records")
    op.drop_index("idx_trips_status", table_name="trips")
    op.drop_index("idx_trips_tenant_id", table_name="trips")
    op.drop_table("trips")
    op.drop_table("route_stops")
    op.drop_constraint("fk_drivers_vehicle_id_vehicles", "drivers", type_="foreignkey")
    op.drop_constraint("fk_vehicles_driver_id_drivers", "vehicles", type_="foreignkey")
    op.drop_constraint("fk_vehicles_route_id_routes", "vehicles", type_="foreignkey")
    op.drop_index("idx_drivers_tenant_id", table_name="drivers")
    op.drop_table("drivers")
    op.drop_index("idx_vehicles_status", table_name="vehicles")
    op.drop_index("idx_vehicles_tenant_id", table_name="vehicles")
    op.drop_table("vehicles")
    op.drop_index(op.f("ix_users_tenant_id"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
    op.drop_index(op.f("ix_subscriptions_tenant_id"), table_name="subscriptions")
    op.drop_table("subscriptions")
    op.drop_index(op.f("ix_stops_tenant_id"), table_name="stops")
    op.drop_table("stops")
    op.drop_index("idx_routes_tenant_id", table_name="routes")
    op.drop_table("routes")
    op.drop_table("tenants")

    bind = op.get_bind()
    for enum_name in (
        "audit_action_type_enum",
        "alert_severity_enum",
        "alert_type_enum",
        "maintenance_status_enum",
        "maintenance_type_enum",
        "trip_status_enum",
        "driver_status_enum",
        "engine_status_enum",
        "vehicle_status_enum",
        "user_role_enum",
        "subscription_status_enum",
        "subscription_tier_enum",
    ):
        sa.Enum(name=enum_name).drop(bind, checkfirst=True)
