import uuid

from app.services.analysis_service import AnalysisService
from app.workers.context import analysis_repository_scope


async def analyze_video_job(ctx: dict, analysis_id: str) -> None:
    async with analysis_repository_scope() as (analysis_repository, video_repository):
        service = AnalysisService(
            analysis_repository=analysis_repository,
            video_repository=video_repository,
            analysis_client=ctx["analysis_client"],
            job_queue=ctx["job_queue"],
        )
        await service.run_analysis(uuid.UUID(analysis_id))
