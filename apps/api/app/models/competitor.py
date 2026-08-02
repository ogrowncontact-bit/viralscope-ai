import uuid

from sqlalchemy import BigInteger, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Competitor(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Canal do YouTube que um usuário decide acompanhar como concorrente."""

    __tablename__ = "competitors"
    __table_args__ = (
        UniqueConstraint("user_id", "youtube_channel_id", name="uq_competitors_user_channel"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    youtube_channel_id: Mapped[str] = mapped_column(String(64))
    channel_name: Mapped[str] = mapped_column(String(255))
    channel_thumbnail_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    subscriber_count: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    user: Mapped["User"] = relationship(back_populates="competitors")  # noqa: F821
