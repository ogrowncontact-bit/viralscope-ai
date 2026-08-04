import uuid

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.youtube_client import YouTubeVideoData
from app.models.enums import TranscriptStatus
from app.models.favorite import Favorite
from app.models.video import Video


class SqlAlchemyVideoRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert(self, data: YouTubeVideoData) -> Video:
        result = await self._session.execute(
            select(Video).where(Video.youtube_video_id == data.youtube_video_id)
        )
        video = result.scalar_one_or_none()

        if video is None:
            video = Video(youtube_video_id=data.youtube_video_id)
            self._session.add(video)

        video.youtube_channel_id = data.youtube_channel_id
        video.channel_title = data.channel_title
        video.title = data.title
        video.description = data.description
        video.thumbnail_url = data.thumbnail_url
        video.view_count = data.view_count
        video.like_count = data.like_count
        video.comment_count = data.comment_count
        video.duration_seconds = data.duration_seconds
        video.published_at = data.published_at

        await self._session.commit()
        await self._session.refresh(video)
        return video

    async def get_by_id(self, video_id: uuid.UUID) -> Video | None:
        return await self._session.get(Video, video_id)

    async def mark_transcript_processing(self, video_id: uuid.UUID) -> None:
        await self._session.execute(
            update(Video)
            .where(Video.id == video_id)
            .values(transcript_status=TranscriptStatus.PROCESSING)
        )
        await self._session.commit()

    async def save_transcript(self, video_id: uuid.UUID, text: str, language: str | None) -> None:
        await self._session.execute(
            update(Video)
            .where(Video.id == video_id)
            .values(
                transcript_status=TranscriptStatus.COMPLETED,
                transcript_text=text,
                transcript_language=language,
                transcript_error=None,
                transcript_completed_at=func.now(),
            )
        )
        await self._session.commit()

    async def mark_transcript_failed(self, video_id: uuid.UUID, error: str) -> None:
        await self._session.execute(
            update(Video)
            .where(Video.id == video_id)
            .values(transcript_status=TranscriptStatus.FAILED, transcript_error=error)
        )
        await self._session.commit()

    async def list_favorited_video_ids(self) -> list[str]:
        result = await self._session.execute(
            select(Video.youtube_video_id)
            .join(Favorite, Favorite.video_id == Video.id)
            .distinct()
        )
        return list(result.scalars().all())

    async def update_metrics(
        self, youtube_video_id: str, view_count: int, like_count: int, comment_count: int
    ) -> None:
        await self._session.execute(
            update(Video)
            .where(Video.youtube_video_id == youtube_video_id)
            .values(
                view_count=view_count,
                like_count=like_count,
                comment_count=comment_count,
                metrics_synced_at=func.now(),
            )
        )
        await self._session.commit()
