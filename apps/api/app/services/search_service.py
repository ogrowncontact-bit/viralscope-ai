import logging
import uuid

from app.core.cache import TTLCache
from app.integrations.job_queue import ArqJobQueue, JobQueueError
from app.integrations.youtube_client import YouTubeClient, YouTubeVideoData
from app.models.enums import TranscriptStatus
from app.models.search import Search
from app.models.video import Video
from app.repositories.interfaces.search_repository import SearchRepositoryProtocol
from app.repositories.interfaces.video_repository import VideoRepositoryProtocol

logger = logging.getLogger(__name__)


class SearchService:
    def __init__(
        self,
        repository: SearchRepositoryProtocol,
        video_repository: VideoRepositoryProtocol,
        youtube_client: YouTubeClient,
        search_cache: TTLCache[list[YouTubeVideoData]],
        job_queue: ArqJobQueue,
    ) -> None:
        self._repository = repository
        self._video_repository = video_repository
        self._youtube_client = youtube_client
        self._search_cache = search_cache
        self._job_queue = job_queue

    async def create_search(self, user_id: uuid.UUID, query: str) -> tuple[Search, list[Video]]:
        search = await self._repository.create(user_id, query.strip())

        cache_key = search.query.lower()
        results = self._search_cache.get(cache_key)
        if results is None:
            results = await self._youtube_client.search_videos(search.query)
            self._search_cache.set(cache_key, results)

        videos = [await self._video_repository.upsert(result) for result in results]

        await self._enqueue_pending_transcriptions(videos)

        return search, videos

    async def list_recent(self, user_id: uuid.UUID, limit: int = 10) -> list[Search]:
        return await self._repository.list_recent(user_id, limit)

    async def _enqueue_pending_transcriptions(self, videos: list[Video]) -> None:
        for video in videos:
            if video.transcript_status != TranscriptStatus.PENDING:
                continue
            try:
                await self._job_queue.enqueue_transcription(video.id)
            except JobQueueError:
                logger.warning(
                    "Falha ao enfileirar transcrição do vídeo %s; busca segue normalmente.",
                    video.id,
                    exc_info=True,
                )
