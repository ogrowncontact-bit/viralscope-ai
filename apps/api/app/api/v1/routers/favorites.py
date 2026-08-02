import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import CurrentUserDep, get_favorite_service
from app.schemas.favorite import FavoriteVideoOut
from app.services.favorite_service import FavoriteService

router = APIRouter(prefix="/favorites", tags=["favorites"])

FavoriteServiceDep = Annotated[FavoriteService, Depends(get_favorite_service)]


@router.get("", response_model=list[FavoriteVideoOut])
async def list_favorites(
    current_user: CurrentUserDep,
    service: FavoriteServiceDep,
) -> list[FavoriteVideoOut]:
    favorites = await service.list_favorites(current_user.id)
    return [
        FavoriteVideoOut(
            favorite_id=favorite.id,
            video_id=video.id,
            youtube_video_id=video.youtube_video_id,
            title=video.title,
            thumbnail_url=video.thumbnail_url,
            channel_title=video.channel_title,
            favorited_at=favorite.created_at,
        )
        for favorite, video in favorites
    ]


@router.post("/{video_id}", status_code=status.HTTP_204_NO_CONTENT)
async def add_favorite(
    video_id: uuid.UUID,
    current_user: CurrentUserDep,
    service: FavoriteServiceDep,
) -> None:
    await service.add_favorite(current_user.id, video_id)


@router.delete("/{video_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_favorite(
    video_id: uuid.UUID,
    current_user: CurrentUserDep,
    service: FavoriteServiceDep,
) -> None:
    removed = await service.remove_favorite(current_user.id, video_id)
    if not removed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Favorito não encontrado")
