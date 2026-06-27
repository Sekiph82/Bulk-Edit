"""Video Generator — real ffmpeg-based MP4 generation."""

import os
import shutil
import tempfile
import uuid
from datetime import datetime, timezone
from typing import Optional

import httpx
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import get_current_org_id, require_active_user
from app.db.session import get_db, AsyncSessionLocal
from app.models.video_render import VideoRender
from app.services.video_renderer import (
    check_ffmpeg,
    render_slideshow_mp4,
    RendererNotAvailableError,
    RenderError,
)

router = APIRouter(prefix="/video-generator", tags=["video-generator"])


# --- Schemas ---

class VideoGeneratorStatus(BaseModel):
    renderer_state: str  # "disabled" | "dependency_missing" | "working"
    message: str


class VideoTemplate(BaseModel):
    id: str
    name: str
    description: str
    max_images: int
    duration_seconds_per_image: float
    output_format: str


class RenderRequest(BaseModel):
    template_id: str
    image_urls: list[str]


class RenderResponse(BaseModel):
    id: str
    status: str
    template_id: str
    image_count: int
    created_at: str


class RenderStatusResponse(BaseModel):
    id: str
    status: str
    template_id: str
    image_count: int
    duration_seconds: Optional[float] = None
    file_size_bytes: Optional[int] = None
    error_message: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None


# --- Static template catalog ---

def _get_templates() -> list[VideoTemplate]:
    return [
        VideoTemplate(
            id="slideshow",
            name="Simple Slideshow",
            description="Cycle through listing photos with letterbox padding. Best for product showcases.",
            max_images=settings.VIDEO_MAX_IMAGES,
            duration_seconds_per_image=2.5,
            output_format="MP4 (H.264, 1080×1080)",
        )
    ]


# --- Endpoints ---

@router.get("/status", response_model=VideoGeneratorStatus)
async def get_video_generator_status(
    org_id: str = Depends(get_current_org_id),
    _user=Depends(require_active_user),
):
    state, message = check_ffmpeg()
    return VideoGeneratorStatus(renderer_state=state, message=message)


@router.get("/templates", response_model=list[VideoTemplate])
async def list_video_templates(
    org_id: str = Depends(get_current_org_id),
    _user=Depends(require_active_user),
):
    state, message = check_ffmpeg()
    if state == "disabled":
        raise HTTPException(status_code=503, detail=message)
    return _get_templates()


@router.post("/render", response_model=RenderResponse, status_code=202)
async def create_render(
    req: RenderRequest,
    background_tasks: BackgroundTasks,
    org_id: str = Depends(get_current_org_id),
    _user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    state, message = check_ffmpeg()
    if state != "working":
        raise HTTPException(status_code=503, detail=message)

    if not req.image_urls:
        raise HTTPException(status_code=422, detail="At least one image URL is required.")

    max_imgs = settings.VIDEO_MAX_IMAGES
    if len(req.image_urls) > max_imgs:
        raise HTTPException(status_code=422, detail=f"Maximum {max_imgs} image URLs allowed.")

    templates = _get_templates()
    template = next((t for t in templates if t.id == req.template_id), None)
    if not template:
        raise HTTPException(status_code=404, detail=f"Template '{req.template_id}' not found.")

    render = VideoRender(
        id=str(uuid.uuid4()),
        organization_id=org_id,
        template_id=req.template_id,
        status="pending",
        image_count=len(req.image_urls),
    )
    db.add(render)
    await db.commit()
    await db.refresh(render)

    background_tasks.add_task(
        _run_render,
        render_id=render.id,
        org_id=org_id,
        image_urls=req.image_urls,
        template=template,
    )

    return RenderResponse(
        id=render.id,
        status=render.status,
        template_id=render.template_id,
        image_count=render.image_count,
        created_at=render.created_at.isoformat(),
    )


@router.get("/renders/{render_id}", response_model=RenderStatusResponse)
async def get_render_status(
    render_id: str,
    org_id: str = Depends(get_current_org_id),
    _user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(VideoRender).where(
            VideoRender.id == render_id,
            VideoRender.organization_id == org_id,
        )
    )
    render = result.scalar_one_or_none()
    if not render:
        raise HTTPException(status_code=404, detail="Render not found.")

    return RenderStatusResponse(
        id=render.id,
        status=render.status,
        template_id=render.template_id,
        image_count=render.image_count,
        duration_seconds=render.duration_seconds,
        file_size_bytes=render.file_size_bytes,
        error_message=render.error_message,
        created_at=render.created_at.isoformat(),
        completed_at=render.completed_at.isoformat() if render.completed_at else None,
    )


@router.get("/renders/{render_id}/download")
async def download_render(
    render_id: str,
    org_id: str = Depends(get_current_org_id),
    _user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(VideoRender).where(
            VideoRender.id == render_id,
            VideoRender.organization_id == org_id,
        )
    )
    render = result.scalar_one_or_none()
    if not render:
        raise HTTPException(status_code=404, detail="Render not found.")
    if render.status != "completed":
        raise HTTPException(status_code=409, detail=f"Render is not ready (status: {render.status}).")
    if not render.file_path or not os.path.exists(render.file_path):
        raise HTTPException(status_code=410, detail="Render file is no longer available.")

    return FileResponse(
        path=render.file_path,
        media_type="video/mp4",
        filename=f"product_video_{render_id[:8]}.mp4",
    )


# --- Background task ---

async def _run_render(
    render_id: str,
    org_id: str,
    image_urls: list[str],
    template: VideoTemplate,
) -> None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(VideoRender).where(VideoRender.id == render_id))
        render = result.scalar_one_or_none()
        if not render:
            return
        render.status = "rendering"
        await db.commit()

    tmp_dir = tempfile.mkdtemp(prefix=f"vr_{render_id[:8]}_")
    try:
        local_paths = await _download_images(image_urls, tmp_dir)

        if not local_paths:
            await _mark_failed(render_id, "No images could be downloaded.")
            return

        output_dir = os.path.join(settings.VIDEO_OUTPUT_DIR, org_id)
        output_path = await render_slideshow_mp4(
            image_paths=local_paths,
            output_dir=output_dir,
            duration_per_image=template.duration_seconds_per_image,
        )

        duration = min(
            len(local_paths) * template.duration_seconds_per_image,
            float(settings.VIDEO_MAX_DURATION_SECONDS),
        )

        async with AsyncSessionLocal() as db:
            result = await db.execute(select(VideoRender).where(VideoRender.id == render_id))
            render = result.scalar_one_or_none()
            if render:
                render.status = "completed"
                render.file_path = output_path
                render.file_size_bytes = os.path.getsize(output_path)
                render.duration_seconds = duration
                render.completed_at = datetime.now(timezone.utc)
                await db.commit()

    except (RendererNotAvailableError, RenderError) as exc:
        await _mark_failed(render_id, str(exc))
    except Exception:
        await _mark_failed(render_id, "Internal render error.")
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


async def _download_images(urls: list[str], dest_dir: str) -> list[str]:
    local_paths: list[str] = []
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        for i, url in enumerate(urls):
            try:
                resp = await client.get(url)
                resp.raise_for_status()
                ext = _guess_ext(resp.headers.get("content-type", ""))
                path = os.path.join(dest_dir, f"{i:04d}{ext}")
                with open(path, "wb") as f:
                    f.write(resp.content)
                local_paths.append(path)
            except Exception:
                pass  # Skip images that fail to download
    return local_paths


async def _mark_failed(render_id: str, message: str) -> None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(VideoRender).where(VideoRender.id == render_id))
        render = result.scalar_one_or_none()
        if render:
            render.status = "failed"
            render.error_message = message
            render.completed_at = datetime.now(timezone.utc)
            await db.commit()


def _guess_ext(content_type: str) -> str:
    for mime, ext in [
        ("image/jpeg", ".jpg"),
        ("image/png", ".png"),
        ("image/webp", ".webp"),
        ("image/gif", ".gif"),
    ]:
        if mime in content_type:
            return ext
    return ".jpg"
