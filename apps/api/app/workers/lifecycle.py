import logging

from app.core.config import get_settings
from app.core.dependencies import get_transcription_client
from app.db.session import engine
from app.integrations.youtube_client import YouTubeClient

logger = logging.getLogger(__name__)


async def startup(ctx: dict) -> None:
    settings = get_settings()
    ctx["transcription_client"] = get_transcription_client(settings)
    ctx["youtube_client"] = YouTubeClient(api_key=settings.youtube_api_key)
    logger.info("Worker iniciado.")


async def shutdown(ctx: dict) -> None:
    await engine.dispose()
