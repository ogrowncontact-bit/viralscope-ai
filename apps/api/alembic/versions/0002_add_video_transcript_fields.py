"""add video transcript fields

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-04

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

transcript_status_enum = postgresql.ENUM(
    "pending", "processing", "completed", "failed", name="transcript_status"
)
transcript_status_column = postgresql.ENUM(
    "pending", "processing", "completed", "failed", name="transcript_status", create_type=False
)


def upgrade() -> None:
    bind = op.get_bind()
    transcript_status_enum.create(bind, checkfirst=True)

    op.add_column(
        "videos",
        sa.Column(
            "transcript_status",
            transcript_status_column,
            nullable=False,
            server_default="pending",
        ),
    )
    op.add_column("videos", sa.Column("transcript_text", sa.Text(), nullable=True))
    op.add_column("videos", sa.Column("transcript_language", sa.String(length=16), nullable=True))
    op.add_column("videos", sa.Column("transcript_error", sa.Text(), nullable=True))
    op.add_column(
        "videos", sa.Column("transcript_completed_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "videos", sa.Column("metrics_synced_at", sa.DateTime(timezone=True), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("videos", "metrics_synced_at")
    op.drop_column("videos", "transcript_completed_at")
    op.drop_column("videos", "transcript_error")
    op.drop_column("videos", "transcript_language")
    op.drop_column("videos", "transcript_text")
    op.drop_column("videos", "transcript_status")

    transcript_status_enum.drop(op.get_bind(), checkfirst=True)
