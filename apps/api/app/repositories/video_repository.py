from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.youtube_client import YouTubeVideoData
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
