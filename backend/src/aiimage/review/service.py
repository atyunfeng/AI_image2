from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from aiimage.quality.service import has_blocking_quality_failure
from aiimage.review.models import ReviewDecision
from aiimage.review.schemas import ReviewRequest
from aiimage.workflow.models import GenerationBatch, GenerationStep
from aiimage.workflow.state import BatchStatus, StepStatus


class ReviewConflictError(RuntimeError):
    pass


async def review_batch(
    session: AsyncSession,
    *,
    batch_id: UUID,
    reviewer_user_id: UUID,
    payload: ReviewRequest,
) -> ReviewDecision:
    batch = await session.scalar(
        select(GenerationBatch)
        .where(GenerationBatch.id == batch_id)
        .with_for_update()
    )
    if batch is None:
        raise LookupError(batch_id)
    if batch.status not in {
        BatchStatus.REVIEW_PENDING.value,
        BatchStatus.REJECTED.value,
        BatchStatus.APPROVED.value,
    }:
        raise ReviewConflictError("Batch is not ready for review")
    step = await session.scalar(
        select(GenerationStep)
        .where(GenerationStep.batch_id == batch.id)
        .order_by(desc(GenerationStep.attempt_count))
        .limit(1)
    )
    if step is None:
        raise ReviewConflictError("Batch has no generation output")
    if payload.decision == "approve":
        if step.status != StepStatus.SUCCEEDED.value or step.output_asset_id is None:
            raise ReviewConflictError("Approval requires a succeeded output asset")
        if await has_blocking_quality_failure(session, batch.id):
            raise ReviewConflictError("Batch has blocking quality failures")
        batch.status = BatchStatus.APPROVED.value
    else:
        batch.status = BatchStatus.REJECTED.value
    decision = ReviewDecision(
        batch_id=batch.id,
        step_id=step.id,
        output_asset_id=step.output_asset_id,
        reviewer_user_id=reviewer_user_id,
        decision=payload.decision,
        rejection_reason=payload.rejection_reason,
        note=(payload.note or "").strip() or None,
    )
    session.add(decision)
    await session.commit()
    await session.refresh(decision)
    return decision
