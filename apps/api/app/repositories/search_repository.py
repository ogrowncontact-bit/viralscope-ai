import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.search import Search


class SqlAlchemySearchRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, user_id: uuid.UUID, query: str) -> Search:
        search = Search(user_id=user_id, query=query)
        self._session.add(search)
        await self._session.commit()
        await self._session.refresh(search)
        return search

    async def list_recent(self, user_id: uuid.UUID, limit: int = 10) -> list[Search]:
        result = await self._session.execute(
            select(Search)
            .where(Search.user_id == user_id)
            .order_by(Search.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_by_user(self, user_id: uuid.UUID) -> int:
        result = await self._session.execute(
            select(func.count()).select_from(Search).where(Search.user_id == user_id)
        )
        return result.scalar_one()
