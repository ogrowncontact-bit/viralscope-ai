from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class SqlAlchemyUserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_clerk_id(self, clerk_user_id: str) -> User | None:
        result = await self._session.execute(
            select(User).where(User.clerk_user_id == clerk_user_id)
        )
        return result.scalar_one_or_none()

    async def get_or_create(self, clerk_user_id: str) -> User:
        user = await self.get_by_clerk_id(clerk_user_id)
        if user is not None:
            return user

        user = User(clerk_user_id=clerk_user_id)
        self._session.add(user)
        await self._session.commit()
        await self._session.refresh(user)
        return user

    async def upsert_from_clerk(
        self,
        clerk_user_id: str,
        email: str | None,
        full_name: str | None,
        avatar_url: str | None,
    ) -> User:
        stmt = (
            insert(User)
            .values(
                clerk_user_id=clerk_user_id,
                email=email,
                full_name=full_name,
                avatar_url=avatar_url,
            )
            .on_conflict_do_update(
                index_elements=[User.clerk_user_id],
                set_={"email": email, "full_name": full_name, "avatar_url": avatar_url},
            )
            .returning(User)
        )
        result = await self._session.execute(stmt)
        await self._session.commit()
        return result.scalar_one()

    async def delete_by_clerk_id(self, clerk_user_id: str) -> None:
        user = await self.get_by_clerk_id(clerk_user_id)
        if user is not None:
            await self._session.delete(user)
            await self._session.commit()
