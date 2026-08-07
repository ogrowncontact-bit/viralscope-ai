import uuid
from unittest.mock import AsyncMock

from httpx import AsyncClient

from app.core.dependencies import get_current_user, get_job_queue, get_video_repository
from app.main import app
from app.models.enums import TranscriptStatus
from app.models.user import User
from app.models.video import Video

FAKE_USER = User(id=uuid.uuid4(), clerk_user_id="user_test", email="test@example.com")


async def _override_current_user() -> User:
    return FAKE_USER


async def test_trigger_transcription_returns_202_and_enqueues_job(client: AsyncClient) -> None:
    video_id = uuid.uuid4()
    video = Video(
        id=video_id,
        youtube_video_id="abc123",
        youtube_channel_id="channel-1",
        channel_title="Canal Teste",
        title="Vídeo de teste",
        view_count=0,
        like_count=0,
        comment_count=0,
        transcript_status=TranscriptStatus.PENDING,
    )
    fake_video_repository = AsyncMock()
    fake_video_repository.get_by_id.return_value = video
    fake_job_queue = AsyncMock()

    app.dependency_overrides[get_current_user] = _override_current_user
    app.dependency_overrides[get_video_repository] = lambda: fake_video_repository
    app.dependency_overrides[get_job_queue] = lambda: fake_job_queue

    response = await client.post(f"/api/v1/videos/{video_id}/transcribe")

    assert response.status_code == 202
    body = response.json()
    assert body["id"] == str(video_id)
    assert body["transcript_status"] == "pending"
    fake_job_queue.enqueue_transcription.assert_awaited_once_with(video_id)

    app.dependency_overrides.clear()


async def test_trigger_transcription_returns_404_when_video_not_found(client: AsyncClient) -> None:
    fake_video_repository = AsyncMock()
    fake_video_repository.get_by_id.return_value = None
    fake_job_queue = AsyncMock()

    app.dependency_overrides[get_current_user] = _override_current_user
    app.dependency_overrides[get_video_repository] = lambda: fake_video_repository
    app.dependency_overrides[get_job_queue] = lambda: fake_job_queue

    response = await client.post(f"/api/v1/videos/{uuid.uuid4()}/transcribe")

    assert response.status_code == 404
    fake_job_queue.enqueue_transcription.assert_not_awaited()

    app.dependency_overrides.clear()
