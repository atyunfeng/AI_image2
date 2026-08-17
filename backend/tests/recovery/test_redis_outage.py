from uuid import uuid4

import pytest
from sqlalchemy import select

from aiimage.auth.models import Role
from aiimage.auth.service import create_user
from aiimage.catalog.models import Product
from aiimage.models.domain import Capability
from aiimage.models.models import ModelConfiguration
from aiimage.workflow.models import GenerationStep
from aiimage.workflow.schemas import CreateBatchRequest
from aiimage.workflow.service import create_batch
from aiimage.workflow.state import BatchStatus


class UnavailableQueue:
    async def publish(self, step_id):
        del step_id
        return False


@pytest.mark.asyncio
async def test_queued_step_survives_redis_outage(session_factory) -> None:
    async with session_factory() as session:
        user = await create_user(session, email=f"outage-{uuid4()}@local", password="Outage-Password-2026", roles={Role.OPERATOR})
        product = Product(sku=f"OUTAGE-{uuid4()}", name="Outage", category="apparel", created_by_user_id=user.id)
        model = ModelConfiguration(name=f"outage-{uuid4()}", provider="mock", model_id="mock-v1", capabilities=[Capability.REFERENCE_TO_IMAGE.value], created_by_user_id=user.id)
        session.add_all([product, model]); await session.commit()
        batch = await create_batch(session, UnavailableQueue(), payload=CreateBatchRequest(product_id=product.id, model_configuration_id=model.id, requested_view="front", prompt="test", width=64, height=64), user_id=user.id)
        assert batch.status == BatchStatus.QUEUED.value
        step = await session.scalar(
            select(GenerationStep).where(GenerationStep.batch_id == batch.id)
        )
        assert step is not None
        assert step.status == "queued"
