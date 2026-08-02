import uuid

from app.models.search import Search
from app.repositories.interfaces.search_repository import SearchRepositoryProtocol


class SearchService:
    def __init__(self, repository: SearchRepositoryProtocol) -> None:
        self._repository = repository

    async def create_search(self, user_id: uuid.UUID, query: str) -> Search:
        return await self._repository.create(user_id, query.strip())

    async def list_recent(self, user_id: uuid.UUID, limit: int = 10) -> list[Search]:
        return await self._repository.list_recent(user_id, limit)
