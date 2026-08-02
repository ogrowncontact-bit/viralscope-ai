from app.core.config import Settings
from app.repositories.interfaces.health_repository import HealthRepositoryProtocol
from app.schemas.health import HealthStatus


class HealthService:
    """Caso de uso: reportar a saúde da aplicação e suas dependências."""

    def __init__(self, repository: HealthRepositoryProtocol, settings: Settings) -> None:
        self._repository = repository
        self._settings = settings

    async def get_health_status(self) -> HealthStatus:
        database_ok = await self._repository.check_connection()
        return HealthStatus(
            status="healthy" if database_ok else "degraded",
            database="connected" if database_ok else "unavailable",
            environment=self._settings.environment,
        )
