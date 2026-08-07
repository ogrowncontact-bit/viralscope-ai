from dataclasses import dataclass
from typing import Protocol


class AnalysisError(Exception):
    """Falha ao analisar um vídeo via IA (chamada à API da Anthropic, parse da resposta, etc.)."""


@dataclass(frozen=True)
class AnalysisRequest:
    """Contexto do vídeo enviado ao modelo. Construído a partir de `Video`, sem depender do
    modelo SQLAlchemy diretamente."""

    title: str
    description: str | None
    channel_title: str
    view_count: int
    like_count: int
    comment_count: int
    duration_seconds: int | None
    transcript_text: str | None
    transcript_language: str | None


@dataclass(frozen=True)
class AnalysisInsights:
    winning_titles: list[str]
    hooks: list[str]
    content_opportunities: list[str]


@dataclass(frozen=True)
class AnalysisResult:
    viral_score: float
    summary: str
    insights: AnalysisInsights


class AnalysisClientProtocol(Protocol):
    async def analyze(self, request: AnalysisRequest) -> AnalysisResult: ...
