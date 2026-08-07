import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import CurrentUserDep, get_analysis_service, get_video_service
from app.schemas.analysis import AnalysisOut
from app.schemas.video import VideoOut
from app.services.analysis_service import AnalysisService
from app.services.video_service import VideoService

router = APIRouter(prefix="/videos", tags=["videos"])

VideoServiceDep = Annotated[VideoService, Depends(get_video_service)]
AnalysisServiceDep = Annotated[AnalysisService, Depends(get_analysis_service)]


@router.post(
    "/{video_id}/transcribe", response_model=VideoOut, status_code=status.HTTP_202_ACCEPTED
)
async def trigger_video_transcription(
    video_id: uuid.UUID,
    current_user: CurrentUserDep,
    service: VideoServiceDep,
) -> VideoOut:
    video = await service.trigger_transcription(video_id)
    if video is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vídeo não encontrado")

    return VideoOut.model_validate(video)


@router.post(
    "/{video_id}/analyze", response_model=AnalysisOut, status_code=status.HTTP_202_ACCEPTED
)
async def trigger_video_analysis(
    video_id: uuid.UUID,
    current_user: CurrentUserDep,
    service: AnalysisServiceDep,
) -> AnalysisOut:
    analysis = await service.trigger_analysis(video_id, current_user.id)
    if analysis is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vídeo não encontrado")

    return AnalysisOut.model_validate(analysis)
