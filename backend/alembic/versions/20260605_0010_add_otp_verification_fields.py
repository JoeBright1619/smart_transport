"""Add OTP verification fields for passenger self-registration.

Revision ID: 0010_add_otp_verification_fields
Revises: 0009_partial_unique_email
Create Date: 2026-06-05 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0010_add_otp_verification_fields"
down_revision: Union[str, None] = "0009_partial_unique_email"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("otp_code", sa.String(), nullable=True))
    op.add_column(
        "users", sa.Column("otp_expires_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "users", sa.Column("otp_resent_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "users",
        sa.Column(
            "email_verified", sa.Boolean(), nullable=False, server_default="false"
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "email_verified")
    op.drop_column("users", "otp_resent_at")
    op.drop_column("users", "otp_expires_at")
    op.drop_column("users", "otp_code")
