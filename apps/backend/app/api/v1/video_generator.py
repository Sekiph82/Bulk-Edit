"""Video Generator — real ffmpeg-based MP4 generation compliant with Etsy video specs."""

import hashlib
import json
import os
import shutil
import tempfile
import uuid
from datetime import datetime, timezone
from typing import Optional

import httpx
from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import get_current_org_id, require_active_user
from app.db.session import get_db, AsyncSessionLocal
from app.models.video_render import VideoRender
from app.models.listing import Listing
from app.models.listing_video import ListingVideo
from app.services.video_renderer import (
    ASPECT_RATIO_PRESETS,
    ETSY_MAX_FILE_SIZE_BYTES,
    ETSY_MIN_DURATION,
    ETSY_MAX_DURATION,
    ETSY_MIN_RESOLUTION,
    check_ffmpeg,
    check_ffprobe,
    check_etsy_ready,
    classify_aspect_ratio,
    probe_video_file,
    render_slideshow_mp4,
    ProbeError,
    RendererNotAvailableError,
    RenderError,
)

# Only MP4 is accepted for direct upload — it's the one format Etsy's own
# upload endpoint and our validation pipeline (ffprobe + check_etsy_ready)
# actually verify. MOV/WEBM would need a transcode step we don't have, so
# they're rejected rather than silently accepted and failing later at Etsy.
ALLOWED_UPLOAD_VIDEO_CONTENT_TYPES = {"video/mp4"}
ALLOWED_UPLOAD_VIDEO_EXTENSIONS = {".mp4"}

router = APIRouter(prefix="/video-generator", tags=["video-generator"])


# --- Schemas ---

class VideoGeneratorStatus(BaseModel):
    renderer_enabled: bool
    renderer_available: bool
    message: str


class AspectRatioOption(BaseModel):
    value: str
    label: str
    width: int
    height: int
    recommended: bool = False


class EtsySpecs(BaseModel):
    max_file_size_mb: int
    min_duration_seconds: int
    max_duration_seconds: int
    min_resolution_px: int
    supported_aspect_ratios: list[str]
    format: str


class VideoTemplate(BaseModel):
    id: str
    name: str
    description: str
    implemented: bool
    max_images: int
    output_format: str


class TemplatesResponse(BaseModel):
    templates: list[VideoTemplate]
    aspect_ratios: list[AspectRatioOption]
    etsy_specs: EtsySpecs
    renderer_enabled: bool
    renderer_available: bool


LOGO_POSITIONS = {"top-left", "top-right", "bottom-left", "bottom-right"}
TEXT_PLACEMENTS = {"bottom", "center", "intro-card", "outro-card"}
_HEX_COLOR_RE = __import__("re").compile(r"^#[0-9A-Fa-f]{6}$")


class BrandingInput(BaseModel):
    """Optional branding overlay (M13.05C). Text fields are burned into the
    local MP4 via ffmpeg drawtext; logo_url is accepted/stored but NOT rendered
    server-side (SSRF risk without a safe allowlist/proxy) — logo stays
    preview-only. Nothing here is ever uploaded to Etsy."""
    logo_url: Optional[str] = Field(default=None, max_length=2000)
    headline: Optional[str] = Field(default=None, max_length=60)
    slogan: Optional[str] = Field(default=None, max_length=80)
    outro_text: Optional[str] = Field(default=None, max_length=80)
    cta_text: Optional[str] = Field(default=None, max_length=30)
    logo_position: str = Field(default="bottom-right")
    text_placement: str = Field(default="bottom")
    brand_color: Optional[str] = Field(default=None)

    @field_validator("logo_position")
    @classmethod
    def _valid_logo_position(cls, v: str) -> str:
        if v not in LOGO_POSITIONS:
            raise ValueError(f"logo_position must be one of {sorted(LOGO_POSITIONS)}")
        return v

    @field_validator("text_placement")
    @classmethod
    def _valid_text_placement(cls, v: str) -> str:
        if v not in TEXT_PLACEMENTS:
            raise ValueError(f"text_placement must be one of {sorted(TEXT_PLACEMENTS)}")
        return v

    @field_validator("brand_color")
    @classmethod
    def _valid_color(cls, v: Optional[str]) -> Optional[str]:
        if v in (None, ""):
            return None
        if not _HEX_COLOR_RE.match(v):
            raise ValueError("brand_color must be a #RRGGBB hex color")
        return v

    def has_text(self) -> bool:
        return any(bool((getattr(self, f) or "").strip())
                   for f in ("headline", "slogan", "outro_text", "cta_text"))

    def to_render_dict(self) -> dict:
        """Map to the renderer's branding keys (headline/slogan/cta/outro/…)."""
        return {
            "headline": self.headline or "",
            "slogan": self.slogan or "",
            "cta": self.cta_text or "",
            "outro": self.outro_text or "",
            "brand_color": self.brand_color or "",
            "text_placement": self.text_placement,
            "logo_position": self.logo_position,
            "logo_url": self.logo_url or "",
        }


class RenderRequest(BaseModel):
    template_id: str
    image_urls: list[str]
    aspect_ratio: str = Field(default="9:16")
    duration_seconds: float = Field(default=10.0, ge=1.0, le=60.0)
    branding: Optional[BrandingInput] = None


class RenderResponse(BaseModel):
    id: str
    status: str
    template_id: str
    image_count: int
    aspect_ratio: str
    duration_seconds: float
    created_at: str


class RenderStatusResponse(BaseModel):
    id: str
    status: str
    template_id: str
    source: str = "generated"
    image_count: int
    aspect_ratio: Optional[str] = None
    duration_seconds: Optional[float] = None
    width: Optional[int] = None
    height: Optional[int] = None
    file_size_bytes: Optional[int] = None
    is_etsy_ready: Optional[bool] = None
    etsy_issues: Optional[list[str]] = None
    error_message: Optional[str] = None
    download_url: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None
    branding: Optional[dict] = None
    branding_text_rendered: Optional[bool] = None


# --- Static data ---

def _aspect_ratio_options() -> list[AspectRatioOption]:
    return [
        AspectRatioOption(value="9:16", label="9:16 Vertical (Recommended)", width=1080, height=1920, recommended=True),
        AspectRatioOption(value="1:1", label="1:1 Square", width=1080, height=1080),
        AspectRatioOption(value="4:5", label="4:5 Vertical", width=1080, height=1350),
        AspectRatioOption(value="16:9", label="16:9 Horizontal", width=1920, height=1080),
    ]


def _etsy_specs() -> EtsySpecs:
    return EtsySpecs(
        max_file_size_mb=100,
        min_duration_seconds=ETSY_MIN_DURATION,
        max_duration_seconds=ETSY_MAX_DURATION,
        min_resolution_px=ETSY_MIN_RESOLUTION,
        supported_aspect_ratios=list(ASPECT_RATIO_PRESETS.keys()),
        format="MP4 (H.264)",
    )


def _get_templates() -> list[VideoTemplate]:
    return [
        VideoTemplate(
            id="clean_zoom",
            name="Clean Zoom",
            description="Gentle zoom on each product photo with letterbox padding. Best for product showcases.",
            implemented=True,
            max_images=settings.VIDEO_MAX_IMAGES,
            output_format="MP4 (H.264)",
        ),
        VideoTemplate(
            id="soft_pan",
            name="Soft Pan",
            description="Subtle horizontal pan across each photo. Coming soon.",
            implemented=False,
            max_images=settings.VIDEO_MAX_IMAGES,
            output_format="MP4 (H.264)",
        ),
        VideoTemplate(
            id="marketplace_promo",
            name="Marketplace Promo",
            description="Bold title card intro with product photos. Coming soon.",
            implemented=False,
            max_images=settings.VIDEO_MAX_IMAGES,
            output_format="MP4 (H.264)",
        ),
    ]


# --- Endpoints ---

@router.get("/status", response_model=VideoGeneratorStatus)
async def get_video_generator_status(
    org_id: str = Depends(get_current_org_id),
    _user=Depends(require_active_user),
):
    renderer_enabled = settings.VIDEO_RENDERER_ENABLED
    state, message = check_ffmpeg()
    return VideoGeneratorStatus(
        renderer_enabled=renderer_enabled,
        renderer_available=(state == "working"),
        message=message,
    )


@router.get("/templates", response_model=TemplatesResponse)
async def list_video_templates(
    org_id: str = Depends(get_current_org_id),
    _user=Depends(require_active_user),
):
    state, _msg = check_ffmpeg()
    renderer_enabled = settings.VIDEO_RENDERER_ENABLED
    renderer_available = state == "working"
    return TemplatesResponse(
        templates=_get_templates(),
        aspect_ratios=_aspect_ratio_options(),
        etsy_specs=_etsy_specs(),
        renderer_enabled=renderer_enabled,
        renderer_available=renderer_available,
    )


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

    if req.aspect_ratio not in ASPECT_RATIO_PRESETS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid aspect ratio '{req.aspect_ratio}'. Must be one of: {', '.join(ASPECT_RATIO_PRESETS)}.",
        )

    if req.duration_seconds < ETSY_MIN_DURATION:
        raise HTTPException(status_code=400, detail="Video duration must be at least 5 seconds.")

    if req.duration_seconds > ETSY_MAX_DURATION:
        raise HTTPException(status_code=400, detail="Video duration must be 15 seconds or less.")

    if not req.image_urls:
        raise HTTPException(status_code=422, detail="At least one image URL is required.")

    max_imgs = settings.VIDEO_MAX_IMAGES
    if len(req.image_urls) > max_imgs:
        raise HTTPException(status_code=422, detail=f"Maximum {max_imgs} image URLs allowed.")

    templates = _get_templates()
    template = next((t for t in templates if t.id == req.template_id), None)
    if not template:
        raise HTTPException(status_code=404, detail=f"Template '{req.template_id}' not found.")
    if not template.implemented:
        raise HTTPException(
            status_code=400,
            detail=f"Template '{req.template_id}' is not yet available. Use 'clean_zoom'.",
        )

    branding_dict = req.branding.to_render_dict() if req.branding else None
    render = VideoRender(
        id=str(uuid.uuid4()),
        organization_id=org_id,
        template_id=req.template_id,
        status="pending",
        image_count=len(req.image_urls),
        aspect_ratio=req.aspect_ratio,
        duration_seconds=req.duration_seconds,
        branding_json=json.dumps({**branding_dict, "text_rendered": None, "logo_rendered": False})
        if branding_dict else None,
    )
    db.add(render)
    await db.commit()
    await db.refresh(render)

    background_tasks.add_task(
        _run_render,
        render_id=render.id,
        org_id=org_id,
        image_urls=req.image_urls,
        aspect_ratio=req.aspect_ratio,
        duration_seconds=req.duration_seconds,
        branding=branding_dict,
    )

    return RenderResponse(
        id=render.id,
        status=render.status,
        template_id=render.template_id,
        image_count=render.image_count,
        aspect_ratio=render.aspect_ratio or req.aspect_ratio,
        duration_seconds=render.duration_seconds or req.duration_seconds,
        created_at=render.created_at.isoformat(),
    )


@router.get("/renders", response_model=list[RenderStatusResponse])
async def list_renders(
    etsy_ready_only: bool = False,
    all_statuses: bool = False,
    org_id: str = Depends(get_current_org_id),
    _user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    """List this org's video renders, newest first. Default (all_statuses=
    False) — completed only — is used to pick a render to upload to a
    listing (see bulk-edit/media replace_video). all_statuses=True powers
    the Video Generator's own render history view (M13.05), which also
    needs to show pending/rendering/failed renders, not just ones ready to
    use."""
    query = select(VideoRender).where(VideoRender.organization_id == org_id)
    if not all_statuses:
        query = query.where(VideoRender.status == "completed")
    if etsy_ready_only:
        query = query.where(VideoRender.is_etsy_ready.is_(True))
    query = query.order_by(VideoRender.created_at.desc()).limit(50)

    result = await db.execute(query)
    renders = result.scalars().all()

    return [
        RenderStatusResponse(
            id=r.id,
            status=r.status,
            template_id=r.template_id,
            source=r.source,
            image_count=r.image_count,
            aspect_ratio=r.aspect_ratio,
            duration_seconds=r.duration_seconds,
            width=r.width,
            height=r.height,
            file_size_bytes=r.file_size_bytes,
            is_etsy_ready=r.is_etsy_ready,
            etsy_issues=r.get_etsy_issues() if r.is_etsy_ready is not None else None,
            error_message=r.error_message,
            download_url=f"/api/v1/video-generator/renders/{r.id}/download",
            created_at=r.created_at.isoformat(),
            completed_at=r.completed_at.isoformat() if r.completed_at else None,
            branding=r.get_branding(),
            branding_text_rendered=(r.get_branding() or {}).get("text_rendered"),
        )
        for r in renders
    ]


@router.post("/uploads", response_model=RenderStatusResponse, status_code=201)
async def upload_video_file(
    file: UploadFile = File(...),
    org_id: str = Depends(get_current_org_id),
    _user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a local MP4 file so it can be selected by Add Video / Replace Video
    on the private /media page. The file is validated and stored server-side
    immediately — this endpoint never contacts Etsy; nothing is sent to Etsy
    until a media job that references this video is applied.
    """
    content_type = (file.content_type or "").split(";")[0].strip().lower()
    ext = os.path.splitext(file.filename or "")[1].lower()
    if content_type not in ALLOWED_UPLOAD_VIDEO_CONTENT_TYPES or ext not in ALLOWED_UPLOAD_VIDEO_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only MP4 video files are supported for upload.")

    state, message = check_ffprobe()
    if state != "working":
        raise HTTPException(status_code=503, detail=f"Video upload validation unavailable: {message}")

    # Never build a filesystem path directly out of org_id: hash it into a
    # fixed-length hex string first. This is the standard fix for path
    # injection on an identifier that's otherwise trusted (our own DB UUID)
    # but still counts as request-derived — a hex digest can't contain "/"
    # or "..", so there is no path to sanitize around.
    org_dir_name = hashlib.sha256(org_id.encode("utf-8")).hexdigest()
    org_dir = os.path.join(settings.VIDEO_OUTPUT_DIR, org_dir_name, "uploads")
    os.makedirs(org_dir, exist_ok=True)
    render_id = str(uuid.uuid4())
    output_path = os.path.join(org_dir, f"{render_id}.mp4")

    file_size_bytes = 0
    chunk_size = 1024 * 1024
    try:
        with open(output_path, "wb") as out:
            while True:
                chunk = await file.read(chunk_size)
                if not chunk:
                    break
                file_size_bytes += len(chunk)
                if file_size_bytes > ETSY_MAX_FILE_SIZE_BYTES:
                    mb = ETSY_MAX_FILE_SIZE_BYTES // (1024 * 1024)
                    raise HTTPException(status_code=413, detail=f"Video file too large. Max {mb} MB.")
                out.write(chunk)
    except HTTPException:
        if os.path.exists(output_path):
            os.remove(output_path)
        raise
    finally:
        await file.close()

    try:
        probe = probe_video_file(output_path)
    except ProbeError as exc:
        os.remove(output_path)
        raise HTTPException(status_code=400, detail=f"Could not read video file: {exc}")

    width = probe["width"]
    height = probe["height"]
    duration_seconds = probe["duration_seconds"]
    aspect_ratio = classify_aspect_ratio(width, height)

    is_etsy_ready, issues = check_etsy_ready(
        file_size_bytes=file_size_bytes,
        duration_seconds=duration_seconds,
        aspect_ratio=aspect_ratio or "unsupported",
        width=width,
        height=height,
    )

    render = VideoRender(
        id=render_id,
        organization_id=org_id,
        template_id="uploaded",
        source="uploaded",
        status="completed",
        image_count=0,
        aspect_ratio=aspect_ratio,
        duration_seconds=duration_seconds,
        file_size_bytes=file_size_bytes,
        width=width,
        height=height,
        is_etsy_ready=is_etsy_ready,
        etsy_issues_json=json.dumps(issues),
        file_path=output_path,
        completed_at=datetime.now(timezone.utc),
    )
    db.add(render)
    await db.commit()
    await db.refresh(render)

    return RenderStatusResponse(
        id=render.id,
        status=render.status,
        template_id=render.template_id,
        source=render.source,
        image_count=render.image_count,
        aspect_ratio=render.aspect_ratio,
        duration_seconds=render.duration_seconds,
        width=render.width,
        height=render.height,
        file_size_bytes=render.file_size_bytes,
        is_etsy_ready=render.is_etsy_ready,
        etsy_issues=render.get_etsy_issues(),
        error_message=render.error_message,
        download_url=f"/api/v1/video-generator/renders/{render.id}/download",
        created_at=render.created_at.isoformat(),
        completed_at=render.completed_at.isoformat() if render.completed_at else None,
        branding=render.get_branding(),
        branding_text_rendered=(render.get_branding() or {}).get("text_rendered"),
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

    download_url = (
        f"/api/v1/video-generator/renders/{render.id}/download"
        if render.status == "completed"
        else None
    )

    return RenderStatusResponse(
        id=render.id,
        status=render.status,
        template_id=render.template_id,
        source=render.source,
        image_count=render.image_count,
        aspect_ratio=render.aspect_ratio,
        duration_seconds=render.duration_seconds,
        width=render.width,
        height=render.height,
        file_size_bytes=render.file_size_bytes,
        is_etsy_ready=render.is_etsy_ready,
        etsy_issues=render.get_etsy_issues() if render.is_etsy_ready is not None else None,
        error_message=render.error_message,
        download_url=download_url,
        created_at=render.created_at.isoformat(),
        completed_at=render.completed_at.isoformat() if render.completed_at else None,
        branding=render.get_branding(),
        branding_text_rendered=(render.get_branding() or {}).get("text_rendered"),
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


# --- M13.03: gated Etsy video-upload intent (dry-run plan; never uploads) ---

class EtsyUploadIntentRequest(BaseModel):
    listing_id: Optional[str] = None  # target listing (org-scoped); omit for a generic plan


class EtsyUploadIntentResponse(BaseModel):
    enabled: bool                      # ETSY_VIDEO_UPLOAD_ENABLED
    allowed: bool                      # whether a real upload could proceed right now
    disabled_reason: Optional[str] = None
    render_id: str
    render_ready: bool
    listing_id: Optional[str] = None
    listing_title: Optional[str] = None
    video_slot_synced: bool            # do we know the listing's current video state?
    has_existing_video: Optional[bool] = None
    operation: Optional[str] = None    # "add_video" | "replace_video"
    replace_supported: bool            # replace also needs MEDIA_DESTRUCTIVE_ACTIONS_ENABLED + re-uploadable backup
    no_auto_upload: bool = True
    message: str


@router.post("/renders/{render_id}/etsy-upload-intent", response_model=EtsyUploadIntentResponse)
async def etsy_upload_intent(
    render_id: str,
    req: EtsyUploadIntentRequest,
    org_id: str = Depends(get_current_org_id),
    _user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    """M13.03 architecture — a READ-ONLY dry-run that powers the Upload to Etsy
    modal. It NEVER calls Etsy and NEVER creates or applies an upload job; it
    only reports what a future, owner-approved upload would do (target listing,
    current video slot, add vs replace, and why it is disabled). Real upload is
    a separate, explicit, feature-flagged action through the media-job path."""
    render_q = await db.execute(
        select(VideoRender).where(
            VideoRender.id == render_id,
            VideoRender.organization_id == org_id,
        )
    )
    render = render_q.scalar_one_or_none()
    if not render:
        raise HTTPException(status_code=404, detail="Render not found.")
    render_ready = render.status == "completed" and bool(render.file_path)
    if render.status != "completed":
        raise HTTPException(status_code=409, detail=f"Render is not ready (status: {render.status}).")

    listing_title: Optional[str] = None
    video_slot_synced = False
    has_existing_video: Optional[bool] = None
    operation: Optional[str] = None

    if req.listing_id:
        listing_q = await db.execute(
            select(Listing).where(
                Listing.id == req.listing_id,
                Listing.organization_id == org_id,
            )
        )
        listing = listing_q.scalar_one_or_none()
        if not listing:
            raise HTTPException(status_code=404, detail="Listing not found or not in your organization.")
        listing_title = listing.title
        # Current video slot from locally-synced ListingVideo (populated by sync).
        vid_q = await db.execute(select(ListingVideo).where(ListingVideo.listing_id == listing.id))
        existing = vid_q.scalars().first()
        # We can only claim the slot is "known" for a listing that has actually
        # been synced; treat presence/absence of a row as the synced state.
        video_slot_synced = True
        has_existing_video = existing is not None
        operation = "replace_video" if has_existing_video else "add_video"

    enabled = settings.ETSY_VIDEO_UPLOAD_ENABLED
    # replace needs BOTH the video flag and the destructive flag (it destroys
    # the current video) AND a re-uploadable backup, which does not exist yet.
    replace_supported = False
    allowed = False
    disabled_reason: Optional[str] = None

    if not enabled:
        disabled_reason = (
            "Etsy video upload is not enabled yet. No video is sent to Etsy from this screen. "
            "When enabled it will require explicit confirmation; generated videos are never auto-uploaded."
        )
    elif operation == "replace_video":
        disabled_reason = (
            "Replacing an existing listing video is not available yet — video restore has no re-uploadable "
            "backup, so a replace could not be safely undone. Only adding a video to a listing with no video "
            "will be supported first."
        )
    elif not render_ready:
        disabled_reason = "Render is not ready."
    elif operation == "add_video":
        allowed = True  # would be allowed once a real confirmed upload flow is wired

    if enabled and operation == "add_video":
        message = "Ready to add this video to the listing (explicit confirmation still required)."
    elif not req.listing_id:
        message = "Select a target listing to see whether the video can be added or would replace an existing one."
    else:
        message = disabled_reason or "Upload plan prepared."

    return EtsyUploadIntentResponse(
        enabled=enabled,
        allowed=allowed,
        disabled_reason=disabled_reason,
        render_id=render.id,
        render_ready=render_ready,
        listing_id=req.listing_id,
        listing_title=listing_title,
        video_slot_synced=video_slot_synced,
        has_existing_video=has_existing_video,
        operation=operation,
        replace_supported=replace_supported,
        no_auto_upload=True,
        message=message,
    )


# --- Background task ---

async def _run_render(
    render_id: str,
    org_id: str,
    image_urls: list[str],
    aspect_ratio: str,
    duration_seconds: float,
    branding: Optional[dict] = None,
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
        render_result = await render_slideshow_mp4(
            image_paths=local_paths,
            output_dir=output_dir,
            duration_seconds=duration_seconds,
            aspect_ratio=aspect_ratio,
            branding=branding,
        )

        output_path = render_result["output_path"]
        file_size_bytes = render_result["file_size_bytes"]
        width = render_result["width"]
        height = render_result["height"]

        is_etsy_ready, etsy_issues = check_etsy_ready(
            file_size_bytes=file_size_bytes,
            duration_seconds=duration_seconds,
            aspect_ratio=aspect_ratio,
            width=width,
            height=height,
        )

        async with AsyncSessionLocal() as db:
            result = await db.execute(select(VideoRender).where(VideoRender.id == render_id))
            render = result.scalar_one_or_none()
            if render:
                render.status = "completed"
                render.file_path = output_path
                render.file_size_bytes = file_size_bytes
                render.width = width
                render.height = height
                render.is_etsy_ready = is_etsy_ready
                render.etsy_issues_json = json.dumps(etsy_issues)
                render.completed_at = datetime.now(timezone.utc)
                if branding:
                    render.branding_json = json.dumps({
                        **branding,
                        "text_rendered": bool(render_result.get("branding_text_rendered")),
                        "logo_rendered": False,  # logo overlay not rendered server-side (SSRF)
                    })
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
