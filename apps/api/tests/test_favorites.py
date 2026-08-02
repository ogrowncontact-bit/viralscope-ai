import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock

from httpx import AsyncClient

from app.core.dependencies import get_current_user, get_favorite_repository
from app.main import app
from app.models.favorite import Favorite
from app.models.user import User
from app.models.video import Video

FAKE_USER = User(id=uuid.uuid4(), clerk_user_id="user_test", email="test@example.com")


async def _override_current_user() -> User:
    return FAKE_USER


async def test_list_favorites_returns_empty_state(client: AsyncClient) -> None:
    fake_repository = AsyncMock()
    fake_repository.list_with_video.return_value = []
    app.dependency_overrides[get_current_user] = _override_current_user
    app.dependency_overrides[get_favorite_repository] = lambda: fake_repository

    response = await client.get("/api/v1/favorites")

    assert response.status_code == 200
    assert response.json() == []

    app.dependency_overrides.clear()


async def test_list_favorites_returns_video_joined_data(client: AsyncClient) -> None:
    video_id = uuid.uuid4()
    favorite = Favorite(
        id=uuid.uuid4(), user_id=FAKE_USER.id, video_id=video_id, created_at=datetime.now(UTC)
    )
    video = Video(
        id=video_id,
        youtube_video_id="abc123",
        youtube_channel_id="chan1",
        channel_title="Canal Teste",
        title="Vídeo Teste",
        thumbnail_url="https://example.com/thumb.jpg",
        view_count=0,
        like_count=0,
        comment_count=0,
    )
    fake_repository = AsyncMock()
    fake_repository.list_with_video.return_value = [(favorite, video)]
    app.dependency_overrides[get_current_user] = _override_current_user
    app.dependency_overrides[get_favorite_repository] = lambda: fake_repository

    response = await client.get("/api/v1/favorites")

    assert response.status_code == 200
    body = response.json()
    assert body[0]["youtube_video_id"] == "abc123"
    assert body[0]["title"] == "Vídeo Teste"

    app.dependency_overrides.clear()


async def test_add_favorite_returns_204(client: AsyncClient) -> None:
    fake_repository = AsyncMock()
    app.dependency_overrides[get_current_user] = _override_current_user
    app.dependency_overrides[get_favorite_repository] = lambda: fake_repository

    response = await client.post(f"/api/v1/favorites/{uuid.uuid4()}")

    assert response.status_code == 204

    app.dependency_overrides.clear()


async def test_remove_favorite_returns_404_when_not_found(client: AsyncClient) -> None:
    fake_repository = AsyncMock()
    fake_repository.remove.return_value = False
    app.dependency_overrides[get_current_user] = _override_current_user
    app.dependency_overrides[get_favorite_repository] = lambda: fake_repository

    response = await client.delete(f"/api/v1/favorites/{uuid.uuid4()}")

    assert response.status_code == 404

    app.dependency_overrides.clear()
