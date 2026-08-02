from typing import Protocol

from app.models.user import User


class UserRepositoryProtocol(Protocol):
    async def get_by_clerk_id(self, clerk_user_id: str) -> User | None: ...

    async def get_or_create(self, clerk_user_id: str) -> User: ...

    async def upsert_from_clerk(
        self,
        clerk_user_id: str,
        email: str | None,
        full_name: str | None,
        avatar_url: str | None,
    ) -> User: ...

    async def delete_by_clerk_id(self, clerk_user_id: str) -> None: ...
