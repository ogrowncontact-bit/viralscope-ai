from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from app.db.session import AsyncSessionFactory
from app.repositories.analysis_repository import SqlAlchemyAnalysisRepository
from app.repositories.interfaces.analysis_repository import AnalysisRepositoryProtocol
from app.repositories.interfaces.video_repository import VideoRepositoryProtocol
from app.repositories.video_repository import SqlAlchemyVideoRepository


@asynccontextmanager
async def video_repository_scope() -> AsyncIterator[VideoRepositoryProtocol]:
    """Abre uma sessão de banco para uso dentro de um job arq (que não tem `Depends`)."""
    async with AsyncSessionFactory() as session:
        yield SqlAlchemyVideoRepository(session)


@asynccontextmanager
async def analysis_repository_scope() -> (
    AsyncIterator[tuple[AnalysisRepositoryProtocol, VideoRepositoryProtocol]]
):
    """Abre uma sessão de banco e devolve os repositórios de Analysis e Video compartilhando a
    mesma sessão — `AnalysisService.run_analysis` precisa dos dois."""
    async with AsyncSessionFactory() as session:
        yield SqlAlchemyAnalysisRepository(session), SqlAlchemyVideoRepository(session)
