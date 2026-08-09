"""add analysis error and completed_at fields

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-07

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("analyses", sa.Column("error", sa.Text(), nullable=True))
    op.add_column("analyses", sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("analyses", "completed_at")
    op.drop_column("analyses", "error")
