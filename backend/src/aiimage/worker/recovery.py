from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from aiimage.workflow.models import GenerationStep
from aiimage.workflow.queue import QueueHints
from aiimage.workflow.state import StepStatus


async def recover_generation_steps(
    session_factory: async_sessionmaker[AsyncSession],
    queue: QueueHints,
    *,
    now: datetime | None = None,
) -> list[UUID]:
    recovery_time = now or datetime.now(UTC)
    async with session_factory() as session:
        steps = list(
            (
                await session.scalars(
                    select(GenerationStep).where(
                        or_(
                            GenerationStep.status.in_(
                                [StepStatus.QUEUED.value, StepStatus.RETRY_QUEUED.value]
                            ),
                            (
                                (GenerationStep.status == StepStatus.RUNNING.value)
                                & (GenerationStep.lease_expires_at <= recovery_time)
                            ),
                        )
                    )
                )
            ).all()
        )
        for step in steps:
            if step.status == StepStatus.RUNNING.value:
                step.status = StepStatus.RETRY_QUEUED.value
                step.lease_owner = None
                step.lease_expires_at = None
        await session.commit()
    for step in steps:
        await queue.publish(step.id)
    return [step.id for step in steps]
