import logging

from app.core.config import get_settings
from app.core.dependencies import get_analysis_client, get_transcription_client
from app.db.session import engine
from app.integrations.job_queue import ArqJobQueue
from app.integrations.youtube_client import YouTubeClient

logger = logging.getLogger(__name__)


async def startup(ctx: dict) -> None:
    settings = get_settings()
    ctx["transcription_client"] = get_transcription_client(settings)
    ctx["analysis_client"] = get_analysis_client(settings)
    ctx["youtube_client"] = YouTubeClient(api_key=settings.youtube_api_key)
    # AnalysisService sempre recebe job_queue no construtor (mesma classe atende router e worker),
    # mesmo que run_analysis não o use.
    ctx["job_queue"] = ArqJobQueue(redis_url=settings.redis_url)
    logger.info("Worker iniciado.")


async def shutdown(ctx: dict) -> None:
    await engine.dispose()
