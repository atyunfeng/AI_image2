from uuid import uuid4

import pytest
from sqlalchemy import select

from aiimage.assets.models import Asset
from aiimage.assets.storage import InMemoryObjectStore
from aiimage.auth.models import Role
from aiimage.auth.service import create_user
from aiimage.catalog.models import Product, ProductReference
from aiimage.fashion.evidence_models import FashionEvidence
from aiimage.fashion.models import FashionPlan
from aiimage.models.domain import Capability, GenerationRequest
from aiimage.models.models import ModelConfiguration
from aiimage.providers.mock import MockProvider
from aiimage.talent.models import ModelProfile, ModelReference
from aiimage.worker.executor import WorkerContext, execute_step
from aiimage.workflow.models import GenerationBatch, GenerationStep
from aiimage.workflow.state import BatchStatus


class RecordingProvider:
    def __init__(self) -> None:
        self.request: GenerationRequest | None = None
        self.mock = MockProvider()

    async def generate(self, request: GenerationRequest):
        self.request = request
        return await self.mock.generate(request)


class RecordingRegistry:
    def __init__(self, provider: RecordingProvider) -> None:
        self.provider = provider

    def get(self, configuration):
        return self.provider


@pytest.mark.asyncio
async def test_virtual_try_on_receives_product_and_model_references(
    session_factory, png_bytes
) -> None:
    store = InMemoryObjectStore()
    stored = await store.put(content=png_bytes, mime_type="image/png")
    async with session_factory() as session:
        user = await create_user(
            session,
            email=f"fashion-worker-{uuid4()}@aiimage.local",
            password="Fashion-Worker-2026",
            roles={Role.OPERATOR},
        )
        asset = Asset(
            object_key=stored.object_key,
            sha256=stored.sha256,
            size_bytes=stored.size_bytes,
            mime_type=stored.mime_type,
        )
        product = Product(
            sku=f"FW-{uuid4()}",
            name="Fashion worker product",
            category="apparel",
            created_by_user_id=user.id,
        )
        profile = ModelProfile(
            name="System model",
            profile_type="system_virtual",
            authorization_status="not_required",
            attributes={},
            created_by_user_id=user.id,
        )
        model = ModelConfiguration(
            name="fashion-mock",
            provider="mock",
            model_id="mock-fashion-v1",
            capabilities=[Capability.VIRTUAL_TRY_ON.value],
            created_by_user_id=user.id,
        )
        session.add_all([asset, product, profile, model])
        await session.flush()
        product_reference = ProductReference(
            product_id=product.id, asset_id=asset.id, view="front"
        )
        model_reference = ModelReference(profile_id=profile.id, asset_id=asset.id, view="front")
        session.add_all([product_reference, model_reference])
        await session.flush()
        plan = FashionPlan(
            product_id=product.id,
            model_profile_id=profile.id,
            model_configuration_id=model.id,
            category="apparel",
            mode="strict",
            requested_outputs=["virtual_try_on"],
            input_snapshot={},
            created_by_user_id=user.id,
        )
        session.add(plan)
        await session.flush()
        batch = GenerationBatch(
            fashion_plan_id=plan.id,
            model_profile_id=profile.id,
            product_id=product.id,
            model_configuration_id=model.id,
            requested_view="front",
            capability=Capability.VIRTUAL_TRY_ON.value,
            mode="strict",
            prompt="virtual try on",
            width=64,
            height=64,
            status=BatchStatus.QUEUED.value,
            input_snapshot={
                "reference_ids": [str(product_reference.id)],
                "model_reference_ids": [str(model_reference.id)],
                "required_product_views": ["front"],
                "required_model_views": ["front"],
                "fashion_output": "virtual_try_on",
                "inferred_view": False,
                "human_review_checks": ["anatomy", "model_identity"],
            },
            created_by_user_id=user.id,
        )
        session.add(batch)
        await session.flush()
        step = GenerationStep(batch_id=batch.id, idempotency_key=f"fashion-{uuid4()}")
        session.add(step)
        await session.commit()
        step_id = step.id
        batch_id = batch.id

    provider = RecordingProvider()
    context = WorkerContext(
        session_factory=session_factory,
        object_store=store,
        provider_registry=RecordingRegistry(provider),
    )
    assert await execute_step(step_id, "fashion-worker", context)
    assert provider.request is not None
    assert provider.request.capability == Capability.VIRTUAL_TRY_ON
    assert provider.request.parameters["product_reference_count"] == 1
    assert provider.request.parameters["model_reference_count"] == 1
    assert len(provider.request.reference_images) == 2
    async with session_factory() as session:
        batch = await session.get(GenerationBatch, batch_id)
        evidence = await session.scalar(
            select(FashionEvidence).where(FashionEvidence.batch_id == batch_id)
        )
        assert batch.status == BatchStatus.REVIEW_PENDING.value
        assert evidence.automated_passed
        assert evidence.human_review_checks == ["anatomy", "model_identity"]
