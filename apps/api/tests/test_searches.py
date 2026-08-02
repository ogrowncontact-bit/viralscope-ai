import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock

from httpx import AsyncClient

from app.core.dependencies import get_current_user, get_search_repository
from app.main import app
from app.models.search import Search
from app.models.user import User

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
    app.dependency_overrides[get_current_user] = _override_current_user
    app.dependency_overrides[get_search_repository] = lambda: fake_repository

    response = await client.post("/api/v1/searches", json={"query": "canais crescendo rápido"})

    assert response.status_code == 201
    assert response.json()["query"] == "canais crescendo rápido"
    fake_repository.create.assert_awaited_once_with(FAKE_USER.id, "canais crescendo rápido")

    app.dependency_overrides.clear()


async def test_create_search_rejects_empty_query(client: AsyncClient) -> None:
    app.dependency_overrides[get_current_user] = _override_current_user

    response = await client.post("/api/v1/searches", json={"query": ""})

    assert response.status_code == 422

    app.dependency_overrides.clear()
