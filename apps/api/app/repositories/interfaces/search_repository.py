import uuid
from typing import Protocol

from app.models.search import Search


class SearchRepositoryProtocol(Protocol):
    async def create(self, user_id: uuid.UUID, query: str) -> Search: ...

    async def list_recent(self, user_id: uuid.UUID, limit: int = 10) -> list[Search]: ...

    async def count_by_user(self, user_id: uuid.UUID) -> int: ...
