import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class FavoriteVideoOut(BaseModel):
    """Vídeo favoritado, com os dados do vídeo já embutidos (evita N+1 no cliente)."""

    model_config = ConfigDict(from_attributes=True)

    favorite_id: uuid.UUID
    video_id: uuid.UUID
    youtube_video_id: str
    title: str
    thumbnail_url: str | None
    channel_title: str
    favorited_at: datetime
