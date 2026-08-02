import uuid

from app.models.favorite import Favorite
from app.models.video import Video
from app.repositories.interfaces.favorite_repository import FavoriteRepositoryProtocol


class FavoriteService:
    def __init__(self, repository: FavoriteRepositoryProtocol) -> None:
        self._repository = repository

    async def list_favorites(self, user_id: uuid.UUID) -> list[tuple[Favorite, Video]]:
        return await self._repository.list_with_video(user_id)

    async def add_favorite(self, user_id: uuid.UUID, video_id: uuid.UUID) -> Favorite:
        return await self._repository.add(user_id, video_id)

    async def remove_favorite(self, user_id: uuid.UUID, video_id: uuid.UUID) -> bool:
        return await self._repository.remove(user_id, video_id)
