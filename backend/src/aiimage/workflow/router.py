from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from aiimage.api.dependencies import get_session
from aiimage.auth.dependencies import require_roles
from aiimage.auth.models import Role, User
from aiimage.workflow.models import GenerationBatch, GenerationStep
from aiimage.workflow.queue import QueueHints, get_queue_hints
from aiimage.workflow.schemas import (
    BatchDetailResponse,
    BatchResponse,
    CloneBatchRequest,
    CreateBatchRequest,
)
from aiimage.workflow.service import BatchValidationError, clone_batch, create_batch

router = APIRouter(prefix="/batches", tags=["batches"])
BatchUser = Annotated[User, Depends(require_roles(Role.ADMIN, Role.OPERATOR))]
BatchReader = Annotated[
    User,
    Depends(require_roles(Role.ADMIN, Role.OPERATOR, Role.REVIEWER)),
]


def _to_detail(batch: GenerationBatch, step: GenerationStep | None) -> BatchDetailResponse:
    return BatchDetailResponse(
        id=batch.id,
        production_plan_id=batch.production_plan_id,
        production_plan_item_id=batch.production_plan_item_id,
        fashion_plan_id=batch.fashion_plan_id,
        model_profile_id=batch.model_profile_id,
        edit_revision_id=batch.edit_revision_id,
        source_batch_id=batch.source_batch_id,
        product_id=batch.product_id,
        model_configuration_id=batch.model_configuration_id,
        requested_view=batch.requested_view,
        capability=batch.capability,
        mode=batch.mode,
        status=batch.status,
        prompt=batch.prompt,
        width=batch.width,
        height=batch.height,
        output_asset_id=step.output_asset_id if step else None,
        provider_request_id=step.provider_request_id if step else None,
        estimated_cost_minor=step.estimated_cost_minor if step else 0,
        error_classification=step.error_classification if step else None,
    )


@router.get("", response_model=list[BatchDetailResponse])
async def list_batches(
    user: BatchReader,
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
    batch_status: Annotated[str | None, Query(alias="status", max_length=30)] = None,
) -> list[BatchDetailResponse]:
    del user
    latest_step_id = (
        select(GenerationStep.id)
        .where(GenerationStep.batch_id == GenerationBatch.id)
        .order_by(desc(GenerationStep.attempt_count), desc(GenerationStep.id))
        .limit(1)
        .correlate(GenerationBatch)
        .scalar_subquery()
    )
    statement = select(GenerationBatch, GenerationStep).outerjoin(
        GenerationStep,
        GenerationStep.id == latest_step_id,
    )
    if batch_status:
        statement = statement.where(GenerationBatch.status == batch_status)
    rows = (
        await session.execute(
            statement.order_by(GenerationBatch.created_at.desc()).offset(offset).limit(limit)
        )
    ).all()
    return [_to_detail(batch, step) for batch, step in rows]


@router.get("/{batch_id}", response_model=BatchDetailResponse)
async def get_batch(
    batch_id: UUID,
    user: BatchReader,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> BatchDetailResponse:
    del user
    batch = await session.get(GenerationBatch, batch_id)
    if batch is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")
    step = await session.scalar(
        select(GenerationStep)
        .where(GenerationStep.batch_id == batch.id)
        .order_by(desc(GenerationStep.attempt_count))
        .limit(1)
    )
    return _to_detail(batch, step)


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


@router.post("/{batch_id}/retry", response_model=BatchResponse, status_code=201)
async def retry_batch_endpoint(
    batch_id: UUID,
    user: BatchUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    queue: Annotated[QueueHints, Depends(get_queue_hints)],
) -> BatchResponse:
    try:
        batch = await clone_batch(
            session, queue, batch_id=batch_id, payload=CloneBatchRequest(), user_id=user.id, retry=True
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Batch not found") from exc
    except BatchValidationError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return BatchResponse.model_validate(batch)


@router.post("/{batch_id}/duplicate", response_model=BatchResponse, status_code=201)
async def duplicate_batch_endpoint(
    batch_id: UUID,
    payload: CloneBatchRequest,
    user: BatchUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    queue: Annotated[QueueHints, Depends(get_queue_hints)],
) -> BatchResponse:
    try:
        batch = await clone_batch(
            session, queue, batch_id=batch_id, payload=payload, user_id=user.id, retry=False
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Batch not found") from exc
    except BatchValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return BatchResponse.model_validate(batch)
