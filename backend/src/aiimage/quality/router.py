from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from aiimage.api.dependencies import get_session
from aiimage.auth.dependencies import require_roles
from aiimage.auth.models import Role, User
from aiimage.quality.schemas import QualityRunResponse
from aiimage.quality.service import latest_quality_response

router = APIRouter(prefix="/batches", tags=["quality"])
QualityUser = Annotated[
    User, Depends(require_roles(Role.ADMIN, Role.OPERATOR, Role.DESIGNER, Role.REVIEWER))
]


@router.get("/{batch_id}/quality", response_model=QualityRunResponse)
async def get_batch_quality(
    batch_id: UUID,
    user: QualityUser,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> QualityRunResponse:
    del user
    response = await latest_quality_response(session, batch_id)
    if response is None:
        raise HTTPException(status_code=404, detail="Quality evidence not found")
    return response
