from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class SqlAlchemyHealthRepository:
    """Implementação concreta de HealthRepositoryProtocol usando SQLAlchemy/Postgres."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def check_connection(self) -> bool:
        result = await self._session.execute(text("SELECT 1"))
        return result.scalar_one() == 1
