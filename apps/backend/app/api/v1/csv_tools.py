from fastapi import APIRouter, Depends, Query, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_org_id, require_active_user
from app.db.session import get_db
from app.schemas.csv_tools import (
    CSVJobOut,
    CSVRowOut,
    CSVPreviewPageOut,
    CSVConvertRequest,
    CSVConvertResponse,
    CSVImportSummaryOut,
)
from app.services.csv_tools import (
    CSVToolsError,
    export_listings_to_csv,
    csv_template,
    parse_csv_upload,
    create_csv_import_job,
    list_csv_jobs,
    get_csv_job,
    get_csv_preview,
    convert_csv_job_to_bulk_edit_session,
    MAX_IMPORT_ROWS,
)

router = APIRouter(prefix="/csv", tags=["csv"])


def _raise(exc: CSVToolsError):
    raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.get("/export")
async def export_csv(
    shop_id: str | None = Query(None),
    state: str | None = Query(None),
    org_id: str = Depends(get_current_org_id),
    user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    csv_text = await export_listings_to_csv(db, org_id, shop_id=shop_id, state=state)

    def _iter():
        yield csv_text.encode("utf-8")

    return StreamingResponse(
        _iter(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="bulk-edit-listings.csv"'},
    )


@router.get("/template")
async def download_template(
    user=Depends(require_active_user),
    org_id: str = Depends(get_current_org_id),
):
    template_text = csv_template()

    def _iter():
        yield template_text.encode("utf-8")

    return StreamingResponse(
        _iter(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="bulk-edit-template.csv"'},
    )


@router.post("/import", response_model=CSVImportSummaryOut, status_code=201)
async def import_csv(
    file: UploadFile = File(...),
    org_id: str = Depends(get_current_org_id),
    user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    fname = file.filename or ""
    if fname and not fname.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv files are accepted.")
    if file.content_type and file.content_type not in (
        "text/csv", "application/csv", "text/plain", "application/octet-stream",
    ):
        if not fname.lower().endswith(".csv"):
            raise HTTPException(status_code=400, detail="File must be a CSV.")

    file_bytes = await file.read()
    try:
        raw_rows, ignored = parse_csv_upload(file_bytes, fname)
    except CSVToolsError as exc:
        _raise(exc)

    try:
        job = await create_csv_import_job(
            db,
            organization_id=org_id,
            user_id=str(user.id),
            filename=fname,
            raw_rows=raw_rows,
            ignored_columns=ignored,
        )
    except CSVToolsError as exc:
        _raise(exc)

    return CSVImportSummaryOut(
        job_id=job.id,
        status=job.status,
        row_count=job.row_count,
        valid_row_count=job.valid_row_count,
        invalid_row_count=job.invalid_row_count,
        changed_row_count=job.changed_row_count,
        unchanged_row_count=job.unchanged_row_count,
        ignored_columns=job.ignored_columns or [],
        message=f"Parsed {job.row_count} rows. {job.valid_row_count} valid, {job.invalid_row_count} invalid, {job.unchanged_row_count} unchanged.",
    )


@router.get("/jobs", response_model=list[CSVJobOut])
async def list_jobs(
    job_type: str | None = Query(None),
    org_id: str = Depends(get_current_org_id),
    user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    return await list_csv_jobs(db, org_id, job_type=job_type)


@router.get("/jobs/{job_id}", response_model=CSVJobOut)
async def get_job(
    job_id: str,
    org_id: str = Depends(get_current_org_id),
    user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await get_csv_job(db, org_id, job_id)
    except CSVToolsError as exc:
        _raise(exc)


@router.get("/jobs/{job_id}/preview", response_model=CSVPreviewPageOut)
async def preview_job(
    job_id: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    status: str | None = Query(None),
    org_id: str = Depends(get_current_org_id),
    user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        rows, total = await get_csv_preview(db, org_id, job_id, page=page, per_page=per_page, status=status)
        return CSVPreviewPageOut(items=rows, total=total, page=page, per_page=per_page, csv_job_id=job_id)
    except CSVToolsError as exc:
        _raise(exc)


@router.post("/jobs/{job_id}/convert", response_model=CSVConvertResponse)
async def convert_job(
    job_id: str,
    body: CSVConvertRequest = CSVConvertRequest(),
    org_id: str = Depends(get_current_org_id),
    user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        session, converted_rows, created_changes = await convert_csv_job_to_bulk_edit_session(
            db,
            organization_id=org_id,
            user_id=str(user.id),
            csv_job_id=job_id,
            ignore_invalid=body.ignore_invalid,
        )
        return CSVConvertResponse(
            bulk_edit_session_id=session.id,
            converted_rows=converted_rows,
            created_changes=created_changes,
            message=(
                f"Created bulk edit session from {converted_rows} CSV rows "
                f"({created_changes} changes). Review and apply in Bulk Edit — "
                "changes will NOT be published to Etsy until you approve them there."
            ),
        )
    except CSVToolsError as exc:
        _raise(exc)
