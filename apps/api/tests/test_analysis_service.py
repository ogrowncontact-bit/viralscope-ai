import uuid
from unittest.mock import AsyncMock

import pytest

from app.integrations.interfaces.analysis_client import (
    AnalysisError,
    AnalysisInsights,
    AnalysisResult,
)
from app.integrations.job_queue import JobQueueError
from app.models.analysis import Analysis
from app.models.enums import AnalysisStatus, TranscriptStatus
from app.models.video import Video
from app.services.analysis_service import AnalysisService


def _make_analysis(analysis_id: uuid.UUID, video_id: uuid.UUID, status: AnalysisStatus) -> Analysis:
    return Analysis(id=analysis_id, video_id=video_id, user_id=uuid.uuid4(), status=status)


def _make_video(video_id: uuid.UUID, transcript_status: TranscriptStatus, **overrides) -> Video:
    defaults = dict(
        id=video_id,
        youtube_video_id="abc123",
        youtube_channel_id="channel-1",
        channel_title="Canal Teste",
        title="Vídeo de teste",
        view_count=0,
        like_count=0,
        comment_count=0,
        transcript_status=transcript_status,
        transcript_text=None,
        transcript_language=None,
    )
    defaults.update(overrides)
    return Video(**defaults)


def _make_service(analysis_repository=None, video_repository=None, analysis_client=None):
    return AnalysisService(
        analysis_repository=analysis_repository or AsyncMock(),
        video_repository=video_repository or AsyncMock(),
        analysis_client=analysis_client or AsyncMock(),
        job_queue=AsyncMock(),
    )


async def test_run_analysis_does_nothing_when_analysis_not_found() -> None:
    analysis_repository = AsyncMock()
    analysis_repository.get_by_id.return_value = None
    analysis_client = AsyncMock()

    service = _make_service(
        analysis_repository=analysis_repository, analysis_client=analysis_client
    )
    await service.run_analysis(uuid.uuid4())

    analysis_client.analyze.assert_not_awaited()


async def test_run_analysis_skips_already_completed_analyses() -> None:
    analysis_id, video_id = uuid.uuid4(), uuid.uuid4()
    analysis_repository = AsyncMock()
    analysis_repository.get_by_id.return_value = _make_analysis(
        analysis_id, video_id, AnalysisStatus.COMPLETED
    )
    analysis_client = AsyncMock()

    service = _make_service(
        analysis_repository=analysis_repository, analysis_client=analysis_client
    )
    await service.run_analysis(analysis_id)

    analysis_client.analyze.assert_not_awaited()


async def test_run_analysis_skips_already_processing_analyses() -> None:
    analysis_id, video_id = uuid.uuid4(), uuid.uuid4()
    analysis_repository = AsyncMock()
    analysis_repository.get_by_id.return_value = _make_analysis(
        analysis_id, video_id, AnalysisStatus.PROCESSING
    )
    analysis_client = AsyncMock()

    service = _make_service(
        analysis_repository=analysis_repository, analysis_client=analysis_client
    )
    await service.run_analysis(analysis_id)

    analysis_client.analyze.assert_not_awaited()


async def test_run_analysis_marks_failed_when_video_not_found() -> None:
    analysis_id, video_id = uuid.uuid4(), uuid.uuid4()
    analysis_repository = AsyncMock()
    analysis_repository.get_by_id.return_value = _make_analysis(
        analysis_id, video_id, AnalysisStatus.PENDING
    )
    video_repository = AsyncMock()
    video_repository.get_by_id.return_value = None

    service = _make_service(
        analysis_repository=analysis_repository, video_repository=video_repository
    )
    await service.run_analysis(analysis_id)

    analysis_repository.mark_failed.assert_awaited_once_with(
        analysis_id, "Vídeo associado não encontrado."
    )


async def test_run_analysis_retries_failed_analyses() -> None:
    analysis_id, video_id = uuid.uuid4(), uuid.uuid4()
    analysis_repository = AsyncMock()
    analysis_repository.get_by_id.return_value = _make_analysis(
        analysis_id, video_id, AnalysisStatus.FAILED
    )
    video_repository = AsyncMock()
    video_repository.get_by_id.return_value = _make_video(video_id, TranscriptStatus.PENDING)
    analysis_client = AsyncMock()
    analysis_client.analyze.return_value = AnalysisResult(
        viral_score=42.0,
        summary="resumo",
        insights=AnalysisInsights(winning_titles=[], hooks=[], content_opportunities=[]),
    )

    service = _make_service(analysis_repository, video_repository, analysis_client)
    await service.run_analysis(analysis_id)

    analysis_client.analyze.assert_awaited_once()
    analysis_repository.save_result.assert_awaited_once()


@pytest.mark.parametrize(
    "transcript_status",
    [TranscriptStatus.PENDING, TranscriptStatus.PROCESSING, TranscriptStatus.FAILED],
)
async def test_run_analysis_uses_metadata_only_when_transcript_not_completed(
    transcript_status: TranscriptStatus,
) -> None:
    analysis_id, video_id = uuid.uuid4(), uuid.uuid4()
    analysis_repository = AsyncMock()
    analysis_repository.get_by_id.return_value = _make_analysis(
        analysis_id, video_id, AnalysisStatus.PENDING
    )
    video_repository = AsyncMock()
    video_repository.get_by_id.return_value = _make_video(
        video_id, transcript_status, transcript_text="conteúdo transcrito"
    )
    analysis_client = AsyncMock()
    analysis_client.analyze.return_value = AnalysisResult(
        viral_score=10.0,
        summary="resumo",
        insights=AnalysisInsights(winning_titles=[], hooks=[], content_opportunities=[]),
    )

    service = _make_service(analysis_repository, video_repository, analysis_client)
    await service.run_analysis(analysis_id)

    sent_request = analysis_client.analyze.call_args.args[0]
    assert sent_request.transcript_text is None
    video_repository.get_by_id.assert_awaited_once()


async def test_run_analysis_success_marks_processing_then_saves_result() -> None:
    analysis_id, video_id = uuid.uuid4(), uuid.uuid4()
    analysis_repository = AsyncMock()
    analysis_repository.get_by_id.return_value = _make_analysis(
        analysis_id, video_id, AnalysisStatus.PENDING
    )
    video_repository = AsyncMock()
    video_repository.get_by_id.return_value = _make_video(
        video_id,
        TranscriptStatus.COMPLETED,
        transcript_text="conteúdo transcrito",
        transcript_language="pt",
    )
    analysis_client = AsyncMock()
    analysis_client.analyze.return_value = AnalysisResult(
        viral_score=75.5,
        summary="resumo",
        insights=AnalysisInsights(
            winning_titles=["Título"], hooks=["Gancho"], content_opportunities=["Ideia"]
        ),
    )

    service = _make_service(analysis_repository, video_repository, analysis_client)
    await service.run_analysis(analysis_id)

    analysis_repository.mark_processing.assert_awaited_once_with(analysis_id)
    sent_request = analysis_client.analyze.call_args.args[0]
    assert sent_request.transcript_text == "conteúdo transcrito"
    assert sent_request.transcript_language == "pt"
    analysis_repository.save_result.assert_awaited_once_with(
        analysis_id,
        viral_score=75.5,
        summary="resumo",
        insights={
            "winning_titles": ["Título"],
            "hooks": ["Gancho"],
            "content_opportunities": ["Ideia"],
        },
    )


async def test_run_analysis_marks_failed_on_analysis_error() -> None:
    analysis_id, video_id = uuid.uuid4(), uuid.uuid4()
    analysis_repository = AsyncMock()
    analysis_repository.get_by_id.return_value = _make_analysis(
        analysis_id, video_id, AnalysisStatus.PENDING
    )
    video_repository = AsyncMock()
    video_repository.get_by_id.return_value = _make_video(video_id, TranscriptStatus.PENDING)
    analysis_client = AsyncMock()
    analysis_client.analyze.side_effect = AnalysisError("falha na chamada à Anthropic")

    service = _make_service(analysis_repository, video_repository, analysis_client)
    await service.run_analysis(analysis_id)

    analysis_repository.mark_failed.assert_awaited_once_with(
        analysis_id, "falha na chamada à Anthropic"
    )
    analysis_repository.save_result.assert_not_awaited()


async def test_trigger_analysis_creates_row_and_enqueues_job() -> None:
    video_id, user_id = uuid.uuid4(), uuid.uuid4()
    video_repository = AsyncMock()
    video_repository.get_by_id.return_value = _make_video(video_id, TranscriptStatus.PENDING)
    analysis_repository = AsyncMock()
    created_analysis = _make_analysis(uuid.uuid4(), video_id, AnalysisStatus.PENDING)
    analysis_repository.create.return_value = created_analysis
    job_queue = AsyncMock()

    service = AnalysisService(
        analysis_repository=analysis_repository,
        video_repository=video_repository,
        analysis_client=AsyncMock(),
        job_queue=job_queue,
    )
    result = await service.trigger_analysis(video_id, user_id)

    assert result is created_analysis
    analysis_repository.create.assert_awaited_once_with(video_id=video_id, user_id=user_id)
    job_queue.enqueue_analysis.assert_awaited_once_with(created_analysis.id)


async def test_trigger_analysis_marks_failed_and_reraises_when_enqueue_fails() -> None:
    video_id, user_id = uuid.uuid4(), uuid.uuid4()
    video_repository = AsyncMock()
    video_repository.get_by_id.return_value = _make_video(video_id, TranscriptStatus.PENDING)
    analysis_repository = AsyncMock()
    created_analysis = _make_analysis(uuid.uuid4(), video_id, AnalysisStatus.PENDING)
    analysis_repository.create.return_value = created_analysis
    job_queue = AsyncMock()
    job_queue.enqueue_analysis.side_effect = JobQueueError("redis indisponível")

    service = AnalysisService(
        analysis_repository=analysis_repository,
        video_repository=video_repository,
        analysis_client=AsyncMock(),
        job_queue=job_queue,
    )

    with pytest.raises(JobQueueError):
        await service.trigger_analysis(video_id, user_id)

    analysis_repository.mark_failed.assert_awaited_once_with(
        created_analysis.id, "redis indisponível"
    )


async def test_trigger_analysis_returns_none_when_video_not_found() -> None:
    video_repository = AsyncMock()
    video_repository.get_by_id.return_value = None
    analysis_repository = AsyncMock()

    service = _make_service(
        analysis_repository=analysis_repository, video_repository=video_repository
    )
    result = await service.trigger_analysis(uuid.uuid4(), uuid.uuid4())

    assert result is None
    analysis_repository.create.assert_not_awaited()
