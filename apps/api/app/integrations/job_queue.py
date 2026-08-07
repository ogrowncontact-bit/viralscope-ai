import asyncio
import uuid

from arq import ArqRedis, create_pool
from arq.connections import RedisSettings


class JobQueueError(Exception):
    """Falha ao enfileirar um job assíncrono (Redis indisponível, etc.)."""


class ArqJobQueue:
    """Fila de jobs assíncronos sobre Redis (arq). Conexão criada de forma lazy e reusada."""

    def __init__(self, redis_url: str) -> None:
        self._redis_url = redis_url
        self._pool: ArqRedis | None = None
        self._pool_lock = asyncio.Lock()

    async def _get_pool(self) -> ArqRedis:
        if self._pool is not None:
            return self._pool

        async with self._pool_lock:
            if self._pool is None:
                try:
                    self._pool = await create_pool(RedisSettings.from_dsn(self._redis_url))
                except Exception as exc:
                    raise JobQueueError(f"Falha ao conectar à fila Redis: {exc}") from exc
            return self._pool

    async def enqueue_transcription(self, video_id: uuid.UUID) -> None:
        pool = await self._get_pool()
        try:
            await pool.enqueue_job(
                "transcribe_video_job", str(video_id), _job_id=f"transcribe-video-{video_id}"
            )
        except Exception as exc:
            raise JobQueueError(
                f"Falha ao enfileirar transcrição do vídeo {video_id}: {exc}"
            ) from exc

    async def enqueue_analysis(self, analysis_id: uuid.UUID) -> None:
        # Dedupe por analysis_id, não por video_id: cada trigger_analysis cria uma linha nova em
        # `analyses` (sem cache/dedupe cross-user), então múltiplas análises do mesmo vídeo por
        # usuários diferentes devem todas rodar — um _job_id por vídeo bloquearia indevidamente.
        pool = await self._get_pool()
        try:
            await pool.enqueue_job(
                "analyze_video_job", str(analysis_id), _job_id=f"analyze-{analysis_id}"
            )
        except Exception as exc:
            raise JobQueueError(f"Falha ao enfileirar análise {analysis_id}: {exc}") from exc
