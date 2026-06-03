"""Add user invitation fields.

Revision ID: 0007_add_user_invitation_fields
Revises: 0006_add_tenant_logo_path
Create Date: 2026-06-03 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0007_add_user_invitation_fields"
down_revision: Union[str, None] = "0006_add_tenant_logo_path"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
    )
    op.add_column(
        "users",
        sa.Column("invitation_token_hash", sa.String(), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("invitation_expires_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "invitation_expires_at")
    op.drop_column("users", "invitation_token_hash")
    op.drop_column("users", "status")
