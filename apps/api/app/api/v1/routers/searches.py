from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.dependencies import CurrentUserDep, get_search_service
from app.schemas.search import SearchCreate, SearchOut
from app.services.search_service import SearchService

router = APIRouter(prefix="/searches", tags=["searches"])

SearchServiceDep = Annotated[SearchService, Depends(get_search_service)]


@router.get("/recent", response_model=list[SearchOut])
async def list_recent_searches(
    current_user: CurrentUserDep,
    service: SearchServiceDep,
) -> list[SearchOut]:
    searches = await service.list_recent(current_user.id)
    return [SearchOut.model_validate(search) for search in searches]


@router.post("", response_model=SearchOut, status_code=status.HTTP_201_CREATED)
async def create_search(
    payload: SearchCreate,
    current_user: CurrentUserDep,
    service: SearchServiceDep,
) -> SearchOut:
    search = await service.create_search(current_user.id, payload.query)
    return SearchOut.model_validate(search)
