from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import TTLCache
from app.core.config import Settings, get_settings
from app.core.security.clerk import get_current_user_id
from app.db.session import get_db_session
from app.integrations.claude_analysis_client import ClaudeAnalysisClient
from app.integrations.interfaces.analysis_client import AnalysisClientProtocol
from app.integrations.interfaces.transcription_client import TranscriptionClientProtocol
from app.integrations.job_queue import ArqJobQueue
from app.integrations.whisper_transcription_client import WhisperTranscriptionClient
from app.integrations.youtube_client import YouTubeClient, YouTubeVideoData
from app.models.user import User
from app.repositories.analysis_repository import SqlAlchemyAnalysisRepository
from app.repositories.favorite_repository import SqlAlchemyFavoriteRepository
from app.repositories.health_repository import SqlAlchemyHealthRepository
from app.repositories.interfaces.analysis_repository import AnalysisRepositoryProtocol
from app.repositories.interfaces.favorite_repository import FavoriteRepositoryProtocol
from app.repositories.interfaces.health_repository import HealthRepositoryProtocol
from app.repositories.interfaces.search_repository import SearchRepositoryProtocol
from app.repositories.interfaces.user_repository import UserRepositoryProtocol
from app.repositories.interfaces.video_repository import VideoRepositoryProtocol
from app.repositories.search_repository import SqlAlchemySearchRepository
from app.repositories.user_repository import SqlAlchemyUserRepository
from app.repositories.video_repository import SqlAlchemyVideoRepository
from app.services.analysis_service import AnalysisService
from app.services.dashboard_service import DashboardService
from app.services.favorite_service import FavoriteService
from app.services.health_service import HealthService
from app.services.search_service import SearchService
from app.services.user_service import UserService
from app.services.video_service import VideoService

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


def get_video_repository(session: DbSessionDep) -> VideoRepositoryProtocol:
    return SqlAlchemyVideoRepository(session)


def get_youtube_client(settings: SettingsDep) -> YouTubeClient:
    return YouTubeClient(api_key=settings.youtube_api_key)


YOUTUBE_SEARCH_CACHE_TTL_SECONDS = 15 * 60


@lru_cache
def get_youtube_search_cache() -> TTLCache[list[YouTubeVideoData]]:
    return TTLCache(ttl_seconds=YOUTUBE_SEARCH_CACHE_TTL_SECONDS)


@lru_cache
def _job_queue_singleton(redis_url: str) -> ArqJobQueue:
    return ArqJobQueue(redis_url=redis_url)


def get_job_queue(settings: SettingsDep) -> ArqJobQueue:
    return _job_queue_singleton(settings.redis_url)


def get_transcription_client(settings: SettingsDep) -> TranscriptionClientProtocol:
    return WhisperTranscriptionClient(api_key=settings.openai_api_key)


def get_search_service(
    repository: Annotated[SearchRepositoryProtocol, Depends(get_search_repository)],
    video_repository: Annotated[VideoRepositoryProtocol, Depends(get_video_repository)],
    youtube_client: Annotated[YouTubeClient, Depends(get_youtube_client)],
    search_cache: Annotated[TTLCache[list[YouTubeVideoData]], Depends(get_youtube_search_cache)],
    job_queue: Annotated[ArqJobQueue, Depends(get_job_queue)],
) -> SearchService:
    return SearchService(repository, video_repository, youtube_client, search_cache, job_queue)


def get_video_service(
    video_repository: Annotated[VideoRepositoryProtocol, Depends(get_video_repository)],
    job_queue: Annotated[ArqJobQueue, Depends(get_job_queue)],
) -> VideoService:
    return VideoService(video_repository, job_queue)


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


def get_analysis_client(settings: SettingsDep) -> AnalysisClientProtocol:
    return ClaudeAnalysisClient(api_key=settings.anthropic_api_key)


def get_analysis_service(
    analysis_repository: Annotated[AnalysisRepositoryProtocol, Depends(get_analysis_repository)],
    video_repository: Annotated[VideoRepositoryProtocol, Depends(get_video_repository)],
    analysis_client: Annotated[AnalysisClientProtocol, Depends(get_analysis_client)],
    job_queue: Annotated[ArqJobQueue, Depends(get_job_queue)],
) -> AnalysisService:
    return AnalysisService(analysis_repository, video_repository, analysis_client, job_queue)
