import logging

from app.integrations.youtube_client import YouTubeAPIError, YouTubeClient
from app.repositories.interfaces.video_repository import VideoRepositoryProtocol

logger = logging.getLogger(__name__)

YOUTUBE_VIDEOS_BATCH_SIZE = 50


class MetricsSyncService:
    """Reconsulta a YouTube Data API para atualizar métricas dos vídeos acompanhados.

    "Acompanhado" hoje significa "favoritado por pelo menos um usuário" — o único conceito de
    vídeo monitorado que já existe no domínio.
    """

    def __init__(
        self, video_repository: VideoRepositoryProtocol, youtube_client: YouTubeClient
    ) -> None:
        self._video_repository = video_repository
        self._youtube_client = youtube_client

    async def sync_tracked_videos(self) -> int:
        video_ids = await self._video_repository.list_favorited_video_ids()
        if not video_ids:
            return 0

        updated = 0
        for batch_start in range(0, len(video_ids), YOUTUBE_VIDEOS_BATCH_SIZE):
            batch = video_ids[batch_start : batch_start + YOUTUBE_VIDEOS_BATCH_SIZE]
            try:
                videos = await self._youtube_client.fetch_videos_by_id(batch)
            except YouTubeAPIError:
                logger.exception("sync_tracked_videos: falha ao buscar lote na YouTube API.")
                continue

            for video in videos:
                await self._video_repository.update_metrics(
                    video.youtube_video_id,
                    view_count=video.view_count,
                    like_count=video.like_count,
                    comment_count=video.comment_count,
                )
                updated += 1

        return updated
