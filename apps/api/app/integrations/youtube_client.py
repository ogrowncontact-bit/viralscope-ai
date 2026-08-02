import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import httpx

YOUTUBE_API_BASE_URL = "https://www.googleapis.com/youtube/v3"

_ISO8601_DURATION_RE = re.compile(
    r"^PT(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+)S)?$"
)


class YouTubeAPIError(Exception):
    """Falha na integração com a YouTube Data API — chave ausente, erro HTTP ou quota excedida."""


@dataclass(frozen=True)
class YouTubeVideoData:
    youtube_video_id: str
    youtube_channel_id: str
    channel_title: str
    title: str
    description: str | None
    thumbnail_url: str | None
    view_count: int
    like_count: int
    comment_count: int
    duration_seconds: int | None
    published_at: datetime | None


def parse_iso8601_duration(value: str) -> int | None:
    """Converte durações no formato ISO 8601 da YouTube API (ex.: 'PT4M13S') para segundos."""
    match = _ISO8601_DURATION_RE.match(value)
    if not match:
        return None
    hours = int(match.group("hours") or 0)
    minutes = int(match.group("minutes") or 0)
    seconds = int(match.group("seconds") or 0)
    return hours * 3600 + minutes * 60 + seconds


class YouTubeClient:
    def __init__(self, api_key: str, base_url: str = YOUTUBE_API_BASE_URL) -> None:
        self._api_key = api_key
        self._base_url = base_url

    async def search_videos(self, query: str, max_results: int = 12) -> list[YouTubeVideoData]:
        if not self._api_key:
            raise YouTubeAPIError("YOUTUBE_API_KEY não configurada.")

        async with httpx.AsyncClient(base_url=self._base_url, timeout=10.0) as client:
            video_ids = await self._search_video_ids(client, query, max_results)
            if not video_ids:
                return []
            return await self._fetch_video_details(client, video_ids)

    async def _search_video_ids(
        self, client: httpx.AsyncClient, query: str, max_results: int
    ) -> list[str]:
        data = await self._get(
            client,
            "/search",
            {
                "part": "snippet",
                "q": query,
                "type": "video",
                "maxResults": max_results,
                "key": self._api_key,
            },
        )
        return [item["id"]["videoId"] for item in data.get("items", [])]

    async def _fetch_video_details(
        self, client: httpx.AsyncClient, video_ids: list[str]
    ) -> list[YouTubeVideoData]:
        data = await self._get(
            client,
            "/videos",
            {
                "part": "snippet,statistics,contentDetails",
                "id": ",".join(video_ids),
                "key": self._api_key,
            },
        )
        return [self._parse_video(item) for item in data.get("items", [])]

    async def _get(self, client: httpx.AsyncClient, path: str, params: dict[str, Any]) -> dict:
        try:
            response = await client.get(path, params=params)
        except httpx.HTTPError as exc:
            raise YouTubeAPIError(f"Falha de rede ao chamar a YouTube API: {exc}") from exc

        if response.status_code != httpx.codes.OK:
            raise YouTubeAPIError(
                f"YouTube API retornou {response.status_code}: {response.text[:300]}"
            )
        return response.json()

    @staticmethod
    def _parse_video(item: dict[str, Any]) -> YouTubeVideoData:
        snippet = item.get("snippet", {})
        statistics = item.get("statistics", {})
        content_details = item.get("contentDetails", {})

        published_at_raw = snippet.get("publishedAt")
        published_at = (
            datetime.fromisoformat(published_at_raw.replace("Z", "+00:00"))
            if published_at_raw
            else None
        )

        thumbnails = snippet.get("thumbnails", {})
        thumbnail_url = (
            thumbnails.get("high", {}).get("url")
            or thumbnails.get("medium", {}).get("url")
            or thumbnails.get("default", {}).get("url")
        )

        duration_raw = content_details.get("duration")
        duration_seconds = parse_iso8601_duration(duration_raw) if duration_raw else None

        return YouTubeVideoData(
            youtube_video_id=item["id"],
            youtube_channel_id=snippet.get("channelId", ""),
            channel_title=snippet.get("channelTitle", ""),
            title=snippet.get("title", ""),
            description=snippet.get("description"),
            thumbnail_url=thumbnail_url,
            view_count=int(statistics.get("viewCount", 0)),
            like_count=int(statistics.get("likeCount", 0)),
            comment_count=int(statistics.get("commentCount", 0)),
            duration_seconds=duration_seconds,
            published_at=published_at,
        )
