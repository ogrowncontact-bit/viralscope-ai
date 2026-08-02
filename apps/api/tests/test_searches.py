import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock

from httpx import AsyncClient

from app.core.dependencies import (
    get_current_user,
    get_search_repository,
    get_video_repository,
    get_youtube_client,
)
from app.integrations.youtube_client import YouTubeVideoData
from app.main import app
from app.models.search import Search
from app.models.user import User
from app.models.video import Video

FAKE_USER = User(
    id=uuid.uuid4(),
    clerk_user_id="user_test",
    email="test@example.com",
    full_name="Test User",
    avatar_url=None,
)


async def _override_current_user() -> User:
    return FAKE_USER


async def test_list_recent_searches_returns_serialized_list(client: AsyncClient) -> None:
    fake_repository = AsyncMock()
    fake_repository.list_recent.return_value = [
        Search(
            id=uuid.uuid4(),
            user_id=FAKE_USER.id,
            query="melhores hooks de youtube shorts",
            created_at=datetime.now(UTC),
        )
    ]
    app.dependency_overrides[get_current_user] = _override_current_user
    app.dependency_overrides[get_search_repository] = lambda: fake_repository

    response = await client.get("/api/v1/searches/recent")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["query"] == "melhores hooks de youtube shorts"
    fake_repository.list_recent.assert_awaited_once_with(FAKE_USER.id, 10)

    app.dependency_overrides.clear()


async def test_create_search_persists_and_returns_it(client: AsyncClient) -> None:
    fake_repository = AsyncMock()
    fake_repository.create.return_value = Search(
        id=uuid.uuid4(),
        user_id=FAKE_USER.id,
        query="canais crescendo rápido",
        created_at=datetime.now(UTC),
    )
    fake_video_repository = AsyncMock()
    fake_video_repository.upsert.return_value = Video(
        id=uuid.uuid4(),
        youtube_video_id="abc123",
        youtube_channel_id="channel-1",
        channel_title="Canal Teste",
        title="Vídeo de teste",
        description=None,
        thumbnail_url=None,
        view_count=0,
        like_count=0,
        comment_count=0,
        duration_seconds=None,
        published_at=None,
    )
    fake_youtube_client = AsyncMock()
    fake_youtube_client.search_videos.return_value = [
        YouTubeVideoData(
            youtube_video_id="abc123",
            youtube_channel_id="channel-1",
            channel_title="Canal Teste",
            title="Vídeo de teste",
            description=None,
            thumbnail_url=None,
            view_count=0,
            like_count=0,
            comment_count=0,
            duration_seconds=None,
            published_at=None,
        )
    ]
    app.dependency_overrides[get_current_user] = _override_current_user
    app.dependency_overrides[get_search_repository] = lambda: fake_repository
    app.dependency_overrides[get_video_repository] = lambda: fake_video_repository
    app.dependency_overrides[get_youtube_client] = lambda: fake_youtube_client

    response = await client.post("/api/v1/searches", json={"query": "canais crescendo rápido"})

    assert response.status_code == 201
    body = response.json()
    assert body["search"]["query"] == "canais crescendo rápido"
    assert body["videos"][0]["youtube_video_id"] == "abc123"
    fake_repository.create.assert_awaited_once_with(FAKE_USER.id, "canais crescendo rápido")
    fake_youtube_client.search_videos.assert_awaited_once_with("canais crescendo rápido")

    app.dependency_overrides.clear()


async def test_create_search_rejects_empty_query(client: AsyncClient) -> None:
    app.dependency_overrides[get_current_user] = _override_current_user

    response = await client.post("/api/v1/searches", json={"query": ""})

    assert response.status_code == 422

    app.dependency_overrides.clear()
