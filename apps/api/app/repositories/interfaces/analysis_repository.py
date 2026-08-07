import uuid
from typing import Protocol

from app.models.analysis import Analysis


class AnalysisRepositoryProtocol(Protocol):
    async def create(self, video_id: uuid.UUID, user_id: uuid.UUID) -> Analysis: ...

    async def get_by_id(self, analysis_id: uuid.UUID) -> Analysis | None: ...

    async def mark_processing(self, analysis_id: uuid.UUID) -> None: ...

    async def save_result(
        self, analysis_id: uuid.UUID, *, viral_score: float, summary: str, insights: dict
    ) -> None: ...

    async def mark_failed(self, analysis_id: uuid.UUID, error: str) -> None: ...

    async def count_by_user(self, user_id: uuid.UUID) -> int: ...
