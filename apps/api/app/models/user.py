from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    clerk_user_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    email: Mapped[str | None] = mapped_column(String(320), unique=True, nullable=True)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    searches: Mapped[list["Search"]] = relationship(back_populates="user")  # noqa: F821
    favorites: Mapped[list["Favorite"]] = relationship(back_populates="user")  # noqa: F821
    competitors: Mapped[list["Competitor"]] = relationship(back_populates="user")  # noqa: F821
    subscription: Mapped["Subscription | None"] = relationship(back_populates="user")  # noqa: F821
