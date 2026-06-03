"""Add invite and accept_invite audit action types.

Revision ID: 0008_add_invite_audit_actions
Revises: 0007_add_user_invitation_fields
Create Date: 2026-06-03 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op


revision: str = "0008_add_invite_audit_actions"
down_revision: Union[str, None] = "0007_add_user_invitation_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("ALTER TYPE audit_action_type_enum ADD VALUE IF NOT EXISTS 'invite'")
        op.execute(
            "ALTER TYPE audit_action_type_enum ADD VALUE IF NOT EXISTS 'accept_invite'"
        )


def downgrade() -> None:
    pass
