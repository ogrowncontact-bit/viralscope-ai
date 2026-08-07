import uuid
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock

from app.workers.tasks.metrics import sync_video_metrics_job
from app.workers.tasks.transcription import transcribe_video_job


def _fake_scope(fake_repository):
    @asynccontextmanager
    async def scope():
        yield fake_repository

    return scope


async def test_transcribe_video_job_uses_scoped_repository_and_ctx_client(
    monkeypatch,
) -> None:
    fake_repository = AsyncMock()
    fake_repository.get_by_id.return_value = None
    monkeypatch.setattr(
        "app.workers.tasks.transcription.video_repository_scope", _fake_scope(fake_repository)
    )
    video_id = uuid.uuid4()
    ctx = {"transcription_client": AsyncMock()}

    await transcribe_video_job(ctx, str(video_id))

    fake_repository.get_by_id.assert_awaited_once_with(video_id)


async def test_sync_video_metrics_job_uses_scoped_repository_and_ctx_client(
    monkeypatch,
) -> None:
    fake_repository = AsyncMock()
    fake_repository.list_favorited_video_ids.return_value = []
    monkeypatch.setattr(
        "app.workers.tasks.metrics.video_repository_scope", _fake_scope(fake_repository)
    )
    ctx = {"youtube_client": AsyncMock()}

    await sync_video_metrics_job(ctx)

    fake_repository.list_favorited_video_ids.assert_awaited_once()
