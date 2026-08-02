import uuid

from app.repositories.interfaces.analysis_repository import AnalysisRepositoryProtocol
from app.repositories.interfaces.favorite_repository import FavoriteRepositoryProtocol
from app.repositories.interfaces.search_repository import SearchRepositoryProtocol
from app.schemas.dashboard import DashboardStats


class DashboardService:
    def __init__(
        self,
        search_repository: SearchRepositoryProtocol,
        favorite_repository: FavoriteRepositoryProtocol,
        analysis_repository: AnalysisRepositoryProtocol,
    ) -> None:
        self._search_repository = search_repository
        self._favorite_repository = favorite_repository
        self._analysis_repository = analysis_repository

    async def get_stats(self, user_id: uuid.UUID) -> DashboardStats:
        searches_count = await self._search_repository.count_by_user(user_id)
        favorites_count = await self._favorite_repository.count_by_user(user_id)
        analyses_count = await self._analysis_repository.count_by_user(user_id)

        return DashboardStats(
            searches_count=searches_count,
            favorites_count=favorites_count,
            analyses_count=analyses_count,
        )
