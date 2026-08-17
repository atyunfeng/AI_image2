from uuid import uuid4

import pytest
from pydantic import ValidationError

from aiimage.assets.models import Asset
from aiimage.assets.storage import InMemoryObjectStore
from aiimage.auth.models import Role
from aiimage.auth.service import create_user
from aiimage.catalog.models import Product
from aiimage.models.domain import Capability
from aiimage.models.models import ModelConfiguration
from aiimage.review.schemas import ReviewRequest
from aiimage.review.service import review_batch
from aiimage.workflow.models import GenerationBatch, GenerationStep
from aiimage.workflow.state import BatchStatus, StepStatus


@pytest.mark.asyncio
async def test_approval_requires_and_records_succeeded_output(session_factory, png_bytes) -> None:
    store = InMemoryObjectStore()
    stored = await store.put(content=png_bytes, mime_type="image/png")
    async with session_factory() as session:
        reviewer = await create_user(
            session,
            email=f"reviewer-{uuid4()}@aiimage.local",
            password="Reviewer-Password-2026",
            roles={Role.REVIEWER},
        )
        asset = Asset(
            object_key=stored.object_key,
            sha256=stored.sha256,
            size_bytes=stored.size_bytes,
            mime_type=stored.mime_type,
        )
        product = Product(
            sku=f"SKU-{uuid4()}",
            name="Review product",
            category="apparel",
            created_by_user_id=reviewer.id,
        )
        model = ModelConfiguration(
            name=f"model-{uuid4()}",
            provider="mock",
            model_id="mock-v1",
            capabilities=[Capability.REFERENCE_TO_IMAGE.value],
            created_by_user_id=reviewer.id,
        )
        session.add_all([asset, product, model])
        await session.flush()
        batch = GenerationBatch(
            product_id=product.id,
            model_configuration_id=model.id,
            requested_view="front",
            mode="strict",
            prompt="clean studio",
            width=64,
            height=64,
            status=BatchStatus.REVIEW_PENDING.value,
            input_snapshot={"reference_ids": [], "truth_anchor_version": 1},
            created_by_user_id=reviewer.id,
        )
        session.add(batch)
        await session.flush()
        step = GenerationStep(
            batch_id=batch.id,
            idempotency_key=f"review-{uuid4()}",
            status=StepStatus.SUCCEEDED.value,
            output_asset_id=asset.id,
        )
        session.add(step)
        await session.commit()

        decision = await review_batch(
            session,
            batch_id=batch.id,
            reviewer_user_id=reviewer.id,
            payload=ReviewRequest(decision="approve"),
        )

        assert decision.output_asset_id == asset.id
        assert batch.status == BatchStatus.APPROVED.value


def test_other_rejection_reason_requires_note() -> None:
    with pytest.raises(ValidationError):
        ReviewRequest(decision="reject", rejection_reason="other")
