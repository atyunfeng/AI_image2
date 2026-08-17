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
    ManagedTemplatePackResponse,
    ProductionPlanResponse,
    TemplatePackCreate,
    TemplatePackResponse,
    TemplatePackVersionCreate,
    TemplatePackVersionResponse,
)
from aiimage.templates.service import (
    DuplicatePackSlugError,
    PackManagementError,
    create_pack_version,
    create_production_plan,
    create_template_pack,
    get_production_plan,
    list_managed_packs,
    list_published_packs,
    publish_pack_version,
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


TemplateManager = Annotated[User, Depends(require_roles(Role.ADMIN, Role.DESIGNER))]


@router.get("/manage", response_model=list[ManagedTemplatePackResponse])
async def manage_template_packs(
    user: TemplateManager,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[ManagedTemplatePackResponse]:
    del user
    return await list_managed_packs(session)


@router.post("", response_model=ManagedTemplatePackResponse, status_code=201)
async def author_template_pack(
    payload: TemplatePackCreate,
    user: TemplateManager,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ManagedTemplatePackResponse:
    try:
        return await create_template_pack(session, payload=payload, user_id=user.id)
    except DuplicatePackSlugError as exc:
        raise HTTPException(status_code=409, detail="Template pack slug already exists") from exc


@router.post("/{pack_id}/versions", response_model=TemplatePackVersionResponse, status_code=201)
async def author_template_pack_version(
    pack_id: UUID,
    payload: TemplatePackVersionCreate,
    user: TemplateManager,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> TemplatePackVersionResponse:
    try:
        return await create_pack_version(
            session, pack_id=pack_id, payload=payload, user_id=user.id
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Template pack not found") from exc
    except PackManagementError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


version_router = APIRouter(prefix="/template-pack-versions", tags=["template-packs"])


@version_router.post("/{version_id}/publish", response_model=TemplatePackVersionResponse)
async def publish_template_pack_version(
    version_id: UUID,
    user: TemplateManager,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> TemplatePackVersionResponse:
    try:
        return await publish_pack_version(session, version_id=version_id, user_id=user.id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Template pack version not found") from exc
    except PackManagementError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


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
