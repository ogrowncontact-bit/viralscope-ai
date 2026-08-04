from unittest.mock import AsyncMock

from app.integrations.youtube_client import YouTubeAPIError, YouTubeVideoData
from app.services.metrics_sync_service import MetricsSyncService


def _video_data(video_id: str, view_count: int = 100) -> YouTubeVideoData:
    return YouTubeVideoData(
        youtube_video_id=video_id,
        youtube_channel_id="channel-1",
        channel_title="Canal Teste",
        title="Vídeo de teste",
        description=None,
        thumbnail_url=None,
        view_count=view_count,
        like_count=10,
        comment_count=1,
        duration_seconds=120,
        published_at=None,
    )


async def test_sync_tracked_videos_returns_zero_when_no_favorites() -> None:
    repository = AsyncMock()
    repository.list_favorited_video_ids.return_value = []
    youtube_client = AsyncMock()

    service = MetricsSyncService(repository, youtube_client)
    updated = await service.sync_tracked_videos()

    assert updated == 0
    youtube_client.fetch_videos_by_id.assert_not_awaited()


async def test_sync_tracked_videos_updates_metrics_for_each_video() -> None:
    repository = AsyncMock()
    repository.list_favorited_video_ids.return_value = ["abc123", "def456"]
    youtube_client = AsyncMock()
    youtube_client.fetch_videos_by_id.return_value = [
        _video_data("abc123", view_count=1000),
        _video_data("def456", view_count=2000),
    ]

    service = MetricsSyncService(repository, youtube_client)
    updated = await service.sync_tracked_videos()

    assert updated == 2
    youtube_client.fetch_videos_by_id.assert_awaited_once_with(["abc123", "def456"])
    assert repository.update_metrics.await_count == 2
    repository.update_metrics.assert_any_await(
        "abc123", view_count=1000, like_count=10, comment_count=1
    )


async def test_sync_tracked_videos_batches_requests_at_fifty_ids() -> None:
    repository = AsyncMock()
    video_ids = [f"video-{i}" for i in range(120)]
    repository.list_favorited_video_ids.return_value = video_ids
    youtube_client = AsyncMock()
    youtube_client.fetch_videos_by_id.return_value = []

    service = MetricsSyncService(repository, youtube_client)
    await service.sync_tracked_videos()

    assert youtube_client.fetch_videos_by_id.await_count == 3
    call_batches = [call.args[0] for call in youtube_client.fetch_videos_by_id.await_args_list]
    assert [len(batch) for batch in call_batches] == [50, 50, 20]


async def test_sync_tracked_videos_continues_after_batch_failure() -> None:
    repository = AsyncMock()
    video_ids = [f"video-{i}" for i in range(60)]
    repository.list_favorited_video_ids.return_value = video_ids
    youtube_client = AsyncMock()
    youtube_client.fetch_videos_by_id.side_effect = [
        YouTubeAPIError("quota excedida"),
        [_video_data("video-59")],
    ]

    service = MetricsSyncService(repository, youtube_client)
    updated = await service.sync_tracked_videos()

    assert updated == 1
    assert youtube_client.fetch_videos_by_id.await_count == 2
