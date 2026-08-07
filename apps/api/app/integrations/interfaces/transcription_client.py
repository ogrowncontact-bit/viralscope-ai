from dataclasses import dataclass
from typing import Protocol


class TranscriptionError(Exception):
    """Falha ao transcrever o áudio de um vídeo (download, chamada à API Whisper, etc.)."""


@dataclass(frozen=True)
class TranscriptionResult:
    text: str
    language: str | None
    duration_seconds: float | None


class TranscriptionClientProtocol(Protocol):
    async def transcribe(self, youtube_video_id: str) -> TranscriptionResult: ...
