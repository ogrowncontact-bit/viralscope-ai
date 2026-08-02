import uuid
from typing import Protocol


class AnalysisRepositoryProtocol(Protocol):
    async def count_by_user(self, user_id: uuid.UUID) -> int: ...
