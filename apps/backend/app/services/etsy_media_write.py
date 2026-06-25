"""
Etsy API media write service — Sprint 11.

Supported in Sprint 11:
  Image fetch:   GET /v3/application/shops/{shop_id}/listings/{listing_id}/images
  Image upload:  POST /v3/application/shops/{shop_id}/listings/{listing_id}/images
                 (multipart/form-data — downloads image from URL first)
  Image delete:  DELETE /v3/application/shops/{shop_id}/listings/{listing_id}/images/{image_id}

Video stubs (Sprint 11):
  fetch, upload, delete — safe stubs; upload/delete raise EtsyMediaWriteError(not_implemented=True)
  Etsy video upload requires server-side direct file upload which is not available in Sprint 11.

Reorder stubs:
  Etsy has no atomic reorder endpoint. Reorder would require delete-all + re-upload.
  Not implemented: raises EtsyMediaWriteError(not_implemented=True).

Safety contract: callers must backup media before calling any write function.
"""
from __future__ import annotations

import logging
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

ETSY_API_BASE = "https://openapi.etsy.com/v3"

VALID_IMAGE_CONTENT_TYPES = {
    "image/jpeg", "image/png", "image/gif", "image/webp",
}
MAX_IMAGE_DOWNLOAD_BYTES = 20 * 1024 * 1024  # 20 MB


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


# ── Video write stubs ─────────────────────────────────────────────────────────

async def upload_etsy_listing_video(
    access_token: str,
    shop_etsy_id: str,
    listing_etsy_id: str,
    video_url: str,
) -> dict[str, Any]:
    """
    STUB — not implemented in Sprint 11.
    Etsy video upload requires direct server-side file upload (multipart).
    URL-based video upload is not supported by Etsy API.
    File upload storage (S3) is deferred to a future sprint.
    """
    raise EtsyMediaWriteError(
        "Video upload not supported in Sprint 11: Etsy requires direct file upload. "
        "URL-based video upload is not available. File upload storage (S3) is deferred.",
        status_code=501,
        not_implemented=True,
    )


async def delete_etsy_listing_video(
    access_token: str,
    shop_etsy_id: str,
    listing_etsy_id: str,
    video_id: str,
) -> None:
    """
    STUB — not implemented in Sprint 11.
    Etsy video delete behavior is uncertain and untested.
    Deferred to a future sprint after endpoint behavior is confirmed.
    """
    raise EtsyMediaWriteError(
        "Video delete not supported in Sprint 11: endpoint behavior unconfirmed. Deferred.",
        status_code=501,
        not_implemented=True,
    )
