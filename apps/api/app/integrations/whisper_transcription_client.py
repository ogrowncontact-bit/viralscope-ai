import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory

import httpx
import yt_dlp

from app.integrations.interfaces.transcription_client import (
    TranscriptionError,
    TranscriptionResult,
)

OPENAI_TRANSCRIPTIONS_URL = "https://api.openai.com/v1/audio/transcriptions"
WHISPER_MODEL = "whisper-1"
YOUTUBE_WATCH_URL = "https://www.youtube.com/watch?v={video_id}"


class WhisperTranscriptionClient:
    """Transcreve o áudio de um vídeo do YouTube via yt-dlp + API Whisper da OpenAI.

    yt-dlp pode ser bloqueado por proteções anti-bot do YouTube quando executado a partir de
    IPs de datacenter/cloud — trade-off conhecido, isolado atrás de `TranscriptionClientProtocol`
    para poder ser substituído sem afetar o resto do fluxo de transcrição.
    """

    def __init__(self, api_key: str, transcriptions_url: str = OPENAI_TRANSCRIPTIONS_URL) -> None:
        self._api_key = api_key
        self._transcriptions_url = transcriptions_url

    async def transcribe(self, youtube_video_id: str) -> TranscriptionResult:
        if not self._api_key:
            raise TranscriptionError("OPENAI_API_KEY não configurada.")

        with TemporaryDirectory() as tmp_dir:
            audio_path = await asyncio.to_thread(
                self._download_audio, youtube_video_id, Path(tmp_dir)
            )
            return await self._call_whisper(audio_path)

    def _download_audio(self, youtube_video_id: str, output_dir: Path) -> Path:
        output_template = str(output_dir / "audio.%(ext)s")
        options = {
            "format": "bestaudio/best",
            "outtmpl": output_template,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "128",
                }
            ],
            "quiet": True,
            "no_warnings": True,
        }

        try:
            with yt_dlp.YoutubeDL(options) as downloader:
                downloader.download([YOUTUBE_WATCH_URL.format(video_id=youtube_video_id)])
        except Exception as exc:
            # yt-dlp levanta tipos de exceção variados (rede, extractor, postprocessor) —
            # todos viram falha de transcrição.
            raise TranscriptionError(f"Falha ao baixar áudio do YouTube: {exc}") from exc

        audio_path = output_dir / "audio.mp3"
        if not audio_path.exists():
            raise TranscriptionError("yt-dlp não gerou o arquivo de áudio esperado.")
        return audio_path

    async def _call_whisper(self, audio_path: Path) -> TranscriptionResult:
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                with audio_path.open("rb") as audio_file:
                    response = await client.post(
                        self._transcriptions_url,
                        headers={"Authorization": f"Bearer {self._api_key}"},
                        data={"model": WHISPER_MODEL, "response_format": "verbose_json"},
                        files={"file": (audio_path.name, audio_file, "audio/mpeg")},
                    )
        except httpx.HTTPError as exc:
            raise TranscriptionError(f"Falha de rede ao chamar a API Whisper: {exc}") from exc

        if response.status_code != httpx.codes.OK:
            raise TranscriptionError(
                f"API Whisper retornou {response.status_code}: {response.text[:300]}"
            )

        data = response.json()
        return TranscriptionResult(
            text=data.get("text", ""),
            language=data.get("language"),
            duration_seconds=data.get("duration"),
        )
