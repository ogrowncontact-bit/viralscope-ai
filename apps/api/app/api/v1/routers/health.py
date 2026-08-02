from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.dependencies import get_health_service
from app.schemas.health import HealthStatus
from app.services.health_service import HealthService

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthStatus)
async def get_health(
    service: Annotated[HealthService, Depends(get_health_service)],
) -> HealthStatus:
    return await service.get_health_status()
