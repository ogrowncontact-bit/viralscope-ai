from typing import Protocol


class HealthRepositoryProtocol(Protocol):
    """Contrato que qualquer implementação de verificação de banco deve seguir.

    O service layer depende desta interface, não da implementação concreta —
    isso é o que permite trocar Postgres por outra fonte, ou usar um fake em
    teste, sem tocar em app/services.
    """

    async def check_connection(self) -> bool: ...
