from pydantic import BaseModel


class HealthStatus(BaseModel):
    """DTO de saída do endpoint de health-check. Nunca expõe models de banco."""

    status: str
    database: str
    environment: str
