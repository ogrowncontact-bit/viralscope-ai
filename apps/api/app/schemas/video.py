import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class VideoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    youtube_video_id: str
    title: str
    channel_title: str
    thumbnail_url: str | None
    view_count: int
    like_count: int
    comment_count: int
    duration_seconds: int | None
    published_at: datetime | None
