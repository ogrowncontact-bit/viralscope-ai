import logging
import uuid

from app.integrations.interfaces.transcription_client import (
    TranscriptionClientProtocol,
    TranscriptionError,
)
from app.models.enums import TranscriptStatus
from app.repositories.interfaces.video_repository import VideoRepositoryProtocol

logger = logging.getLogger(__name__)

_RETRANSCRIBABLE_STATUSES = (TranscriptStatus.PENDING, TranscriptStatus.FAILED)


class TranscriptionService:
    def __init__(
        self,
        video_repository: VideoRepositoryProtocol,
        transcription_client: TranscriptionClientProtocol,
    ) -> None:
        self._video_repository = video_repository
        self._transcription_client = transcription_client

    async def transcribe_video(self, video_id: uuid.UUID) -> None:
        video = await self._video_repository.get_by_id(video_id)
        if video is None:
            logger.warning("transcribe_video: vídeo %s não encontrado.", video_id)
            return

        if video.transcript_status not in _RETRANSCRIBABLE_STATUSES:
            logger.info(
                "transcribe_video: vídeo %s já está em status %s, ignorando.",
                video_id,
                video.transcript_status,
            )
            return

        await self._video_repository.mark_transcript_processing(video_id)

        try:
            result = await self._transcription_client.transcribe(video.youtube_video_id)
        except TranscriptionError as exc:
            logger.exception("transcribe_video: falha ao transcrever vídeo %s.", video_id)
            await self._video_repository.mark_transcript_failed(video_id, str(exc))
            return

        await self._video_repository.save_transcript(
            video_id, text=result.text, language=result.language
        )
