"""
Bulk Edit Media Service.

Orchestrates safe media writes to Etsy listings:
  - add_image: download from URL, upload to Etsy, update local ListingImage rows
  - replace_image: delete existing at rank, upload new, update local rows
  - delete_image: delete from Etsy by rank or image_id, remove local row
  - add_video: upload a completed, Etsy-ready VideoRender (local MP4 file —
    either a Product Video Generator render or a directly uploaded file) to
    a listing's video slot. Etsy listings support exactly one video, so this
    fails clearly if the listing already has one — use replace_video instead.
  - replace_video: upload a completed, Etsy-ready VideoRender (local MP4 file)
    to Etsy, replacing any existing listing video; updates local ListingVideo rows
  - delete_video: delete the listing's video from Etsy, remove local row
  - reorder_images: STUB — investigated, not implemented. See the entry in
    _STUB_REASONS below for the full evidence — Etsy has no atomic reorder
    endpoint, and the only workaround (delete-then-reupload) has a real,
    uneliminable data-loss window on a LIVE customer-facing listing.

Safety contract:
  1. listing_ids must belong to organization
  2. operation_type must be valid
  3. Backup snapshot created per listing BEFORE any Etsy media write
  4. Local ListingImage/ListingVideo rows updated ONLY after Etsy write succeeds
  5. Audit log written on job start and job finish
  6. Per-listing BulkEditMediaResult row created for every listing
  7. Partial failure supported — each listing gets its own result row
  8. Backup snapshots never deleted
"""
import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select, func, delete as sa_delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.audit_log import AuditLog
from app.models.bulk_edit_media_job import BulkEditMediaJob
from app.models.bulk_edit_media_result import BulkEditMediaResult
from app.models.etsy_shop import EtsyShop
from app.models.listing import Listing
from app.models.listing_image import ListingImage
from app.models.listing_video import ListingVideo
from app.models.listing_media_backup_snapshot import ListingMediaBackupSnapshot
from app.models.video_render import VideoRender
from app.services.etsy_sync import get_valid_etsy_access_token, upsert_listing_images
from app.services.etsy_media_write import (
    fetch_etsy_listing_images,
    fetch_etsy_listing_videos,
    upload_etsy_listing_image,
    delete_etsy_listing_image,
    upload_etsy_listing_video,
    delete_etsy_listing_video,
    EtsyMediaWriteError,
)

logger = logging.getLogger(__name__)

VALID_OPERATION_TYPES = {
    "add_image",
    "replace_image",
    "delete_image",
    "reorder_images",
    "add_video",
    "replace_video",
    "delete_video",
}

# Operations implemented with real Etsy writes
IMPLEMENTED_OPERATIONS = {
    "add_image", "replace_image", "delete_image", "add_video", "replace_video", "delete_video",
}

# Stubs with clear reason
_STUB_REASONS = {
    "reorder_images": (
        "Image reorder is not implemented: investigated against Etsy's API and confirmed there is "
        "no endpoint to change an existing image's rank without re-uploading it (only GET/POST-create/"
        "DELETE exist for listing images). The only possible workaround — delete then re-upload in the "
        "new order — has a real window where a live, customer-facing listing can show fewer or zero "
        "photos if the process fails partway (network error, timeout, restart). Magic Revert can repair "
        "this after the fact but the risk during the operation itself cannot be eliminated with Etsy's "
        "current API, so this was not implemented rather than accepting that risk silently. Revisit only "
        "with either sandbox/disposable-shop testing first, or an explicit opt-in beta with a clear warning."
    ),
}


async def _write_audit_log(
    db: AsyncSession,
    org_id: str,
    user_id: str | None,
    event_type: str,
    entity_type: str | None = None,
    entity_id: str | None = None,
    message: str | None = None,
    extra_data: Any = None,
) -> None:
    log = AuditLog(
        organization_id=org_id,
        user_id=user_id,
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        message=message,
        extra_data=extra_data,
    )
    db.add(log)
    await db.flush()


async def create_media_job(
    db: AsyncSession,
    organization_id: str,
    user_id: str,
    operation_type: str,
    listing_ids: list[str],
    payload: dict[str, Any],
) -> BulkEditMediaJob:
    """
    Validate and create a BulkEditMediaJob.
    Raises HTTPException on validation failure.
    """
    if not listing_ids:
        raise HTTPException(status_code=400, detail="listing_ids must not be empty.")

    if operation_type not in VALID_OPERATION_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid operation_type '{operation_type}'. Must be one of: {', '.join(sorted(VALID_OPERATION_TYPES))}.",
        )

    # Validate all listing_ids belong to org
    listings_q = await db.execute(
        select(Listing).where(
            Listing.id.in_(listing_ids),
            Listing.organization_id == organization_id,
        )
    )
    found_listings = list(listings_q.scalars().all())
    found_ids = {l.id for l in found_listings}
    missing = [lid for lid in listing_ids if lid not in found_ids]
    if missing:
        raise HTTPException(
            status_code=404,
            detail=f"Listing(s) not found or do not belong to your organization: {missing[:5]}",
        )

    job = BulkEditMediaJob(
        organization_id=organization_id,
        created_by_user_id=user_id,
        operation_type=operation_type,
        operation_payload=payload,
        listing_ids=listing_ids,
        status="pending",
        total_items=len(listing_ids),
        success_count=0,
        failure_count=0,
        skipped_count=0,
    )
    db.add(job)
    await db.flush()
    await db.commit()
    await db.refresh(job)
    return job


async def apply_media_job(
    db: AsyncSession,
    organization_id: str,
    user_id: str,
    media_job_id: str,
) -> BulkEditMediaJob:
    """
    Execute a media job inline (synchronous MVP).
    Returns the finished BulkEditMediaJob.
    """
    if not settings.is_etsy_configured():
        raise HTTPException(
            status_code=503,
            detail="Etsy integration not configured. Set ETSY_CLIENT_ID.",
        )

    job_q = await db.execute(
        select(BulkEditMediaJob).where(
            BulkEditMediaJob.id == media_job_id,
            BulkEditMediaJob.organization_id == organization_id,
        )
    )
    job = job_q.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Media job not found.")

    if job.status not in ("pending",):
        raise HTTPException(
            status_code=400,
            detail=f"Media job cannot be applied: current status is '{job.status}'. Only 'pending' jobs can be applied.",
        )

    listing_ids: list[str] = job.listing_ids or []
    operation_type: str = job.operation_type
    payload: dict[str, Any] = job.operation_payload or {}

    # Mark running
    job.status = "running"
    job.started_at = datetime.now(timezone.utc)
    db.add(job)
    await db.flush()

    await _write_audit_log(
        db,
        org_id=organization_id,
        user_id=user_id,
        event_type="bulk_edit_media_job_started",
        entity_type="bulk_edit_media_job",
        entity_id=media_job_id,
        message=f"Media job {media_job_id} started. operation={operation_type}, listings={len(listing_ids)}.",
        extra_data={"media_job_id": media_job_id, "operation_type": operation_type, "total": len(listing_ids)},
    )
    await db.commit()

    # Load listings + shops + tokens
    listings_q = await db.execute(
        select(Listing).where(
            Listing.id.in_(listing_ids),
            Listing.organization_id == organization_id,
        )
    )
    listings_map: dict[str, Listing] = {l.id: l for l in listings_q.scalars().all()}

    shop_ids = list({l.etsy_shop_id for l in listings_map.values()})
    shops_q = await db.execute(select(EtsyShop).where(EtsyShop.id.in_(shop_ids)))
    shops_map: dict[str, EtsyShop] = {s.id: s for s in shops_q.scalars().all()}

    access_tokens: dict[str, str] = {}
    for shop_id, shop in shops_map.items():
        try:
            token = await get_valid_etsy_access_token(shop, db)
            access_tokens[shop_id] = token
        except Exception as e:
            logger.warning("Could not get token for shop %s: %s", shop_id, e)

    success_count = 0
    failure_count = 0
    skipped_count = 0

    for listing_id in listing_ids:
        now = datetime.now(timezone.utc)
        listing = listings_map.get(listing_id)

        if not listing:
            skipped_count += 1
            mr = BulkEditMediaResult(
                organization_id=organization_id,
                media_job_id=media_job_id,
                bulk_edit_session_id=job.bulk_edit_session_id,
                listing_id=listing_id,
                etsy_listing_id=listing_id,
                operation_type=operation_type,
                status="skipped",
                error_message="Listing not found in database.",
                attempted_at=now,
                completed_at=now,
            )
            db.add(mr)
            await db.flush()
            continue

        access_token = access_tokens.get(listing.etsy_shop_id)
        if not access_token:
            skipped_count += 1
            mr = BulkEditMediaResult(
                organization_id=organization_id,
                media_job_id=media_job_id,
                bulk_edit_session_id=job.bulk_edit_session_id,
                listing_id=listing.id,
                etsy_listing_id=listing.etsy_listing_id,
                operation_type=operation_type,
                status="skipped",
                error_message="No valid Etsy access token for this shop.",
                attempted_at=now,
                completed_at=now,
            )
            db.add(mr)
            await db.flush()
            continue

        shop = shops_map.get(listing.etsy_shop_id)
        if not shop:
            skipped_count += 1
            mr = BulkEditMediaResult(
                organization_id=organization_id,
                media_job_id=media_job_id,
                bulk_edit_session_id=job.bulk_edit_session_id,
                listing_id=listing.id,
                etsy_listing_id=listing.etsy_listing_id,
                operation_type=operation_type,
                status="skipped",
                error_message="Shop not found.",
                attempted_at=now,
                completed_at=now,
            )
            db.add(mr)
            await db.flush()
            continue

        # Handle stub operations
        if operation_type not in IMPLEMENTED_OPERATIONS:
            skipped_count += 1
            mr = BulkEditMediaResult(
                organization_id=organization_id,
                media_job_id=media_job_id,
                bulk_edit_session_id=job.bulk_edit_session_id,
                listing_id=listing.id,
                etsy_listing_id=listing.etsy_listing_id,
                operation_type=operation_type,
                status="skipped",
                error_message=_STUB_REASONS.get(operation_type, "Operation not implemented."),
                attempted_at=now,
                completed_at=now,
            )
            db.add(mr)
            await db.flush()
            continue

        # Create media backup snapshot BEFORE write
        snapshot = await _create_media_backup_snapshot(
            db=db,
            organization_id=organization_id,
            user_id=user_id,
            media_job_id=media_job_id,
            bulk_edit_session_id=job.bulk_edit_session_id,
            listing=listing,
            shop=shop,
        )

        # Load current images for before_media
        images_q = await db.execute(
            select(ListingImage).where(ListingImage.listing_id == listing.id).order_by(ListingImage.rank)
        )
        current_images = list(images_q.scalars().all())
        before_media = [_image_to_dict(img) for img in current_images]

        mr = BulkEditMediaResult(
            organization_id=organization_id,
            media_job_id=media_job_id,
            bulk_edit_session_id=job.bulk_edit_session_id,
            listing_id=listing.id,
            etsy_listing_id=listing.etsy_listing_id,
            operation_type=operation_type,
            status="pending",
            before_media=before_media,
            request_payload={"operation_type": operation_type, **payload},
            attempted_at=now,
        )
        db.add(mr)
        await db.flush()

        # Execute the operation
        try:
            after_media, response = await _apply_one_operation(
                operation_type=operation_type,
                access_token=access_token,
                shop=shop,
                listing=listing,
                payload=payload,
                db=db,
            )
            mr.status = "success"
            mr.after_media = after_media
            mr.response_payload = response
            mr.completed_at = datetime.now(timezone.utc)
            success_count += 1
        except EtsyMediaWriteError as e:
            mr.status = "failed"
            mr.error_message = e.message
            mr.response_payload = e.response_body
            mr.completed_at = datetime.now(timezone.utc)
            failure_count += 1
            logger.warning(
                "Media op %s failed for listing %s: %s",
                operation_type, listing.etsy_listing_id, e.message,
            )
        except Exception as e:
            mr.status = "failed"
            mr.error_message = str(e)
            mr.completed_at = datetime.now(timezone.utc)
            failure_count += 1
            logger.exception("Unexpected error on media op %s for %s", operation_type, listing.etsy_listing_id)

        await db.flush()

    # Finalize
    job.success_count = success_count
    job.failure_count = failure_count
    job.skipped_count = skipped_count
    job.finished_at = datetime.now(timezone.utc)
    job.status = (
        "completed" if failure_count == 0 and skipped_count == 0
        else "completed_with_errors" if success_count > 0
        else "failed"
    )
    db.add(job)

    await _write_audit_log(
        db,
        org_id=organization_id,
        user_id=user_id,
        event_type="bulk_edit_media_job_finished",
        entity_type="bulk_edit_media_job",
        entity_id=media_job_id,
        message=(
            f"Media job {media_job_id} finished. "
            f"success={success_count}, failure={failure_count}, skipped={skipped_count}."
        ),
        extra_data={
            "media_job_id": media_job_id,
            "operation_type": operation_type,
            "success_count": success_count,
            "failure_count": failure_count,
            "skipped_count": skipped_count,
            "status": job.status,
        },
    )

    await db.commit()
    await db.refresh(job)
    return job


async def _load_video_render_or_raise(
    db: AsyncSession,
    video_render_id: str,
    organization_id: str,
) -> VideoRender:
    """Shared lookup/validation for add_video and replace_video: the render
    must belong to the org, be a completed local file, and pass Etsy's specs."""
    render_q = await db.execute(
        select(VideoRender).where(
            VideoRender.id == video_render_id,
            VideoRender.organization_id == organization_id,
        )
    )
    render = render_q.scalar_one_or_none()
    if not render:
        raise EtsyMediaWriteError(
            "Video not found or does not belong to your organization.", status_code=404
        )
    if render.status != "completed" or not render.file_path:
        raise EtsyMediaWriteError(
            f"Video is not completed (status={render.status}).", status_code=400
        )
    if render.is_etsy_ready is False:
        issues = render.get_etsy_issues()
        raise EtsyMediaWriteError(
            f"Video does not meet Etsy's video specs: {'; '.join(issues) or 'unknown issue'}",
            status_code=400,
        )
    return render


async def _apply_one_operation(
    operation_type: str,
    access_token: str,
    shop: "EtsyShop",
    listing: "Listing",
    payload: dict[str, Any],
    db: AsyncSession,
) -> tuple[list[dict], Any]:
    """
    Execute one media operation for one listing.
    Returns (after_media_list, etsy_response).
    Raises EtsyMediaWriteError on failure.
    """
    shop_etsy_id = shop.etsy_shop_id
    listing_etsy_id = listing.etsy_listing_id

    if operation_type == "add_image":
        image_url = payload.get("image_url")
        if not image_url:
            raise EtsyMediaWriteError("add_image requires 'image_url' in payload.", status_code=400)
        rank = payload.get("rank")
        alt_text = payload.get("alt_text")
        overwrite = bool(payload.get("overwrite", False))

        etsy_response = await upload_etsy_listing_image(
            access_token=access_token,
            shop_etsy_id=shop_etsy_id,
            listing_etsy_id=listing_etsy_id,
            image_url=image_url,
            rank=rank,
            overwrite=overwrite,
            alt_text=alt_text,
        )

        # Update local images with the new image from Etsy response
        await upsert_listing_images(db, listing, [etsy_response])
        await db.flush()

        # Return updated image list
        updated_q = await db.execute(
            select(ListingImage).where(ListingImage.listing_id == listing.id).order_by(ListingImage.rank)
        )
        after_images = [_image_to_dict(img) for img in updated_q.scalars().all()]
        return after_images, etsy_response

    elif operation_type == "replace_image":
        target_rank = payload.get("target_rank")
        image_url = payload.get("image_url")
        if not image_url:
            raise EtsyMediaWriteError("replace_image requires 'image_url' in payload.", status_code=400)

        # Find existing image at target_rank
        existing_q = await db.execute(
            select(ListingImage).where(
                ListingImage.listing_id == listing.id,
                ListingImage.rank == target_rank,
            )
        )
        existing_image = existing_q.scalar_one_or_none()

        # Delete existing if found
        if existing_image and existing_image.etsy_image_id:
            await delete_etsy_listing_image(
                access_token=access_token,
                shop_etsy_id=shop_etsy_id,
                listing_etsy_id=listing_etsy_id,
                image_id=existing_image.etsy_image_id,
            )
            # Remove local row
            await db.delete(existing_image)
            await db.flush()

        # Upload new image
        alt_text = payload.get("alt_text")
        etsy_response = await upload_etsy_listing_image(
            access_token=access_token,
            shop_etsy_id=shop_etsy_id,
            listing_etsy_id=listing_etsy_id,
            image_url=image_url,
            rank=target_rank,
            overwrite=True,
            alt_text=alt_text,
        )

        await upsert_listing_images(db, listing, [etsy_response])
        await db.flush()

        updated_q = await db.execute(
            select(ListingImage).where(ListingImage.listing_id == listing.id).order_by(ListingImage.rank)
        )
        after_images = [_image_to_dict(img) for img in updated_q.scalars().all()]
        return after_images, etsy_response

    elif operation_type == "delete_image":
        target_rank = payload.get("target_rank")
        image_id = payload.get("image_id")

        # Locate image by rank or image_id
        target_image: ListingImage | None = None
        if image_id:
            q = await db.execute(
                select(ListingImage).where(
                    ListingImage.listing_id == listing.id,
                    ListingImage.etsy_image_id == str(image_id),
                )
            )
            target_image = q.scalar_one_or_none()
        elif target_rank is not None:
            q = await db.execute(
                select(ListingImage).where(
                    ListingImage.listing_id == listing.id,
                    ListingImage.rank == target_rank,
                )
            )
            target_image = q.scalar_one_or_none()

        if not target_image:
            raise EtsyMediaWriteError(
                f"No image found at rank={target_rank} or image_id={image_id}. Listing has no matching image.",
                status_code=404,
            )

        etsy_image_id = target_image.etsy_image_id
        if not etsy_image_id:
            raise EtsyMediaWriteError(
                "Target image has no etsy_image_id — cannot delete from Etsy.",
                status_code=400,
            )

        await delete_etsy_listing_image(
            access_token=access_token,
            shop_etsy_id=shop_etsy_id,
            listing_etsy_id=listing_etsy_id,
            image_id=etsy_image_id,
        )

        # Remove local row
        await db.delete(target_image)
        await db.flush()

        updated_q = await db.execute(
            select(ListingImage).where(ListingImage.listing_id == listing.id).order_by(ListingImage.rank)
        )
        after_images = [_image_to_dict(img) for img in updated_q.scalars().all()]
        return after_images, {"deleted_image_id": etsy_image_id}

    elif operation_type == "add_video":
        video_render_id = payload.get("video_render_id") or payload.get("uploaded_video_id")
        if not video_render_id:
            raise EtsyMediaWriteError(
                "add_video requires 'video_render_id' or 'uploaded_video_id' in payload.", status_code=400
            )

        render = await _load_video_render_or_raise(db, video_render_id, listing.organization_id)

        # Etsy listings support exactly one video — add_video must not silently
        # replace it. Fail clearly and point the user at replace_video instead.
        existing_q = await db.execute(select(ListingVideo).where(ListingVideo.listing_id == listing.id))
        existing_video = existing_q.scalar_one_or_none()
        if existing_video:
            raise EtsyMediaWriteError(
                "This listing already has a video. Use Replace Video instead.", status_code=400
            )

        etsy_response = await upload_etsy_listing_video(
            access_token=access_token,
            shop_etsy_id=shop_etsy_id,
            listing_etsy_id=listing_etsy_id,
            video_file_path=render.file_path,
        )

        new_video = ListingVideo(
            listing_id=listing.id,
            etsy_video_id=str(etsy_response.get("video_id") or etsy_response.get("listing_video_id") or ""),
            video_url=etsy_response.get("video_url"),
            thumbnail_url=etsy_response.get("thumbnail_url"),
            rank=1,
            raw_data=etsy_response,
        )
        db.add(new_video)
        await db.flush()

        updated_q = await db.execute(select(ListingVideo).where(ListingVideo.listing_id == listing.id))
        after_videos = [_video_to_dict(v) for v in updated_q.scalars().all()]
        return after_videos, etsy_response

    elif operation_type == "replace_video":
        video_render_id = payload.get("video_render_id")
        if not video_render_id:
            raise EtsyMediaWriteError("replace_video requires 'video_render_id' in payload.", status_code=400)

        render = await _load_video_render_or_raise(db, video_render_id, listing.organization_id)

        # Etsy listings support one video — replace any existing one first.
        existing_q = await db.execute(select(ListingVideo).where(ListingVideo.listing_id == listing.id))
        existing_video = existing_q.scalar_one_or_none()
        if existing_video and existing_video.etsy_video_id:
            await delete_etsy_listing_video(
                access_token=access_token,
                shop_etsy_id=shop_etsy_id,
                listing_etsy_id=listing_etsy_id,
                video_id=existing_video.etsy_video_id,
            )
            await db.delete(existing_video)
            await db.flush()

        etsy_response = await upload_etsy_listing_video(
            access_token=access_token,
            shop_etsy_id=shop_etsy_id,
            listing_etsy_id=listing_etsy_id,
            video_file_path=render.file_path,
        )

        new_video = ListingVideo(
            listing_id=listing.id,
            etsy_video_id=str(etsy_response.get("video_id") or etsy_response.get("listing_video_id") or ""),
            video_url=etsy_response.get("video_url"),
            thumbnail_url=etsy_response.get("thumbnail_url"),
            rank=1,
            raw_data=etsy_response,
        )
        db.add(new_video)
        await db.flush()

        updated_q = await db.execute(select(ListingVideo).where(ListingVideo.listing_id == listing.id))
        after_videos = [_video_to_dict(v) for v in updated_q.scalars().all()]
        return after_videos, etsy_response

    elif operation_type == "delete_video":
        video_id = payload.get("video_id")

        target_video: ListingVideo | None = None
        if video_id:
            q = await db.execute(
                select(ListingVideo).where(
                    ListingVideo.listing_id == listing.id,
                    ListingVideo.etsy_video_id == str(video_id),
                )
            )
            target_video = q.scalar_one_or_none()
        else:
            # Etsy listings support one video — no id given means "the" video.
            q = await db.execute(select(ListingVideo).where(ListingVideo.listing_id == listing.id))
            target_video = q.scalar_one_or_none()

        if not target_video:
            raise EtsyMediaWriteError(
                f"No video found for this listing (video_id={video_id}).", status_code=404
            )

        etsy_video_id = target_video.etsy_video_id
        if not etsy_video_id:
            raise EtsyMediaWriteError(
                "Target video has no etsy_video_id — cannot delete from Etsy.", status_code=400
            )

        await delete_etsy_listing_video(
            access_token=access_token,
            shop_etsy_id=shop_etsy_id,
            listing_etsy_id=listing_etsy_id,
            video_id=etsy_video_id,
        )

        await db.delete(target_video)
        await db.flush()

        return [], {"deleted_video_id": etsy_video_id}

    raise EtsyMediaWriteError(f"Unknown operation: {operation_type}", status_code=400)


async def _create_media_backup_snapshot(
    db: AsyncSession,
    organization_id: str,
    user_id: str,
    media_job_id: str,
    bulk_edit_session_id: str | None,
    listing: "Listing",
    shop: "EtsyShop",
) -> ListingMediaBackupSnapshot:
    """Snapshot current listing images and videos before any media write."""
    images_q = await db.execute(
        select(ListingImage).where(ListingImage.listing_id == listing.id).order_by(ListingImage.rank)
    )
    images_snapshot = [_image_to_dict(img) for img in images_q.scalars().all()]

    videos_q = await db.execute(select(ListingVideo).where(ListingVideo.listing_id == listing.id))
    videos_snapshot = [_video_to_dict(v) for v in videos_q.scalars().all()]

    snap = ListingMediaBackupSnapshot(
        organization_id=organization_id,
        media_job_id=media_job_id,
        bulk_edit_session_id=bulk_edit_session_id,
        listing_id=listing.id,
        etsy_shop_id=listing.etsy_shop_id,
        etsy_listing_id=listing.etsy_listing_id,
        snapshot_type="pre_media_write",
        images_snapshot=images_snapshot,
        videos_snapshot=videos_snapshot or None,
        raw_snapshot=None,
        created_by_user_id=user_id,
    )
    db.add(snap)
    await db.flush()
    return snap


def _image_to_dict(img: "ListingImage") -> dict[str, Any]:
    return {
        "id": img.id,
        "etsy_image_id": img.etsy_image_id,
        "rank": img.rank,
        "url_fullxfull": img.url_fullxfull,
        "url_570xN": img.url_570xN,
        "alt_text": img.alt_text,
    }


def _video_to_dict(video: "ListingVideo") -> dict[str, Any]:
    return {
        "id": video.id,
        "etsy_video_id": video.etsy_video_id,
        "video_url": video.video_url,
        "thumbnail_url": video.thumbnail_url,
        "rank": video.rank,
    }


# ── Query helpers ─────────────────────────────────────────────────────────────

async def get_media_job(
    db: AsyncSession,
    organization_id: str,
    media_job_id: str,
) -> BulkEditMediaJob:
    q = await db.execute(
        select(BulkEditMediaJob).where(
            BulkEditMediaJob.id == media_job_id,
            BulkEditMediaJob.organization_id == organization_id,
        )
    )
    job = q.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Media job not found.")
    return job


async def list_media_jobs(
    db: AsyncSession,
    organization_id: str,
) -> list[BulkEditMediaJob]:
    q = await db.execute(
        select(BulkEditMediaJob).where(
            BulkEditMediaJob.organization_id == organization_id,
        ).order_by(BulkEditMediaJob.created_at.desc())
    )
    return list(q.scalars().all())


async def get_media_results(
    db: AsyncSession,
    organization_id: str,
    media_job_id: str,
    page: int = 1,
    per_page: int = 50,
) -> dict:
    await get_media_job(db, organization_id, media_job_id)

    base_q = select(BulkEditMediaResult).where(
        BulkEditMediaResult.media_job_id == media_job_id,
        BulkEditMediaResult.organization_id == organization_id,
    )
    count_q = await db.execute(select(func.count()).select_from(base_q.subquery()))
    total = count_q.scalar_one()

    paged_q = base_q.order_by(BulkEditMediaResult.created_at.asc()).offset((page - 1) * per_page).limit(per_page)
    result_q = await db.execute(paged_q)
    items = list(result_q.scalars().all())

    return {"items": items, "page": page, "per_page": per_page, "total": total, "media_job_id": media_job_id}


async def get_media_backups(
    db: AsyncSession,
    organization_id: str,
    media_job_id: str,
) -> list[ListingMediaBackupSnapshot]:
    await get_media_job(db, organization_id, media_job_id)

    q = await db.execute(
        select(ListingMediaBackupSnapshot).where(
            ListingMediaBackupSnapshot.media_job_id == media_job_id,
            ListingMediaBackupSnapshot.organization_id == organization_id,
        ).order_by(ListingMediaBackupSnapshot.created_at.asc())
    )
    return list(q.scalars().all())
