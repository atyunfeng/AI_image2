from uuid import uuid4

import pytest

from aiimage.assets.models import Asset
from aiimage.auth.models import Role
from aiimage.auth.service import create_user
from aiimage.catalog.models import Product
from aiimage.models.models import ModelConfiguration
from aiimage.quality.models import QualityCheck, QualityRun
from aiimage.review.schemas import ReviewRequest
from aiimage.review.service import ReviewConflictError, review_batch
from aiimage.workflow.models import GenerationBatch, GenerationStep
from aiimage.workflow.state import BatchStatus, StepStatus


@pytest.mark.asyncio
async def test_batch_with_blocking_quality_failure_cannot_be_approved(session_factory) -> None:
    async with session_factory() as session:
        user = await create_user(
            session,
            email=f"quality-{uuid4()}@aiimage.local",
            password="Quality-Password-2026",
            roles={Role.REVIEWER},
        )
        product = Product(
            sku=f"QA-{uuid4()}",
            name="QA product",
            category="apparel",
            created_by_user_id=user.id,
        )
        model = ModelConfiguration(
            name="qa-mock",
            provider="mock",
            model_id="mock-v1",
            capabilities=["reference_to_image"],
            created_by_user_id=user.id,
        )
        asset = Asset(
            object_key=f"sha256/qa/{uuid4()}",
            sha256=uuid4().hex + uuid4().hex,
            size_bytes=10,
            mime_type="image/png",
        )
        session.add_all([product, model, asset])
        await session.flush()
        batch = GenerationBatch(
            product_id=product.id,
            model_configuration_id=model.id,
            requested_view="front",
            mode="strict",
            prompt="qa",
            width=64,
            height=64,
            status=BatchStatus.REVIEW_PENDING.value,
            input_snapshot={},
            created_by_user_id=user.id,
        )
        session.add(batch)
        await session.flush()
        step = GenerationStep(
            batch_id=batch.id,
            idempotency_key=f"qa-{uuid4()}",
            status=StepStatus.SUCCEEDED.value,
            output_asset_id=asset.id,
        )
        run = QualityRun(batch_id=batch.id, output_asset_id=asset.id, passed=False)
        session.add_all([step, run])
        await session.flush()
        session.add(
            QualityCheck(
                run_id=run.id,
                code="dimensions",
                passed=False,
                blocking=True,
                expected={"width": 64},
                measured={"width": 32},
                message="bad dimensions",
            )
        )
        await session.commit()
        with pytest.raises(ReviewConflictError, match="blocking quality"):
            await review_batch(
                session,
                batch_id=batch.id,
                reviewer_user_id=user.id,
                payload=ReviewRequest(decision="approve"),
            )
