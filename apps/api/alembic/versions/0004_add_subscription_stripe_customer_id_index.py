"""add index on subscriptions.stripe_customer_id

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-07

"""

from collections.abc import Sequence

from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "ix_subscriptions_stripe_customer_id",
        "subscriptions",
        ["stripe_customer_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_subscriptions_stripe_customer_id", table_name="subscriptions")
