import uuid

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analysis import Analysis
from app.models.enums import AnalysisStatus


class SqlAlchemyAnalysisRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, video_id: uuid.UUID, user_id: uuid.UUID) -> Analysis:
        analysis = Analysis(video_id=video_id, user_id=user_id, status=AnalysisStatus.PENDING)
        self._session.add(analysis)
        await self._session.commit()
        await self._session.refresh(analysis)
        return analysis

    async def get_by_id(self, analysis_id: uuid.UUID) -> Analysis | None:
        return await self._session.get(Analysis, analysis_id)

    async def mark_processing(self, analysis_id: uuid.UUID) -> None:
        await self._session.execute(
            update(Analysis)
            .where(Analysis.id == analysis_id)
            .values(status=AnalysisStatus.PROCESSING)
        )
        await self._session.commit()

    async def save_result(
        self, analysis_id: uuid.UUID, *, viral_score: float, summary: str, insights: dict
    ) -> None:
        await self._session.execute(
            update(Analysis)
            .where(Analysis.id == analysis_id)
            .values(
                status=AnalysisStatus.COMPLETED,
                viral_score=viral_score,
                summary=summary,
                insights=insights,
                error=None,
                completed_at=func.now(),
            )
        )
        await self._session.commit()

    async def mark_failed(self, analysis_id: uuid.UUID, error: str) -> None:
        await self._session.execute(
            update(Analysis)
            .where(Analysis.id == analysis_id)
            .values(status=AnalysisStatus.FAILED, error=error)
        )
        await self._session.commit()

    async def count_by_user(self, user_id: uuid.UUID) -> int:
        result = await self._session.execute(
            select(func.count()).select_from(Analysis).where(Analysis.user_id == user_id)
        )
        return result.scalar_one()
