import pytest
import respx
from httpx import Response

from app.integrations.youtube_client import (
    YOUTUBE_API_BASE_URL,
    YouTubeAPIError,
    YouTubeClient,
    parse_iso8601_duration,
)


def test_parse_iso8601_duration_handles_hours_minutes_seconds() -> None:
    assert parse_iso8601_duration("PT1H2M10S") == 3730
    assert parse_iso8601_duration("PT4M13S") == 253
    assert parse_iso8601_duration("PT45S") == 45


def test_parse_iso8601_duration_returns_none_for_invalid_input() -> None:
    assert parse_iso8601_duration("not-a-duration") is None


async def test_search_videos_raises_without_api_key() -> None:
    client = YouTubeClient(api_key="")

    with pytest.raises(YouTubeAPIError):
        await client.search_videos("gatos")


@respx.mock
async def test_search_videos_returns_parsed_videos() -> None:
    respx.get(f"{YOUTUBE_API_BASE_URL}/search").mock(
        return_value=Response(200, json={"items": [{"id": {"videoId": "abc123"}}]})
    )
    respx.get(f"{YOUTUBE_API_BASE_URL}/videos").mock(
        return_value=Response(
            200,
            json={
                "items": [
                    {
                        "id": "abc123",
                        "snippet": {
                            "channelId": "channel-1",
                            "channelTitle": "Canal Teste",
                            "title": "Vídeo de teste",
                            "description": "Descrição",
                            "publishedAt": "2026-01-01T00:00:00Z",
                            "thumbnails": {"high": {"url": "https://example.com/thumb.jpg"}},
                        },
                        "statistics": {
                            "viewCount": "1000",
                            "likeCount": "100",
                            "commentCount": "10",
                        },
                        "contentDetails": {"duration": "PT4M13S"},
                    }
                ]
            },
        )
    )

    client = YouTubeClient(api_key="fake-key")
    videos = await client.search_videos("gatos", max_results=1)

    assert len(videos) == 1
    video = videos[0]
    assert video.youtube_video_id == "abc123"
    assert video.channel_title == "Canal Teste"
    assert video.thumbnail_url == "https://example.com/thumb.jpg"
    assert video.view_count == 1000
    assert video.duration_seconds == 253


@respx.mock
async def test_search_videos_raises_on_http_error() -> None:
    respx.get(f"{YOUTUBE_API_BASE_URL}/search").mock(
        return_value=Response(403, text="quota exceeded")
    )

    client = YouTubeClient(api_key="fake-key")

    with pytest.raises(YouTubeAPIError):
        await client.search_videos("gatos")


@respx.mock
async def test_search_videos_returns_empty_list_when_no_results() -> None:
    respx.get(f"{YOUTUBE_API_BASE_URL}/search").mock(return_value=Response(200, json={"items": []}))

    client = YouTubeClient(api_key="fake-key")
    videos = await client.search_videos("query sem resultados")

    assert videos == []
