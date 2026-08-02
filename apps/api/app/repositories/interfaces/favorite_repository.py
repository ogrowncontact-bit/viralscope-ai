import uuid
from typing import Protocol

from app.models.favorite import Favorite
from app.models.video import Video


class FavoriteRepositoryProtocol(Protocol):
    async def list_with_video(self, user_id: uuid.UUID) -> list[tuple[Favorite, Video]]: ...

    async def add(self, user_id: uuid.UUID, video_id: uuid.UUID) -> Favorite: ...

    async def remove(self, user_id: uuid.UUID, video_id: uuid.UUID) -> bool: ...

    async def count_by_user(self, user_id: uuid.UUID) -> int: ...
