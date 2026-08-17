from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from aiimage.api.dependencies import get_session
from aiimage.assets.storage import ObjectStore, get_object_store
from aiimage.auth.dependencies import require_roles
from aiimage.auth.models import Role, User
from aiimage.export.service import ExportConflictError, build_export_zip

router = APIRouter(prefix="/batches", tags=["export"])
ExportUser = Annotated[User, Depends(require_roles(Role.ADMIN, Role.OPERATOR, Role.REVIEWER))]


@router.get("/{batch_id}/export.zip")
async def export_batch_endpoint(
    batch_id: UUID,
    user: ExportUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    store: Annotated[ObjectStore, Depends(get_object_store)],
) -> Response:
    del user
    try:
        content = await build_export_zip(session, store, batch_id=batch_id)
    except LookupError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found") from error
    except ExportConflictError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    return Response(
        content=content,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="batch-{batch_id}.zip"'},
    )
