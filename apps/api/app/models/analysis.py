import uuid

from sqlalchemy import Enum, ForeignKey, Numeric, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import AnalysisStatus
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Analysis(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Análise de IA sobre um vídeo (score de viralização, insights). Módulo 5 popula os dados."""

    __tablename__ = "analyses"

    video_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("videos.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    status: Mapped[AnalysisStatus] = mapped_column(
        Enum(AnalysisStatus, name="analysis_status"), default=AnalysisStatus.PENDING
    )
    viral_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    insights: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    video: Mapped["Video"] = relationship(back_populates="analyses")  # noqa: F821
    user: Mapped["User | None"] = relationship()  # noqa: F821
