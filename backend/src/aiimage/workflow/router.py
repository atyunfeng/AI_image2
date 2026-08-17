from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from aiimage.api.dependencies import get_session
from aiimage.auth.dependencies import require_roles
from aiimage.auth.models import Role, User
from aiimage.workflow.queue import QueueHints, get_queue_hints
from aiimage.workflow.schemas import BatchResponse, CreateBatchRequest
from aiimage.workflow.service import BatchValidationError, create_batch

router = APIRouter(prefix="/batches", tags=["batches"])
BatchUser = Annotated[User, Depends(require_roles(Role.ADMIN, Role.OPERATOR))]


@router.post("", response_model=BatchResponse, status_code=status.HTTP_201_CREATED)
async def create_batch_endpoint(
    payload: CreateBatchRequest,
    user: BatchUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    queue: Annotated[QueueHints, Depends(get_queue_hints)],
) -> BatchResponse:
    try:
        batch = await create_batch(session, queue, payload=payload, user_id=user.id)
    except BatchValidationError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error
    return BatchResponse.model_validate(batch)

