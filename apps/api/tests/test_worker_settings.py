from app.workers.lifecycle import shutdown, startup
from app.workers.tasks.analysis import analyze_video_job
from app.workers.tasks.metrics import sync_video_metrics_job
from app.workers.tasks.transcription import transcribe_video_job
from app.workers.worker import WorkerSettings


def test_worker_settings_registers_functions_and_cron() -> None:
    assert len(WorkerSettings.functions) == 2
    assert WorkerSettings.functions[0].coroutine is transcribe_video_job
    assert WorkerSettings.functions[1].coroutine is analyze_video_job
    assert len(WorkerSettings.cron_jobs) == 1
    assert WorkerSettings.on_startup is startup
    assert WorkerSettings.on_shutdown is shutdown


def test_worker_settings_transcription_job_does_not_keep_result() -> None:
    # keep_result=0 evita que o dedupe nativo do arq (mesmo `_job_id`) bloqueie um retry manual
    # depois que um job anterior já terminou — ver comentário em app/workers/worker.py.
    assert WorkerSettings.functions[0].keep_result_s == 0


def test_worker_settings_analysis_job_does_not_keep_result() -> None:
    assert WorkerSettings.functions[1].keep_result_s == 0


def test_worker_settings_cron_job_targets_metrics_sync() -> None:
    cron_job = WorkerSettings.cron_jobs[0]
    assert cron_job.coroutine is sync_video_metrics_job
