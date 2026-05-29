"""Add login_failed audit action.

Revision ID: 0004_add_login_failed_audit
Revises: 0003_add_analytics_table
Create Date: 2026-05-28 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op


revision: str = "0004_add_login_failed_audit"
down_revision: Union[str, None] = "0003_add_analytics_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute(
            "ALTER TYPE audit_action_type_enum ADD VALUE IF NOT EXISTS 'login_failed'"
        )


def downgrade() -> None:
    pass
