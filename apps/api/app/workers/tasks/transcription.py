import uuid

from app.services.transcription_service import TranscriptionService
from app.workers.context import video_repository_scope


async def transcribe_video_job(ctx: dict, video_id: str) -> None:
    async with video_repository_scope() as video_repository:
        service = TranscriptionService(video_repository, ctx["transcription_client"])
        await service.transcribe_video(uuid.UUID(video_id))
