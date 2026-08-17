from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from aiimage.auth.models import Role
from aiimage.auth.service import create_user
from aiimage.catalog.models import Product
from aiimage.models.domain import Capability
from aiimage.models.models import ModelConfiguration
from aiimage.worker.recovery import recover_generation_steps
from aiimage.workflow.models import GenerationBatch, GenerationStep
from aiimage.workflow.state import BatchStatus, StepStatus


class RecordingQueue:
    def __init__(self) -> None:
        self.published: list[UUID] = []

    async def publish(self, step_id: UUID) -> bool:
        self.published.append(step_id)
        return True


@pytest.mark.asyncio
async def test_recovers_queued_and_expired_steps(session_factory) -> None:
    now = datetime.now(UTC)
    async with session_factory() as session:
        user = await create_user(
            session,
            email=f"recovery-{uuid4()}@aiimage.local",
            password="Worker-Password-2026",
            roles={Role.OPERATOR},
        )
        product = Product(
            sku=f"SKU-{uuid4()}",
            name="Recovery product",
            category="shoes",
            created_by_user_id=user.id,
        )
        model = ModelConfiguration(
            name=f"mock-{uuid4()}",
            provider="mock",
            model_id="mock-v1",
            capabilities=[Capability.REFERENCE_TO_IMAGE.value],
            created_by_user_id=user.id,
        )
        session.add_all([product, model])
        await session.flush()
        batch = GenerationBatch(
            product_id=product.id,
            model_configuration_id=model.id,
            requested_view="front",
            mode="strict",
            prompt="test",
            width=64,
            height=64,
            status=BatchStatus.RUNNING.value,
            input_snapshot={},
            created_by_user_id=user.id,
        )
        session.add(batch)
        await session.flush()
        queued = GenerationStep(batch_id=batch.id, idempotency_key=f"q-{uuid4()}")
        expired = GenerationStep(
            batch_id=batch.id,
            idempotency_key=f"e-{uuid4()}",
            status=StepStatus.RUNNING.value,
            lease_owner="lost-worker",
            lease_expires_at=now - timedelta(minutes=1),
        )
        session.add_all([queued, expired])
        await session.commit()
        queued_id, expired_id = queued.id, expired.id

    queue = RecordingQueue()
    recovered = await recover_generation_steps(session_factory, queue, now=now)

    assert set(recovered) == {queued_id, expired_id}
    assert set(queue.published) == {queued_id, expired_id}
    async with session_factory() as session:
        expired = await session.get(GenerationStep, expired_id)
        assert expired.status == StepStatus.RETRY_QUEUED.value
        assert expired.lease_owner is None
