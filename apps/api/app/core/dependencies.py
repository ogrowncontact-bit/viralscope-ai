from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.security.clerk import get_current_user_id
from app.db.session import get_db_session
from app.models.user import User
from app.repositories.analysis_repository import SqlAlchemyAnalysisRepository
from app.repositories.favorite_repository import SqlAlchemyFavoriteRepository
from app.repositories.health_repository import SqlAlchemyHealthRepository
from app.repositories.interfaces.analysis_repository import AnalysisRepositoryProtocol
from app.repositories.interfaces.favorite_repository import FavoriteRepositoryProtocol
from app.repositories.interfaces.health_repository import HealthRepositoryProtocol
from app.repositories.interfaces.search_repository import SearchRepositoryProtocol
from app.repositories.interfaces.user_repository import UserRepositoryProtocol
from app.repositories.search_repository import SqlAlchemySearchRepository
from app.repositories.user_repository import SqlAlchemyUserRepository
from app.services.dashboard_service import DashboardService
from app.services.favorite_service import FavoriteService
from app.services.health_service import HealthService
from app.services.search_service import SearchService
from app.services.user_service import UserService

SettingsDep = Annotated[Settings, Depends(get_settings)]
DbSessionDep = Annotated[AsyncSession, Depends(get_db_session)]


def get_health_repository(session: DbSessionDep) -> HealthRepositoryProtocol:
    return SqlAlchemyHealthRepository(session)


def get_health_service(
    repository: Annotated[HealthRepositoryProtocol, Depends(get_health_repository)],
    settings: SettingsDep,
) -> HealthService:
    return HealthService(repository, settings)


def get_user_repository(session: DbSessionDep) -> UserRepositoryProtocol:
    return SqlAlchemyUserRepository(session)


def get_user_service(
    repository: Annotated[UserRepositoryProtocol, Depends(get_user_repository)],
) -> UserService:
    return UserService(repository)


async def get_current_user(
    clerk_user_id: Annotated[str, Depends(get_current_user_id)],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> User:
    return await user_service.get_or_create_current_user(clerk_user_id)


CurrentUserDep = Annotated[User, Depends(get_current_user)]


def get_search_repository(session: DbSessionDep) -> SearchRepositoryProtocol:
    return SqlAlchemySearchRepository(session)


def get_search_service(
    repository: Annotated[SearchRepositoryProtocol, Depends(get_search_repository)],
) -> SearchService:
    return SearchService(repository)


def get_favorite_repository(session: DbSessionDep) -> FavoriteRepositoryProtocol:
    return SqlAlchemyFavoriteRepository(session)


def get_favorite_service(
    repository: Annotated[FavoriteRepositoryProtocol, Depends(get_favorite_repository)],
) -> FavoriteService:
    return FavoriteService(repository)


def get_analysis_repository(session: DbSessionDep) -> AnalysisRepositoryProtocol:
    return SqlAlchemyAnalysisRepository(session)


def get_dashboard_service(
    search_repository: Annotated[SearchRepositoryProtocol, Depends(get_search_repository)],
    favorite_repository: Annotated[FavoriteRepositoryProtocol, Depends(get_favorite_repository)],
    analysis_repository: Annotated[AnalysisRepositoryProtocol, Depends(get_analysis_repository)],
) -> DashboardService:
    return DashboardService(search_repository, favorite_repository, analysis_repository)
