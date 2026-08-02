from unittest.mock import AsyncMock

from httpx import AsyncClient

from app.core.dependencies import get_health_repository
from app.main import app


async def test_health_endpoint_returns_healthy_when_database_is_reachable(
    client: AsyncClient,
) -> None:
    fake_repository = AsyncMock()
    fake_repository.check_connection.return_value = True
    app.dependency_overrides[get_health_repository] = lambda: fake_repository

    response = await client.get("/api/v1/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert body["database"] == "connected"

    app.dependency_overrides.clear()


async def test_health_endpoint_returns_degraded_when_database_is_unreachable(
    client: AsyncClient,
) -> None:
    fake_repository = AsyncMock()
    fake_repository.check_connection.return_value = False
    app.dependency_overrides[get_health_repository] = lambda: fake_repository

    response = await client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["status"] == "degraded"

    app.dependency_overrides.clear()
