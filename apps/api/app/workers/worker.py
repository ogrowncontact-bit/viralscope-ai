from arq.connections import RedisSettings
from arq.cron import cron
from arq.worker import func

from app.core.config import get_settings
from app.workers.lifecycle import shutdown, startup
from app.workers.tasks.metrics import sync_video_metrics_job
from app.workers.tasks.transcription import transcribe_video_job


class WorkerSettings:
    """Executar com: `poetry run arq app.workers.worker.WorkerSettings`."""

    # keep_result=0: sem isso, o resultado do job fica em cache no Redis pela duração padrão do
    # arq (result_key_prefix + job_id) e um novo `enqueue_job` com o mesmo `_job_id` determinístico
    # (ver ArqJobQueue.enqueue_transcription) retorna None silenciosamente em vez de enfileirar —
    # o que quebraria o retry manual de vídeos `failed` via POST /videos/{id}/transcribe.
    functions = [func(transcribe_video_job, keep_result=0)]
    cron_jobs = [cron(sync_video_metrics_job, minute=0)]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = RedisSettings.from_dsn(get_settings().redis_url)
    job_timeout = 600
    max_jobs = 5
