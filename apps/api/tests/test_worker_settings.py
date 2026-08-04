from app.workers.lifecycle import shutdown, startup
from app.workers.tasks.metrics import sync_video_metrics_job
from app.workers.tasks.transcription import transcribe_video_job
from app.workers.worker import WorkerSettings


def test_worker_settings_registers_functions_and_cron() -> None:
    assert WorkerSettings.functions == [transcribe_video_job]
    assert len(WorkerSettings.cron_jobs) == 1
    assert WorkerSettings.on_startup is startup
    assert WorkerSettings.on_shutdown is shutdown


def test_worker_settings_cron_job_targets_metrics_sync() -> None:
    cron_job = WorkerSettings.cron_jobs[0]
    assert cron_job.coroutine is sync_video_metrics_job
