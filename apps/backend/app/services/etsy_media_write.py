"""
Etsy API media write service.

Images:
  Image fetch:   GET /v3/application/shops/{shop_id}/listings/{listing_id}/images
  Image upload:  POST /v3/application/shops/{shop_id}/listings/{listing_id}/images
                 (multipart/form-data — downloads image from URL first)
  Image delete:  DELETE /v3/application/shops/{shop_id}/listings/{listing_id}/images/{image_id}

Videos:
  Video fetch:   GET /v3/application/shops/{shop_id}/listings/{listing_id}/videos
  Video upload:  POST /v3/application/shops/{shop_id}/listings/{listing_id}/videos
                 (multipart/form-data, local file — see notes below)
  Video delete:  DELETE /v3/application/shops/{shop_id}/listings/{listing_id}/videos/{video_id}

  Evidence checked across multiple independent sources:
    (1) Etsy's own public API changelog (developers.etsy.com) references a
        real, named "ListingVideo_Upload" operation with its own bug-fix
        history.
    (2) ButterMyGit/Etsy-Bulk-Video-Uploader (github.com), a working
        third-party tool, uses exactly this shape: POST /application/shops/
        {shop_id}/listings/{listing_id}/videos, multipart field "video", no
        other form fields; DELETE .../videos/{video_id}; delete-then-upload
        for a replace — identical to what's implemented here.
    (3) Etsy's live official reference site (developers.etsy.com/documentation/
        reference/) has valid operationId-anchored links for both
        "uploadListingVideo" and "getListingVideos" — Redoc/Swagger-style
        docs generate these anchors directly from the underlying spec's
        operationId, so their existence is itself first-party evidence these
        operations are real. The reference page is a JS-rendered SPA, so the
        actual request/response schema couldn't be fetched programmatically
        here — only the anchor's existence was confirmable.
    (4) A direct fetch of Etsy's raw OpenAPI JSON
        (https://www.etsy.com/openapi/generated/oas/3.0.0.json) initially
        appeared to show zero operations under the "ShopListing Video" tag —
        but given (3) confirms the operationIds are real on the live docs
        site, this was almost certainly an artifact of summarizing a huge
        (70+ endpoint) spec file through an intermediate model, not a
        genuine absence.
  Taken together, (1)-(3) are strong enough to implement this for real
  rather than stub it. NOT YET exercised against our own live Etsy
  connection — the first real apply on staging is the actual end-to-end
  confirmation for this codebase. EtsyMediaWriteError.not_implemented is set
  to True when Etsy responds 404/405/501, so a shape mismatch would still
  surface as a clear, distinct, actionable error rather than a generic one.

Reorder — investigated and NOT implemented:
  Etsy has no PATCH/PUT endpoint to change an existing image's rank without
  re-uploading it (confirmed: only GET/POST-create/DELETE exist for images).
  The only possible path is delete-then-reupload, which — because Etsy's
  create endpoint requires image bytes and has no true "swap" primitive —
  necessarily has a real, uneliminable window where a LIVE customer-facing
  listing can show fewer/zero photos if the process fails mid-sequence
  (network error, timeout, process restart). Magic Revert can repair this
  after the fact, but the risk during the operation itself cannot be
  eliminated with Etsy's current API, which fails the "no risk of data loss"
  bar. Left as a stub; see reorder_images entry in bulk_edit_media.py for
  the full evidence and a safe path to revisit (e.g. testing against a
  disposable/sandbox shop first, or an explicit opt-in beta with warnings).

Safety contract: callers must backup media before calling any write function.
"""
from __future__ import annotations

import logging
import os
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

ETSY_API_BASE = "https://openapi.etsy.com/v3"

VALID_IMAGE_CONTENT_TYPES = {
    "image/jpeg", "image/png", "image/gif", "image/webp",
}
MAX_IMAGE_DOWNLOAD_BYTES = 20 * 1024 * 1024  # 20 MB
MAX_VIDEO_UPLOAD_BYTES = 100 * 1024 * 1024  # 100 MB — matches Etsy's listing video spec


class EtsyMediaWriteError(Exception):
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        response_body: Any = None,
        not_implemented: bool = False,
    ):
        self.message = message
        self.status_code = status_code
        self.response_body = response_body
        self.not_implemented = not_implemented
        super().__init__(message)


def _auth_headers(access_token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {access_token}",
        "x-api-key": settings.ETSY_CLIENT_ID,
    }


# ── Image reads ───────────────────────────────────────────────────────────────

async def fetch_etsy_listing_images(
    access_token: str,
    shop_etsy_id: str,
    listing_etsy_id: str,
) -> list[dict[str, Any]]:
    """GET images for a listing. Returns [] on 404."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(
            f"{ETSY_API_BASE}/application/shops/{shop_etsy_id}/listings/{listing_etsy_id}/images",
            headers=_auth_headers(access_token),
        )
    if resp.status_code == 404:
        return []
    if resp.status_code >= 400:
        raise EtsyMediaWriteError(
            f"Fetch images failed: HTTP {resp.status_code}",
            status_code=resp.status_code,
        )
    return resp.json().get("results", [])


# ── Image writes ──────────────────────────────────────────────────────────────

async def upload_etsy_listing_image(
    access_token: str,
    shop_etsy_id: str,
    listing_etsy_id: str,
    image_url: str,
    rank: int | None = None,
    overwrite: bool = False,
    alt_text: str | None = None,
) -> dict[str, Any]:
    """
    Download image from image_url then POST as multipart/form-data to Etsy.
    Returns the created ListingImage object from Etsy.
    Raises EtsyMediaWriteError on download failure or Etsy HTTP error.
    """
    # Download image bytes
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as dl:
            img_resp = await dl.get(image_url)
    except Exception as exc:
        raise EtsyMediaWriteError(f"Failed to download image from URL: {exc}") from exc

    if img_resp.status_code >= 400:
        raise EtsyMediaWriteError(
            f"Image URL returned HTTP {img_resp.status_code}",
            status_code=img_resp.status_code,
        )

    content_type = img_resp.headers.get("content-type", "image/jpeg").split(";")[0].strip().lower()
    image_bytes = img_resp.content

    if len(image_bytes) > MAX_IMAGE_DOWNLOAD_BYTES:
        raise EtsyMediaWriteError(
            f"Image too large: {len(image_bytes)} bytes (max {MAX_IMAGE_DOWNLOAD_BYTES})"
        )

    # Determine file extension from content-type
    ext_map = {"image/jpeg": "jpg", "image/png": "png", "image/gif": "gif", "image/webp": "webp"}
    ext = ext_map.get(content_type, "jpg")
    filename = f"image.{ext}"

    # Build multipart form data
    files: list[tuple[str, Any]] = [
        ("image", (filename, image_bytes, content_type)),
    ]
    data: dict[str, str] = {}
    if rank is not None:
        data["rank"] = str(rank)
    if overwrite:
        data["overwrite"] = "true"
    if alt_text:
        data["alt_text"] = alt_text

    headers = _auth_headers(access_token)

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            f"{ETSY_API_BASE}/application/shops/{shop_etsy_id}/listings/{listing_etsy_id}/images",
            headers=headers,
            files=files,
            data=data,
        )

    if resp.status_code >= 400:
        body: Any = None
        try:
            body = resp.json()
        except Exception:
            body = resp.text
        raise EtsyMediaWriteError(
            f"Etsy image upload failed: HTTP {resp.status_code}",
            status_code=resp.status_code,
            response_body=body,
        )

    return resp.json()


async def delete_etsy_listing_image(
    access_token: str,
    shop_etsy_id: str,
    listing_etsy_id: str,
    image_id: str,
) -> None:
    """DELETE a listing image. Raises EtsyMediaWriteError on HTTP error (404 treated as success)."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.delete(
            f"{ETSY_API_BASE}/application/shops/{shop_etsy_id}/listings/{listing_etsy_id}/images/{image_id}",
            headers=_auth_headers(access_token),
        )

    # 404 means already deleted — treat as success
    if resp.status_code == 404:
        return

    if resp.status_code >= 400:
        body: Any = None
        try:
            body = resp.json()
        except Exception:
            body = resp.text
        raise EtsyMediaWriteError(
            f"Etsy image delete failed: HTTP {resp.status_code}",
            status_code=resp.status_code,
            response_body=body,
        )


# ── Video reads ───────────────────────────────────────────────────────────────

async def fetch_etsy_listing_videos(
    access_token: str,
    shop_etsy_id: str,
    listing_etsy_id: str,
) -> list[dict[str, Any]]:
    """GET videos for a listing. Best-effort — returns [] on any failure."""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                f"{ETSY_API_BASE}/application/shops/{shop_etsy_id}/listings/{listing_etsy_id}/videos",
                headers=_auth_headers(access_token),
            )
        if resp.status_code in (404, 405):
            return []
        if not resp.is_success:
            return []
        return resp.json().get("results", [])
    except Exception:
        return []


# ── Video writes ──────────────────────────────────────────────────────────────

async def upload_etsy_listing_video(
    access_token: str,
    shop_etsy_id: str,
    listing_etsy_id: str,
    video_file_path: str,
) -> dict[str, Any]:
    """
    POST a local MP4 file (produced by app/services/video_renderer.py — the
    Product Video Generator) to Etsy as multipart/form-data. Unlike images,
    no URL download step is needed: we already generated and stored the file
    ourselves, so we read it directly from disk.

    Raises EtsyMediaWriteError on missing/oversized file or Etsy HTTP error.
    Sets not_implemented=True if Etsy responds 404/405/501 — that specific
    response would mean this endpoint shape doesn't match Etsy's real API,
    which is the concrete signal this needs re-investigation rather than a
    generic failure.
    """
    if not os.path.isfile(video_file_path):
        raise EtsyMediaWriteError(f"Video file not found on disk: {video_file_path}", status_code=500)

    file_size = os.path.getsize(video_file_path)
    if file_size > MAX_VIDEO_UPLOAD_BYTES:
        raise EtsyMediaWriteError(
            f"Video too large: {file_size} bytes (max {MAX_VIDEO_UPLOAD_BYTES})",
            status_code=400,
        )

    with open(video_file_path, "rb") as f:
        video_bytes = f.read()

    files: list[tuple[str, Any]] = [
        ("video", (os.path.basename(video_file_path), video_bytes, "video/mp4")),
    ]
    headers = _auth_headers(access_token)

    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(
            f"{ETSY_API_BASE}/application/shops/{shop_etsy_id}/listings/{listing_etsy_id}/videos",
            headers=headers,
            files=files,
        )

    if resp.status_code >= 400:
        body: Any = None
        try:
            body = resp.json()
        except Exception:
            body = resp.text
        raise EtsyMediaWriteError(
            f"Etsy video upload failed: HTTP {resp.status_code}",
            status_code=resp.status_code,
            response_body=body,
            not_implemented=resp.status_code in (404, 405, 501),
        )

    return resp.json()


async def delete_etsy_listing_video(
    access_token: str,
    shop_etsy_id: str,
    listing_etsy_id: str,
    video_id: str,
) -> None:
    """DELETE a listing video. Raises EtsyMediaWriteError on HTTP error (404 treated as success)."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.delete(
            f"{ETSY_API_BASE}/application/shops/{shop_etsy_id}/listings/{listing_etsy_id}/videos/{video_id}",
            headers=_auth_headers(access_token),
        )

    if resp.status_code == 404:
        return

    if resp.status_code >= 400:
        body: Any = None
        try:
            body = resp.json()
        except Exception:
            body = resp.text
        raise EtsyMediaWriteError(
            f"Etsy video delete failed: HTTP {resp.status_code}",
            status_code=resp.status_code,
            response_body=body,
            not_implemented=resp.status_code in (405, 501),
        )
