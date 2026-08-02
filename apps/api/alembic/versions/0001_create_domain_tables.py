"""create domain tables

Revision ID: 0001
Revises:
Create Date: 2026-08-02

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

analysis_status_enum = postgresql.ENUM(
    "pending", "processing", "completed", "failed", name="analysis_status"
)
subscription_plan_enum = postgresql.ENUM("free", "pro", "business", name="subscription_plan")
subscription_status_enum = postgresql.ENUM(
    "active", "trialing", "past_due", "canceled", "incomplete", name="subscription_status"
)

# Variantes usadas dentro das colunas: create_type=False evita que create_table tente
# recriar o tipo (ele já é criado explicitamente abaixo, antes das tabelas existirem).
analysis_status_column = postgresql.ENUM(
    "pending", "processing", "completed", "failed", name="analysis_status", create_type=False
)
subscription_plan_column = postgresql.ENUM(
    "free", "pro", "business", name="subscription_plan", create_type=False
)
subscription_status_column = postgresql.ENUM(
    "active",
    "trialing",
    "past_due",
    "canceled",
    "incomplete",
    name="subscription_status",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    analysis_status_enum.create(bind, checkfirst=True)
    subscription_plan_enum.create(bind, checkfirst=True)
    subscription_status_enum.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("clerk_user_id", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=True),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("avatar_url", sa.String(length=2048), nullable=True),
        sa.UniqueConstraint("clerk_user_id", name="uq_users_clerk_user_id"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_clerk_user_id", "users", ["clerk_user_id"])

    op.create_table(
        "videos",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("youtube_video_id", sa.String(length=32), nullable=False),
        sa.Column("youtube_channel_id", sa.String(length=64), nullable=False),
        sa.Column("channel_title", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("thumbnail_url", sa.String(length=2048), nullable=True),
        sa.Column("view_count", sa.BigInteger(), nullable=False),
        sa.Column("like_count", sa.BigInteger(), nullable=False),
        sa.Column("comment_count", sa.BigInteger(), nullable=False),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("youtube_video_id", name="uq_videos_youtube_video_id"),
    )
    op.create_index("ix_videos_youtube_video_id", "videos", ["youtube_video_id"])
    op.create_index("ix_videos_youtube_channel_id", "videos", ["youtube_channel_id"])

    op.create_table(
        "searches",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("query", sa.String(length=500), nullable=False),
        sa.Column("filters", postgresql.JSONB(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_searches_user_id", "searches", ["user_id"])

    op.create_table(
        "analyses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("video_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "status",
            analysis_status_column,
            nullable=False,
            server_default="pending",
        ),
        sa.Column("viral_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("insights", postgresql.JSONB(), nullable=True),
        sa.ForeignKeyConstraint(["video_id"], ["videos.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_analyses_video_id", "analyses", ["video_id"])
    op.create_index("ix_analyses_user_id", "analyses", ["user_id"])

    op.create_table(
        "favorites",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("video_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["video_id"], ["videos.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", "video_id", name="uq_favorites_user_video"),
    )
    op.create_index("ix_favorites_user_id", "favorites", ["user_id"])
    op.create_index("ix_favorites_video_id", "favorites", ["video_id"])

    op.create_table(
        "competitors",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("youtube_channel_id", sa.String(length=64), nullable=False),
        sa.Column("channel_name", sa.String(length=255), nullable=False),
        sa.Column("channel_thumbnail_url", sa.String(length=2048), nullable=True),
        sa.Column("subscriber_count", sa.BigInteger(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", "youtube_channel_id", name="uq_competitors_user_channel"),
    )
    op.create_index("ix_competitors_user_id", "competitors", ["user_id"])

    op.create_table(
        "subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("stripe_customer_id", sa.String(length=255), nullable=True),
        sa.Column("stripe_subscription_id", sa.String(length=255), nullable=True),
        sa.Column("plan", subscription_plan_column, nullable=False, server_default="free"),
        sa.Column("status", subscription_status_column, nullable=False, server_default="active"),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", name="uq_subscriptions_user_id"),
    )
    op.create_index("ix_subscriptions_user_id", "subscriptions", ["user_id"])


def downgrade() -> None:
    op.drop_table("subscriptions")
    op.drop_table("competitors")
    op.drop_table("favorites")
    op.drop_table("analyses")
    op.drop_table("searches")
    op.drop_table("videos")
    op.drop_table("users")

    subscription_status_enum.drop(op.get_bind(), checkfirst=True)
    subscription_plan_enum.drop(op.get_bind(), checkfirst=True)
    analysis_status_enum.drop(op.get_bind(), checkfirst=True)
