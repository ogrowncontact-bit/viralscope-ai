import dataclasses
import logging
import uuid

from app.integrations.interfaces.analysis_client import (
    AnalysisClientProtocol,
    AnalysisError,
    AnalysisRequest,
)
from app.integrations.job_queue import ArqJobQueue, JobQueueError
from app.models.analysis import Analysis
from app.models.enums import AnalysisStatus, TranscriptStatus
from app.repositories.interfaces.analysis_repository import AnalysisRepositoryProtocol
from app.repositories.interfaces.video_repository import VideoRepositoryProtocol

logger = logging.getLogger(__name__)

_RETRYABLE_STATUSES = (AnalysisStatus.PENDING, AnalysisStatus.FAILED)


class AnalysisService:
    """Acumula disparo (chamado pelo router) e execução (chamada pelo worker) — diferente do par
    VideoService/TranscriptionService do Módulo 4, aqui não há um service dono do agregado
    `Analysis` além deste."""

    def __init__(
        self,
        analysis_repository: AnalysisRepositoryProtocol,
        video_repository: VideoRepositoryProtocol,
        analysis_client: AnalysisClientProtocol,
        job_queue: ArqJobQueue,
    ) -> None:
        self._analysis_repository = analysis_repository
        self._video_repository = video_repository
        self._analysis_client = analysis_client
        self._job_queue = job_queue

    async def trigger_analysis(self, video_id: uuid.UUID, user_id: uuid.UUID) -> Analysis | None:
        """Cria sempre uma nova linha em `analyses` (sem cache/dedupe cross-user) e enfileira o
        job. Diferente do fire-and-forget de `SearchService`, aqui uma falha ao enfileirar deve
        propagar como erro pro chamador — é o próprio propósito do endpoint. Mas antes de propagar,
        marca a análise recém-criada como `failed` (em vez de deixá-la presa em `pending` para
        sempre, já que nenhum job foi de fato enfileirado para tirá-la desse estado)."""
        video = await self._video_repository.get_by_id(video_id)
        if video is None:
            return None

        analysis = await self._analysis_repository.create(video_id=video_id, user_id=user_id)
        try:
            await self._job_queue.enqueue_analysis(analysis.id)
        except JobQueueError as exc:
            await self._analysis_repository.mark_failed(analysis.id, str(exc))
            raise
        return analysis

    async def run_analysis(self, analysis_id: uuid.UUID) -> None:
        analysis = await self._analysis_repository.get_by_id(analysis_id)
        if analysis is None:
            logger.warning("run_analysis: análise %s não encontrada.", analysis_id)
            return

        if analysis.status not in _RETRYABLE_STATUSES:
            logger.info(
                "run_analysis: análise %s já está em status %s, ignorando.",
                analysis_id,
                analysis.status,
            )
            return

        video = await self._video_repository.get_by_id(analysis.video_id)
        if video is None:
            logger.warning(
                "run_analysis: vídeo %s da análise %s não encontrado.",
                analysis.video_id,
                analysis_id,
            )
            await self._analysis_repository.mark_failed(
                analysis_id, "Vídeo associado não encontrado."
            )
            return

        await self._analysis_repository.mark_processing(analysis_id)

        transcript_available = (
            video.transcript_status == TranscriptStatus.COMPLETED
            and bool(video.transcript_text)
        )
        request = AnalysisRequest(
            title=video.title,
            description=video.description,
            channel_title=video.channel_title,
            view_count=video.view_count,
            like_count=video.like_count,
            comment_count=video.comment_count,
            duration_seconds=video.duration_seconds,
            transcript_text=video.transcript_text if transcript_available else None,
            transcript_language=video.transcript_language if transcript_available else None,
        )

        try:
            result = await self._analysis_client.analyze(request)
        except AnalysisError as exc:
            logger.exception(
                "run_analysis: falha ao analisar vídeo %s (análise %s).", video.id, analysis_id
            )
            await self._analysis_repository.mark_failed(analysis_id, str(exc))
            return

        await self._analysis_repository.save_result(
            analysis_id,
            viral_score=result.viral_score,
            summary=result.summary,
            insights=dataclasses.asdict(result.insights),
        )
