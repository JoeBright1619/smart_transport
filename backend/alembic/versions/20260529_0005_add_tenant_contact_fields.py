"""Add tenant contact fields.

Revision ID: 0005_add_tenant_contact_fields
Revises: 0004_add_login_failed_audit
Create Date: 2026-05-29 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0005_add_tenant_contact_fields"
down_revision: Union[str, None] = "0004_add_login_failed_audit"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("tenants", sa.Column("address", sa.String(), nullable=True))
    op.add_column("tenants", sa.Column("phone", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("tenants", "phone")
    op.drop_column("tenants", "address")
