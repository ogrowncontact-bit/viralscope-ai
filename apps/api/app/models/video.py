from datetime import datetime

from sqlalchemy import BigInteger, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Video(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Catálogo de vídeos ingeridos do YouTube. Populado a partir do Módulo 3 (ingestão)."""

    __tablename__ = "videos"

    youtube_video_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    youtube_channel_id: Mapped[str] = mapped_column(String(64), index=True)
    channel_title: Mapped[str] = mapped_column(String(255))
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    thumbnail_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    view_count: Mapped[int] = mapped_column(BigInteger, default=0)
    like_count: Mapped[int] = mapped_column(BigInteger, default=0)
    comment_count: Mapped[int] = mapped_column(BigInteger, default=0)
    duration_seconds: Mapped[int | None] = mapped_column(nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    analyses: Mapped[list["Analysis"]] = relationship(back_populates="video")  # noqa: F821
    favorited_by: Mapped[list["Favorite"]] = relationship(back_populates="video")  # noqa: F821
