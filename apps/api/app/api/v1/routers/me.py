from fastapi import APIRouter

from app.core.dependencies import CurrentUserDep
from app.schemas.user import UserProfile

router = APIRouter(prefix="/me", tags=["me"])


@router.get("", response_model=UserProfile)
async def get_me(current_user: CurrentUserDep) -> UserProfile:
    return UserProfile.model_validate(current_user)
