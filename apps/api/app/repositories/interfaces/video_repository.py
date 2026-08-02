from typing import Protocol

from app.integrations.youtube_client import YouTubeVideoData
from app.models.video import Video


class VideoRepositoryProtocol(Protocol):
    async def upsert(self, data: YouTubeVideoData) -> Video: ...
