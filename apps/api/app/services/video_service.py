import uuid

from app.integrations.job_queue import ArqJobQueue
from app.models.video import Video
from app.repositories.interfaces.video_repository import VideoRepositoryProtocol


class VideoService:
    def __init__(self, video_repository: VideoRepositoryProtocol, job_queue: ArqJobQueue) -> None:
        self._video_repository = video_repository
        self._job_queue = job_queue

    async def trigger_transcription(self, video_id: uuid.UUID) -> Video | None:
        video = await self._video_repository.get_by_id(video_id)
        if video is None:
            return None

        await self._job_queue.enqueue_transcription(video.id)
        return video
