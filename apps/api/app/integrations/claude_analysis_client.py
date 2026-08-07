import json

import anthropic

from app.integrations.interfaces.analysis_client import (
    AnalysisError,
    AnalysisInsights,
    AnalysisRequest,
    AnalysisResult,
)

CLAUDE_ANALYSIS_MODEL = "claude-haiku-4-5"
MAX_OUTPUT_TOKENS = 2048
REQUEST_TIMEOUT_SECONDS = 60.0

# Limite de caracteres da transcrição enviada no prompt. Vídeos longos (podcasts, lives) podem ter
# transcrições muito extensas; truncar evita custo/latência desnecessários e mantém a chamada bem
# abaixo do contexto do modelo. Mantém só o início da transcrição — hooks/títulos tendem a se
# relacionar com a abertura do vídeo.
TRANSCRIPT_MAX_CHARS = 20_000

SYSTEM_PROMPT = (
    "Você é um analista especializado em conteúdo viral do YouTube. Você recebe metadados de um "
    "vídeo e, quando disponível, a transcrição do áudio, e produz uma análise estruturada sobre o "
    "potencial de viralização do vídeo. Sua análise deve explicar por que o vídeo viralizou (ou "
    "tem potencial para viralizar), sugerir títulos alternativos mais eficazes, ganchos (hooks) de "
    "abertura para maximizar retenção, e oportunidades de conteúdo derivado (ideias de Shorts ou "
    "vídeos relacionados). Se a transcrição não estiver disponível, baseie sua análise só nos "
    "metadados fornecidos (título, descrição, canal, métricas de engajamento, duração) — não "
    "presuma o conteúdo falado do vídeo nem invente detalhes que não estão nos dados. Responda "
    "'summary' e todos os itens de 'insights' em português do Brasil."
)

ANALYSIS_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "viral_score": {
            "type": "integer",
            "description": "Nota de 0 a 100 indicando o potencial de viralização do vídeo.",
        },
        "summary": {
            "type": "string",
            "description": (
                "Explicação de por que o vídeo viralizou ou tem potencial de viralização."
            ),
        },
        "insights": {
            "type": "object",
            "properties": {
                "winning_titles": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Títulos alternativos com maior potencial de cliques.",
                },
                "hooks": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Ganchos de abertura sugeridos para maximizar retenção.",
                },
                "content_opportunities": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Ideias de conteúdo derivado (Shorts, vídeos relacionados).",
                },
            },
            "required": ["winning_titles", "hooks", "content_opportunities"],
            "additionalProperties": False,
        },
    },
    "required": ["viral_score", "summary", "insights"],
    "additionalProperties": False,
}


class ClaudeAnalysisClient:
    """Analisa um vídeo via Claude (`claude-haiku-4-5`) usando o SDK oficial `anthropic`.

    Diferente de `WhisperTranscriptionClient`/`YouTubeClient` (httpx puro), chamadas à própria API
    da Anthropic usam o SDK oficial. Haiku 4.5 não suporta `thinking` adaptativo nem
    `output_config.effort` — nenhum dos dois é passado na chamada.
    """

    def __init__(self, api_key: str, model: str = CLAUDE_ANALYSIS_MODEL) -> None:
        self._api_key = api_key
        self._client = anthropic.AsyncAnthropic(api_key=api_key, timeout=REQUEST_TIMEOUT_SECONDS)
        self._model = model

    async def analyze(self, request: AnalysisRequest) -> AnalysisResult:
        if not self._api_key:
            raise AnalysisError("ANTHROPIC_API_KEY não configurada.")

        try:
            response = await self._client.messages.create(
                model=self._model,
                max_tokens=MAX_OUTPUT_TOKENS,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": self._build_user_message(request)}],
                output_config={
                    "format": {"type": "json_schema", "schema": ANALYSIS_OUTPUT_SCHEMA}
                },
            )
        except anthropic.APIStatusError as exc:
            raise AnalysisError(
                f"API da Anthropic retornou erro ({exc.status_code}): {exc.message}"
            ) from exc
        except anthropic.APIConnectionError as exc:
            raise AnalysisError(f"Falha de rede ao chamar a API da Anthropic: {exc}") from exc

        if response.stop_reason == "refusal":
            raise AnalysisError("A Anthropic recusou processar esta análise (stop_reason=refusal).")
        if response.stop_reason == "max_tokens":
            raise AnalysisError(
                "Resposta da Anthropic truncada por max_tokens; JSON pode estar incompleto."
            )

        text_block = next((block for block in response.content if block.type == "text"), None)
        if text_block is None:
            raise AnalysisError(
                "Resposta da Anthropic não contém bloco de texto com o JSON esperado."
            )

        try:
            data = json.loads(text_block.text)
        except json.JSONDecodeError as exc:
            raise AnalysisError(f"Resposta da Anthropic não é um JSON válido: {exc}") from exc

        return self._parse_result(data)

    def _build_user_message(self, request: AnalysisRequest) -> str:
        return (
            "## Metadados do vídeo\n"
            f"Título: {request.title}\n"
            f"Canal: {request.channel_title}\n"
            f"Descrição: {request.description or '(sem descrição)'}\n"
            f"Duração (segundos): {self._format_duration(request.duration_seconds)}\n"
            f"Visualizações: {request.view_count}\n"
            f"Curtidas: {request.like_count}\n"
            f"Comentários: {request.comment_count}\n\n"
            "## Transcrição\n"
            f"{self._build_transcript_section(request)}"
        )

    @staticmethod
    def _format_duration(duration_seconds: int | None) -> str:
        return str(duration_seconds) if duration_seconds is not None else "desconhecida"

    @staticmethod
    def _build_transcript_section(request: AnalysisRequest) -> str:
        if not request.transcript_text:
            return (
                "Transcrição não disponível para este vídeo. Baseie sua análise apenas nos "
                "metadados acima."
            )
        text = request.transcript_text
        if len(text) > TRANSCRIPT_MAX_CHARS:
            text = text[:TRANSCRIPT_MAX_CHARS]
            text += "\n\n[transcrição truncada — vídeo mais longo que o limite enviado ao modelo]"
        language_note = (
            f" (idioma: {request.transcript_language})" if request.transcript_language else ""
        )
        return f"{text}{language_note}"

    @staticmethod
    def _parse_result(data: dict) -> AnalysisResult:
        try:
            insights_data = data["insights"]
            insights = AnalysisInsights(
                winning_titles=list(insights_data["winning_titles"]),
                hooks=list(insights_data["hooks"]),
                content_opportunities=list(insights_data["content_opportunities"]),
            )
            viral_score = _clamp_score(float(data["viral_score"]))
            summary = str(data["summary"])
        except (KeyError, TypeError, ValueError) as exc:
            raise AnalysisError(
                f"JSON estruturado da Anthropic não corresponde ao schema esperado: {exc}"
            ) from exc

        return AnalysisResult(viral_score=viral_score, summary=summary, insights=insights)


def _clamp_score(score: float) -> float:
    # JSON Schema de structured outputs não suporta minimum/maximum — clampar defensivamente.
    return max(0.0, min(100.0, score))
