from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from aiimage.api.dependencies import get_session
from aiimage.auth.dependencies import require_roles
from aiimage.auth.models import Role, User
from aiimage.fashion.compiler import FashionCompilationError
from aiimage.fashion.schemas import CreateFashionPlanRequest, FashionPlanResponse
from aiimage.fashion.service import create_fashion_plan, get_fashion_plan
from aiimage.workflow.queue import QueueHints, get_queue_hints

router = APIRouter(prefix="/fashion-plans", tags=["fashion-plans"])
FashionUser = Annotated[User, Depends(require_roles(Role.ADMIN, Role.OPERATOR, Role.DESIGNER))]


@router.post("", response_model=FashionPlanResponse, status_code=status.HTTP_201_CREATED)
async def create_fashion_plan_endpoint(
    payload: CreateFashionPlanRequest,
    user: FashionUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    queue: Annotated[QueueHints, Depends(get_queue_hints)],
) -> FashionPlanResponse:
    try:
        return await create_fashion_plan(session, queue, payload=payload, user_id=user.id)
    except FashionCompilationError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.get("/{plan_id}", response_model=FashionPlanResponse)
async def read_fashion_plan(
    plan_id: UUID,
    user: FashionUser,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> FashionPlanResponse:
    del user
    plan = await get_fashion_plan(session, plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="Fashion plan not found")
    return plan
