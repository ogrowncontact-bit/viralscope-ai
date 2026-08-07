import logging

from app.services.metrics_sync_service import MetricsSyncService
from app.workers.context import video_repository_scope

logger = logging.getLogger(__name__)


async def sync_video_metrics_job(ctx: dict) -> None:
    async with video_repository_scope() as video_repository:
        service = MetricsSyncService(video_repository, ctx["youtube_client"])
        updated = await service.sync_tracked_videos()
        logger.info("sync_video_metrics_job: %d vídeos atualizados.", updated)
