"""make service_tokens.tenant_id nullable

Revision ID: 4ab6d44381f4
Revises: be9989e72aa2
Create Date: 2026-10-27 14:55:22.522518+00:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "4ab6d44381f4"
down_revision: Union[str, None] = "be9989e72aa2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "service_tokens",
        "tenant_id",
        existing_type=sa.String(),
        nullable=True,
    )


def downgrade() -> None:
    # Refuse to downgrade if any universal tokens exist — deleting them
    # would silently drop issuance history. Revoke them first.
    bind = op.get_bind()
    count = bind.execute(
        sa.text("SELECT COUNT(*) FROM service_tokens WHERE tenant_id IS NULL")
    ).scalar_one()
    if count > 0:
        raise RuntimeError(
            f"Cannot downgrade: {count} universal service_tokens exist. "
            "Revoke or delete them before downgrading."
        )
    op.alter_column(
        "service_tokens",
        "tenant_id",
        existing_type=sa.String(),
        nullable=False,
    )
