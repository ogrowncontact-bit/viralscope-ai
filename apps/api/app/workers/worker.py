from arq.connections import RedisSettings
from arq.cron import cron

from app.core.config import get_settings
from app.workers.lifecycle import shutdown, startup
from app.workers.tasks.metrics import sync_video_metrics_job
from app.workers.tasks.transcription import transcribe_video_job


class WorkerSettings:
    """Executar com: `poetry run arq app.workers.worker.WorkerSettings`."""

    functions = [transcribe_video_job]
    cron_jobs = [cron(sync_video_metrics_job, minute=0)]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = RedisSettings.from_dsn(get_settings().redis_url)
    job_timeout = 600
    max_jobs = 5
