"""Video Generator — product video generation config and job management."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.deps import get_current_org_id, require_active_user
from app.core.config import settings

router = APIRouter(prefix="/video-generator", tags=["video-generator"])


class VideoGeneratorStatus(BaseModel):
    renderer_enabled: bool
    message: str


@router.get("/status", response_model=VideoGeneratorStatus)
async def get_video_generator_status(
    org_id: str = Depends(get_current_org_id),
    _user=Depends(require_active_user),
):
    if settings.VIDEO_RENDERER_ENABLED:
        return VideoGeneratorStatus(
            renderer_enabled=True,
            message="Video renderer is available.",
        )
    return VideoGeneratorStatus(
        renderer_enabled=False,
        message="Video renderer is not configured. Set VIDEO_RENDERER_ENABLED=true to enable.",
    )
