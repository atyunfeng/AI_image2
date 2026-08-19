import csv
from io import StringIO
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from aiimage.api.dependencies import get_session
from aiimage.auth.dependencies import require_roles
from aiimage.auth.models import Role, User
from aiimage.bulk.schemas import BulkJobResponse
from aiimage.bulk.service import BulkImportError, create_bulk_job, get_bulk_job, list_bulk_jobs
from aiimage.workflow.queue import QueueHints, get_queue_hints

router = APIRouter(prefix="/bulk-jobs", tags=["bulk-jobs"])
BulkUser = Annotated[User, Depends(require_roles(Role.ADMIN, Role.OPERATOR))]


@router.get("", response_model=list[BulkJobResponse])
async def read_bulk_jobs(
    user: BulkUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[BulkJobResponse]:
    del user
    return await list_bulk_jobs(session, limit=limit, offset=offset)


@router.get("/{job_id}", response_model=BulkJobResponse)
async def read_bulk_job(
    job_id: UUID,
    user: BulkUser,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> BulkJobResponse:
    del user
    job = await get_bulk_job(session, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Bulk job not found")
    return job


@router.get("/{job_id}/errors.csv")
async def download_bulk_errors(
    job_id: UUID,
    user: BulkUser,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Response:
    del user
    job = await get_bulk_job(session, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Bulk job not found")
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["row_number", "sku", "error"])
    for row in job.rows:
        if row.error:
            writer.writerow([row.row_number, row.sku, row.error])
    return Response(
        content="\ufeff" + output.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="bulk-{job_id}-errors.csv"'},
    )


@router.post("/import", response_model=BulkJobResponse, status_code=status.HTTP_201_CREATED)
async def import_bulk_job(
    user: BulkUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    queue: Annotated[QueueHints, Depends(get_queue_hints)],
    model_configuration_id: Annotated[UUID, Form()],
    category_pack_version_id: Annotated[UUID, Form()],
    brand_pack_version_id: Annotated[UUID, Form()],
    dry_run: Annotated[bool, Form()] = False,
    file: Annotated[UploadFile, File()] = None,
) -> BulkJobResponse:
    if file is None:
        raise HTTPException(status_code=422, detail="CSV or XLSX file is required")
    try:
        return await create_bulk_job(
            session,
            queue,
            filename=file.filename or "import.csv",
            content=await file.read(),
            dry_run=dry_run,
            model_configuration_id=model_configuration_id,
            category_pack_version_id=category_pack_version_id,
            brand_pack_version_id=brand_pack_version_id,
            user_id=user.id,
        )
    except BulkImportError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
