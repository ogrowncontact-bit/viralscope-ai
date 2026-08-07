import uuid
from unittest.mock import AsyncMock

import pytest

from app.integrations.job_queue import ArqJobQueue, JobQueueError


async def test_enqueue_transcription_creates_pool_lazily_and_reuses_it(monkeypatch) -> None:
    fake_pool = AsyncMock()
    create_pool_mock = AsyncMock(return_value=fake_pool)
    monkeypatch.setattr("app.integrations.job_queue.create_pool", create_pool_mock)

    queue = ArqJobQueue(redis_url="redis://localhost:6379/0")
    video_id = uuid.uuid4()

    await queue.enqueue_transcription(video_id)
    await queue.enqueue_transcription(video_id)

    create_pool_mock.assert_awaited_once()
    assert fake_pool.enqueue_job.await_count == 2
    fake_pool.enqueue_job.assert_awaited_with(
        "transcribe_video_job", str(video_id), _job_id=f"transcribe-video-{video_id}"
    )


async def test_enqueue_transcription_raises_job_queue_error_when_pool_creation_fails(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "app.integrations.job_queue.create_pool", AsyncMock(side_effect=ConnectionError("boom"))
    )

    queue = ArqJobQueue(redis_url="redis://localhost:6379/0")

    with pytest.raises(JobQueueError):
        await queue.enqueue_transcription(uuid.uuid4())


async def test_enqueue_transcription_raises_job_queue_error_when_enqueue_fails(monkeypatch) -> None:
    fake_pool = AsyncMock()
    fake_pool.enqueue_job.side_effect = ConnectionError("boom")
    monkeypatch.setattr(
        "app.integrations.job_queue.create_pool", AsyncMock(return_value=fake_pool)
    )

    queue = ArqJobQueue(redis_url="redis://localhost:6379/0")

    with pytest.raises(JobQueueError):
        await queue.enqueue_transcription(uuid.uuid4())


async def test_enqueue_analysis_creates_pool_lazily_and_reuses_it(monkeypatch) -> None:
    fake_pool = AsyncMock()
    create_pool_mock = AsyncMock(return_value=fake_pool)
    monkeypatch.setattr("app.integrations.job_queue.create_pool", create_pool_mock)

    queue = ArqJobQueue(redis_url="redis://localhost:6379/0")
    analysis_id = uuid.uuid4()

    await queue.enqueue_analysis(analysis_id)
    await queue.enqueue_analysis(analysis_id)

    create_pool_mock.assert_awaited_once()
    assert fake_pool.enqueue_job.await_count == 2
    fake_pool.enqueue_job.assert_awaited_with(
        "analyze_video_job", str(analysis_id), _job_id=f"analyze-{analysis_id}"
    )


async def test_enqueue_analysis_raises_job_queue_error_when_pool_creation_fails(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "app.integrations.job_queue.create_pool", AsyncMock(side_effect=ConnectionError("boom"))
    )

    queue = ArqJobQueue(redis_url="redis://localhost:6379/0")

    with pytest.raises(JobQueueError):
        await queue.enqueue_analysis(uuid.uuid4())


async def test_enqueue_analysis_raises_job_queue_error_when_enqueue_fails(monkeypatch) -> None:
    fake_pool = AsyncMock()
    fake_pool.enqueue_job.side_effect = ConnectionError("boom")
    monkeypatch.setattr("app.integrations.job_queue.create_pool", AsyncMock(return_value=fake_pool))

    queue = ArqJobQueue(redis_url="redis://localhost:6379/0")

    with pytest.raises(JobQueueError):
        await queue.enqueue_analysis(uuid.uuid4())
