import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import AnalysisStatus


class AnalysisInsightsOut(BaseModel):
    winning_titles: list[str]
    hooks: list[str]
    content_opportunities: list[str]


class AnalysisOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    video_id: uuid.UUID
    status: AnalysisStatus
    viral_score: float | None
    summary: str | None
    insights: AnalysisInsightsOut | None
    error: str | None
    created_at: datetime
    completed_at: datetime | None
