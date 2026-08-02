from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import CurrentUserDep, get_search_service
from app.integrations.youtube_client import YouTubeAPIError
from app.schemas.search import SearchCreate, SearchOut, SearchResultOut
from app.schemas.video import VideoOut
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


@router.post("", response_model=SearchResultOut, status_code=status.HTTP_201_CREATED)
async def create_search(
    payload: SearchCreate,
    current_user: CurrentUserDep,
    service: SearchServiceDep,
) -> SearchResultOut:
    try:
        search, videos = await service.create_search(current_user.id, payload.query)
    except YouTubeAPIError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(
                "Não foi possível buscar vídeos no YouTube agora. "
                "Sua busca foi salva; tente novamente em instantes."
            ),
        ) from exc

    return SearchResultOut(
        search=SearchOut.model_validate(search),
        videos=[VideoOut.model_validate(video) for video in videos],
    )
