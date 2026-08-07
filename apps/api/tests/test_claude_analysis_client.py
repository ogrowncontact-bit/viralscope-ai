import json

import httpx
import pytest
import respx
from httpx import Response

from app.integrations.claude_analysis_client import (
    ANALYSIS_OUTPUT_SCHEMA,
    ClaudeAnalysisClient,
)
from app.integrations.interfaces.analysis_client import AnalysisError, AnalysisRequest

ANTHROPIC_MESSAGES_URL = "https://api.anthropic.com/v1/messages"


def _request(**overrides: object) -> AnalysisRequest:
    defaults: dict[str, object] = {
        "title": "Vídeo de teste",
        "description": "Descrição de teste",
        "channel_title": "Canal Teste",
        "view_count": 1000,
        "like_count": 100,
        "comment_count": 10,
        "duration_seconds": 300,
        "transcript_text": None,
        "transcript_language": None,
    }
    defaults.update(overrides)
    return AnalysisRequest(**defaults)


def _message_response(
    data: dict | None = None, stop_reason: str = "end_turn", content: list | None = None
) -> dict:
    if content is None:
        content = [{"type": "text", "text": json.dumps(data)}]
    return {
        "id": "msg_test",
        "type": "message",
        "role": "assistant",
        "model": "claude-haiku-4-5",
        "content": content,
        "stop_reason": stop_reason,
        "stop_sequence": None,
        "usage": {"input_tokens": 100, "output_tokens": 50},
    }


VALID_ANALYSIS_JSON = {
    "viral_score": 87,
    "summary": "O vídeo viralizou por causa do hook forte na abertura.",
    "insights": {
        "winning_titles": ["Título 1", "Título 2"],
        "hooks": ["Gancho 1"],
        "content_opportunities": ["Ideia de Short 1"],
    },
}


async def test_analyze_raises_without_api_key() -> None:
    client = ClaudeAnalysisClient(api_key="")

    with pytest.raises(AnalysisError):
        await client.analyze(_request())


@respx.mock
async def test_analyze_returns_result_with_transcript() -> None:
    route = respx.post(ANTHROPIC_MESSAGES_URL).mock(
        return_value=Response(200, json=_message_response(VALID_ANALYSIS_JSON))
    )

    client = ClaudeAnalysisClient(api_key="fake-key")
    result = await client.analyze(_request(transcript_text="Fala, galera, hoje vamos..."))

    assert result.viral_score == 87.0
    assert result.summary == VALID_ANALYSIS_JSON["summary"]
    assert result.insights.winning_titles == ["Título 1", "Título 2"]
    assert result.insights.hooks == ["Gancho 1"]
    assert result.insights.content_opportunities == ["Ideia de Short 1"]

    sent_body = json.loads(route.calls.last.request.content)
    assert "Fala, galera, hoje vamos..." in sent_body["messages"][0]["content"]
    assert sent_body["output_config"]["format"]["schema"] == ANALYSIS_OUTPUT_SCHEMA


@respx.mock
async def test_analyze_without_transcript_notes_unavailable_in_prompt() -> None:
    route = respx.post(ANTHROPIC_MESSAGES_URL).mock(
        return_value=Response(200, json=_message_response(VALID_ANALYSIS_JSON))
    )

    client = ClaudeAnalysisClient(api_key="fake-key")
    await client.analyze(_request(transcript_text=None))

    sent_body = json.loads(route.calls.last.request.content)
    assert "Transcrição não disponível" in sent_body["messages"][0]["content"]


@respx.mock
async def test_analyze_truncates_long_transcript() -> None:
    route = respx.post(ANTHROPIC_MESSAGES_URL).mock(
        return_value=Response(200, json=_message_response(VALID_ANALYSIS_JSON))
    )

    client = ClaudeAnalysisClient(api_key="fake-key")
    long_transcript = "a" * 30_000
    await client.analyze(_request(transcript_text=long_transcript))

    sent_body = json.loads(route.calls.last.request.content)
    sent_content = sent_body["messages"][0]["content"]
    assert "[transcrição truncada" in sent_content
    assert len(sent_content) < len(long_transcript)


@respx.mock
async def test_analyze_raises_on_refusal_stop_reason() -> None:
    respx.post(ANTHROPIC_MESSAGES_URL).mock(
        return_value=Response(200, json=_message_response(content=[], stop_reason="refusal"))
    )

    client = ClaudeAnalysisClient(api_key="fake-key")

    with pytest.raises(AnalysisError):
        await client.analyze(_request())


@respx.mock
async def test_analyze_raises_on_max_tokens_stop_reason() -> None:
    respx.post(ANTHROPIC_MESSAGES_URL).mock(
        return_value=Response(
            200, json=_message_response(VALID_ANALYSIS_JSON, stop_reason="max_tokens")
        )
    )

    client = ClaudeAnalysisClient(api_key="fake-key")

    with pytest.raises(AnalysisError):
        await client.analyze(_request())


@respx.mock
async def test_analyze_raises_on_invalid_json_text() -> None:
    respx.post(ANTHROPIC_MESSAGES_URL).mock(
        return_value=Response(
            200, json=_message_response(content=[{"type": "text", "text": "não é json"}])
        )
    )

    client = ClaudeAnalysisClient(api_key="fake-key")

    with pytest.raises(AnalysisError):
        await client.analyze(_request())


@respx.mock
async def test_analyze_raises_on_schema_mismatch() -> None:
    incomplete = {"viral_score": 50, "summary": "resumo", "insights": {"winning_titles": []}}
    respx.post(ANTHROPIC_MESSAGES_URL).mock(
        return_value=Response(200, json=_message_response(incomplete))
    )

    client = ClaudeAnalysisClient(api_key="fake-key")

    with pytest.raises(AnalysisError):
        await client.analyze(_request())


@respx.mock
async def test_analyze_clamps_viral_score_above_100() -> None:
    data = {**VALID_ANALYSIS_JSON, "viral_score": 150}
    respx.post(ANTHROPIC_MESSAGES_URL).mock(
        return_value=Response(200, json=_message_response(data))
    )

    client = ClaudeAnalysisClient(api_key="fake-key")
    result = await client.analyze(_request())

    assert result.viral_score == 100.0


@respx.mock
async def test_analyze_raises_on_api_5xx_error() -> None:
    respx.post(ANTHROPIC_MESSAGES_URL).mock(
        return_value=Response(500, json={"type": "error", "error": {"message": "boom"}})
    )

    client = ClaudeAnalysisClient(api_key="fake-key")

    with pytest.raises(AnalysisError):
        await client.analyze(_request())


@respx.mock
async def test_analyze_raises_on_connection_error() -> None:
    respx.post(ANTHROPIC_MESSAGES_URL).mock(side_effect=httpx.ConnectError("boom"))

    client = ClaudeAnalysisClient(api_key="fake-key")

    with pytest.raises(AnalysisError):
        await client.analyze(_request())
