from pathlib import Path
from types import SimpleNamespace

import pytest
import respx
from httpx import Response

from app.integrations.interfaces.transcription_client import TranscriptionError
from app.integrations.whisper_transcription_client import (
    OPENAI_TRANSCRIPTIONS_URL,
    WhisperTranscriptionClient,
)


class _FakeYoutubeDL:
    def __init__(self, options: dict) -> None:
        self._options = options

    def __enter__(self) -> "_FakeYoutubeDL":
        return self

    def __exit__(self, *exc_info: object) -> bool:
        return False

    def download(self, urls: list[str]) -> None:
        audio_path = Path(self._options["outtmpl"].replace("%(ext)s", "mp3"))
        audio_path.write_bytes(b"fake-audio-bytes")


class _FailingYoutubeDL(_FakeYoutubeDL):
    def download(self, urls: list[str]) -> None:
        raise RuntimeError("yt-dlp explodiu")


async def test_transcribe_raises_without_api_key() -> None:
    client = WhisperTranscriptionClient(api_key="")

    with pytest.raises(TranscriptionError):
        await client.transcribe("abc123")


@respx.mock
async def test_transcribe_downloads_audio_and_calls_whisper(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "app.integrations.whisper_transcription_client.yt_dlp",
        SimpleNamespace(YoutubeDL=_FakeYoutubeDL),
    )
    respx.post(OPENAI_TRANSCRIPTIONS_URL).mock(
        return_value=Response(
            200, json={"text": "transcrição de teste", "language": "portuguese", "duration": 12.3}
        )
    )

    client = WhisperTranscriptionClient(api_key="fake-key")
    result = await client.transcribe("abc123")

    assert result.text == "transcrição de teste"
    assert result.language == "portuguese"
    assert result.duration_seconds == 12.3


async def test_transcribe_raises_when_audio_download_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.integrations.whisper_transcription_client.yt_dlp",
        SimpleNamespace(YoutubeDL=_FailingYoutubeDL),
    )

    client = WhisperTranscriptionClient(api_key="fake-key")

    with pytest.raises(TranscriptionError):
        await client.transcribe("abc123")


@respx.mock
async def test_transcribe_raises_when_whisper_api_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.integrations.whisper_transcription_client.yt_dlp",
        SimpleNamespace(YoutubeDL=_FakeYoutubeDL),
    )
    respx.post(OPENAI_TRANSCRIPTIONS_URL).mock(return_value=Response(500, text="server error"))

    client = WhisperTranscriptionClient(api_key="fake-key")

    with pytest.raises(TranscriptionError):
        await client.transcribe("abc123")
