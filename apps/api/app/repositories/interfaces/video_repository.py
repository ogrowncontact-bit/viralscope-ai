import uuid
from typing import Protocol

from app.integrations.youtube_client import YouTubeVideoData
from app.models.video import Video


class VideoRepositoryProtocol(Protocol):
    async def upsert(self, data: YouTubeVideoData) -> Video: ...

    async def get_by_id(self, video_id: uuid.UUID) -> Video | None: ...

    async def mark_transcript_processing(self, video_id: uuid.UUID) -> None: ...

    async def save_transcript(
        self, video_id: uuid.UUID, text: str, language: str | None
    ) -> None: ...

    async def mark_transcript_failed(self, video_id: uuid.UUID, error: str) -> None: ...

    async def list_favorited_video_ids(self) -> list[str]: ...

    async def update_metrics(
        self, youtube_video_id: str, view_count: int, like_count: int, comment_count: int
    ) -> None: ...
