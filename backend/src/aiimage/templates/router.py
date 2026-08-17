from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from aiimage.api.dependencies import get_session
from aiimage.auth.dependencies import require_roles
from aiimage.auth.models import Role, User
from aiimage.templates.compiler import PlanCompilationError
from aiimage.templates.schemas import (
    CompilePlanRequest,
    ProductionPlanResponse,
    TemplatePackResponse,
)
from aiimage.templates.service import (
    create_production_plan,
    get_production_plan,
    list_published_packs,
)
from aiimage.workflow.queue import QueueHints, get_queue_hints
from aiimage.workflow.schemas import BatchResponse, ExecuteProductionPlanRequest
from aiimage.workflow.service import BatchValidationError, execute_production_plan

router = APIRouter(prefix="/template-packs", tags=["template-packs"])
TemplateUser = Annotated[
    User, Depends(require_roles(Role.ADMIN, Role.OPERATOR, Role.DESIGNER))
]


@router.get("", response_model=list[TemplatePackResponse])
async def list_template_packs(
    user: TemplateUser,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[TemplatePackResponse]:
    del user
    return await list_published_packs(session)


plan_router = APIRouter(prefix="/production-plans", tags=["production-plans"])


@plan_router.post("/compile", response_model=ProductionPlanResponse, status_code=201)
async def compile_production_plan(
    payload: CompilePlanRequest,
    user: TemplateUser,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ProductionPlanResponse:
    try:
        return await create_production_plan(session, payload=payload, user_id=user.id)
    except PlanCompilationError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)
        ) from error


@plan_router.get("/{plan_id}", response_model=ProductionPlanResponse)
async def read_production_plan(
    plan_id: UUID,
    user: TemplateUser,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ProductionPlanResponse:
    del user
    plan = await get_production_plan(session, plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="Production plan not found")
    return plan


@plan_router.post(
    "/{plan_id}/execute",
    response_model=list[BatchResponse],
    status_code=status.HTTP_201_CREATED,
)
async def execute_plan_endpoint(
    plan_id: UUID,
    payload: ExecuteProductionPlanRequest,
    user: TemplateUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    queue: Annotated[QueueHints, Depends(get_queue_hints)],
) -> list[BatchResponse]:
    try:
        batches = await execute_production_plan(
            session,
            queue,
            plan_id=plan_id,
            model_configuration_id=payload.model_configuration_id,
            user_id=user.id,
        )
    except BatchValidationError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)
        ) from error
    return [BatchResponse.model_validate(batch) for batch in batches]
