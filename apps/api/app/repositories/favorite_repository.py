import uuid

from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.favorite import Favorite
from app.models.video import Video


class SqlAlchemyFavoriteRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_with_video(self, user_id: uuid.UUID) -> list[tuple[Favorite, Video]]:
        result = await self._session.execute(
            select(Favorite, Video)
            .join(Video, Favorite.video_id == Video.id)
            .where(Favorite.user_id == user_id)
            .order_by(Favorite.created_at.desc())
        )
        return [(favorite, video) for favorite, video in result.all()]

    async def add(self, user_id: uuid.UUID, video_id: uuid.UUID) -> Favorite:
        favorite = Favorite(user_id=user_id, video_id=video_id)
        self._session.add(favorite)
        try:
            await self._session.commit()
        except IntegrityError:
            await self._session.rollback()
            result = await self._session.execute(
                select(Favorite).where(Favorite.user_id == user_id, Favorite.video_id == video_id)
            )
            return result.scalar_one()
        await self._session.refresh(favorite)
        return favorite

    async def remove(self, user_id: uuid.UUID, video_id: uuid.UUID) -> bool:
        result = await self._session.execute(
            delete(Favorite).where(Favorite.user_id == user_id, Favorite.video_id == video_id)
        )
        await self._session.commit()
        return result.rowcount > 0

    async def count_by_user(self, user_id: uuid.UUID) -> int:
        result = await self._session.execute(
            select(func.count()).select_from(Favorite).where(Favorite.user_id == user_id)
        )
        return result.scalar_one()
