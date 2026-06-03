"""Change users.email unique index to partial (exclude soft-deleted rows).

Revision ID: 0009_partial_unique_email
Revises: 0008_add_invite_audit_actions
Create Date: 2026-06-03 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op


revision: str = "0009_partial_unique_email"
down_revision: Union[str, None] = "0008_add_invite_audit_actions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the full unique index, replace with a partial one that excludes
    # soft-deleted rows so the same email can be re-invited after deletion.
    op.drop_index("ix_users_email", table_name="users")
    op.execute(
        "CREATE UNIQUE INDEX ix_users_email ON users (email) WHERE is_deleted = false"
    )


def downgrade() -> None:
    op.drop_index("ix_users_email", table_name="users")
    op.create_index("ix_users_email", "users", ["email"], unique=True)
