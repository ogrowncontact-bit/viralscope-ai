import uuid
from unittest.mock import AsyncMock

from httpx import AsyncClient

from app.core.dependencies import (
    get_analysis_repository,
    get_current_user,
    get_favorite_repository,
    get_search_repository,
)
from app.main import app
from app.models.user import User

FAKE_USER = User(id=uuid.uuid4(), clerk_user_id="user_test", email="test@example.com")


async def _override_current_user() -> User:
    return FAKE_USER


async def test_get_dashboard_stats_aggregates_counts(client: AsyncClient) -> None:
    fake_searches = AsyncMock()
    fake_searches.count_by_user.return_value = 3
    fake_favorites = AsyncMock()
    fake_favorites.count_by_user.return_value = 5
    fake_analyses = AsyncMock()
    fake_analyses.count_by_user.return_value = 0

    app.dependency_overrides[get_current_user] = _override_current_user
    app.dependency_overrides[get_search_repository] = lambda: fake_searches
    app.dependency_overrides[get_favorite_repository] = lambda: fake_favorites
    app.dependency_overrides[get_analysis_repository] = lambda: fake_analyses

    response = await client.get("/api/v1/dashboard/stats")

    assert response.status_code == 200
    assert response.json() == {
        "searches_count": 3,
        "favorites_count": 5,
        "analyses_count": 0,
    }

    app.dependency_overrides.clear()
