from app.models.user import User
from app.repositories.interfaces.user_repository import UserRepositoryProtocol


class UserService:
    def __init__(self, repository: UserRepositoryProtocol) -> None:
        self._repository = repository

    async def get_or_create_current_user(self, clerk_user_id: str) -> User:
        return await self._repository.get_or_create(clerk_user_id)

    async def sync_from_clerk(
        self,
        clerk_user_id: str,
        email: str | None,
        full_name: str | None,
        avatar_url: str | None,
    ) -> User:
        return await self._repository.upsert_from_clerk(clerk_user_id, email, full_name, avatar_url)

    async def delete_from_clerk(self, clerk_user_id: str) -> None:
        await self._repository.delete_by_clerk_id(clerk_user_id)
