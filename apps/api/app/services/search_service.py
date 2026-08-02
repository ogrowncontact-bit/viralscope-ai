import uuid

from app.integrations.youtube_client import YouTubeClient
from app.models.search import Search
from app.models.video import Video
from app.repositories.interfaces.search_repository import SearchRepositoryProtocol
from app.repositories.interfaces.video_repository import VideoRepositoryProtocol


class SearchService:
    def __init__(
        self,
        repository: SearchRepositoryProtocol,
        video_repository: VideoRepositoryProtocol,
        youtube_client: YouTubeClient,
    ) -> None:
        self._repository = repository
        self._video_repository = video_repository
        self._youtube_client = youtube_client

    async def create_search(self, user_id: uuid.UUID, query: str) -> tuple[Search, list[Video]]:
        search = await self._repository.create(user_id, query.strip())

        results = await self._youtube_client.search_videos(search.query)
        videos = [await self._video_repository.upsert(result) for result in results]

        return search, videos

    async def list_recent(self, user_id: uuid.UUID, limit: int = 10) -> list[Search]:
        return await self._repository.list_recent(user_id, limit)
