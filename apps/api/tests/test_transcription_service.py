import uuid
from unittest.mock import AsyncMock

from app.integrations.interfaces.transcription_client import (
    TranscriptionError,
    TranscriptionResult,
)
from app.models.enums import TranscriptStatus
from app.models.video import Video
from app.services.transcription_service import TranscriptionService


def _make_video(video_id: uuid.UUID, status: TranscriptStatus) -> Video:
    return Video(
        id=video_id,
        youtube_video_id="abc123",
        youtube_channel_id="channel-1",
        channel_title="Canal Teste",
        title="Vídeo de teste",
        view_count=0,
        like_count=0,
        comment_count=0,
        transcript_status=status,
    )


async def test_transcribe_video_does_nothing_when_video_not_found() -> None:
    repository = AsyncMock()
    repository.get_by_id.return_value = None
    client = AsyncMock()

    service = TranscriptionService(repository, client)
    await service.transcribe_video(uuid.uuid4())

    client.transcribe.assert_not_awaited()
    repository.mark_transcript_processing.assert_not_awaited()


async def test_transcribe_video_success_marks_processing_then_saves_transcript() -> None:
    video_id = uuid.uuid4()
    repository = AsyncMock()
    repository.get_by_id.return_value = _make_video(video_id, TranscriptStatus.PENDING)
    client = AsyncMock()
    client.transcribe.return_value = TranscriptionResult(
        text="olá mundo", language="pt", duration_seconds=10.0
    )

    service = TranscriptionService(repository, client)
    await service.transcribe_video(video_id)

    repository.mark_transcript_processing.assert_awaited_once_with(video_id)
    client.transcribe.assert_awaited_once_with("abc123")
    repository.save_transcript.assert_awaited_once_with(video_id, text="olá mundo", language="pt")
    repository.mark_transcript_failed.assert_not_awaited()


async def test_transcribe_video_retries_failed_videos() -> None:
    video_id = uuid.uuid4()
    repository = AsyncMock()
    repository.get_by_id.return_value = _make_video(video_id, TranscriptStatus.FAILED)
    client = AsyncMock()
    client.transcribe.return_value = TranscriptionResult(
        text="retry ok", language="pt", duration_seconds=5.0
    )

    service = TranscriptionService(repository, client)
    await service.transcribe_video(video_id)

    client.transcribe.assert_awaited_once_with("abc123")
    repository.save_transcript.assert_awaited_once_with(video_id, text="retry ok", language="pt")


async def test_transcribe_video_skips_already_completed_videos() -> None:
    video_id = uuid.uuid4()
    repository = AsyncMock()
    repository.get_by_id.return_value = _make_video(video_id, TranscriptStatus.COMPLETED)
    client = AsyncMock()

    service = TranscriptionService(repository, client)
    await service.transcribe_video(video_id)

    client.transcribe.assert_not_awaited()
    repository.mark_transcript_processing.assert_not_awaited()


async def test_transcribe_video_skips_already_processing_videos() -> None:
    video_id = uuid.uuid4()
    repository = AsyncMock()
    repository.get_by_id.return_value = _make_video(video_id, TranscriptStatus.PROCESSING)
    client = AsyncMock()

    service = TranscriptionService(repository, client)
    await service.transcribe_video(video_id)

    client.transcribe.assert_not_awaited()


async def test_transcribe_video_marks_failed_on_transcription_error() -> None:
    video_id = uuid.uuid4()
    repository = AsyncMock()
    repository.get_by_id.return_value = _make_video(video_id, TranscriptStatus.PENDING)
    client = AsyncMock()
    client.transcribe.side_effect = TranscriptionError("falha ao baixar áudio")

    service = TranscriptionService(repository, client)
    await service.transcribe_video(video_id)

    repository.mark_transcript_failed.assert_awaited_once_with(video_id, "falha ao baixar áudio")
    repository.save_transcript.assert_not_awaited()
