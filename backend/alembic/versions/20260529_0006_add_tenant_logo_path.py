"""Add tenant logo path.

Revision ID: 0006_add_tenant_logo_path
Revises: 0005_add_tenant_contact_fields
Create Date: 2026-05-29 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0006_add_tenant_logo_path"
down_revision: Union[str, None] = "0005_add_tenant_contact_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("tenants", sa.Column("logo_path", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("tenants", "logo_path")
