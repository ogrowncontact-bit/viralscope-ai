from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.dependencies import CurrentUserDep, get_dashboard_service
from app.schemas.dashboard import DashboardStats
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    current_user: CurrentUserDep,
    service: Annotated[DashboardService, Depends(get_dashboard_service)],
) -> DashboardStats:
    return await service.get_stats(current_user.id)
