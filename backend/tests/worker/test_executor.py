from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import select

from aiimage.assets.models import Asset
from aiimage.assets.storage import InMemoryObjectStore
from aiimage.auth.models import Role
from aiimage.auth.service import create_user
from aiimage.catalog.models import Product, ProductReference
from aiimage.config import get_settings
from aiimage.models.domain import Capability
from aiimage.models.models import ModelConfiguration
from aiimage.providers.registry import ProviderRegistry
from aiimage.worker.executor import WorkerContext, execute_step
from aiimage.workflow.models import GenerationBatch, GenerationStep
from aiimage.workflow.state import BatchStatus, StepStatus


async def _queued_step(session_factory, png_bytes):
    store = InMemoryObjectStore()
    stored = await store.put(content=png_bytes, mime_type="image/png")
    async with session_factory() as session:
        user = await create_user(
            session,
            email=f"worker-{uuid4()}@aiimage.local",
            password="Worker-Password-2026",
            roles={Role.OPERATOR},
        )
        asset = Asset(
            object_key=stored.object_key,
            sha256=stored.sha256,
            size_bytes=stored.size_bytes,
            mime_type=stored.mime_type,
        )
        session.add(asset)
        await session.flush()
        product = Product(
            sku=f"SKU-{uuid4()}",
            name="Worker test product",
            category="apparel",
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
        reference = ProductReference(product_id=product.id, asset_id=asset.id, view="front")
        session.add(reference)
        await session.flush()
        batch = GenerationBatch(
            product_id=product.id,
            model_configuration_id=model.id,
            requested_view="front",
            mode="strict",
            prompt="plain studio product photo",
            width=64,
            height=64,
            status=BatchStatus.QUEUED.value,
            input_snapshot={
                "product_id": str(product.id),
                "sku": product.sku,
                "reference_ids": [str(reference.id)],
                "truth_anchor_version": 1,
            },
            created_by_user_id=user.id,
        )
        session.add(batch)
        await session.flush()
        step = GenerationStep(
            batch_id=batch.id,
            idempotency_key=f"worker-{uuid4()}",
        )
        session.add(step)
        await session.commit()
        return step.id, batch.id, store


@pytest.mark.asyncio
async def test_worker_stores_output_and_advances_batch(session_factory, png_bytes) -> None:
    step_id, batch_id, store = await _queued_step(session_factory, png_bytes)
    context = WorkerContext(
        session_factory=session_factory,
        object_store=store,
        provider_registry=ProviderRegistry(
            secret_key_base64=get_settings().secret_key_base64
        ),
    )

    assert await execute_step(step_id, worker_id="test-worker", context=context)

    async with session_factory() as session:
        step = await session.get(GenerationStep, step_id)
        batch = await session.get(GenerationBatch, batch_id)
        output = await session.scalar(select(Asset).where(Asset.id == step.output_asset_id))
        assert step.status == StepStatus.SUCCEEDED.value
        assert output is not None
        assert batch.status == BatchStatus.REVIEW_PENDING.value


@pytest.mark.asyncio
async def test_duplicate_delivery_is_noop(session_factory, png_bytes) -> None:
    step_id, _, store = await _queued_step(session_factory, png_bytes)
    context = WorkerContext(
        session_factory=session_factory,
        object_store=store,
        provider_registry=ProviderRegistry(
            secret_key_base64=get_settings().secret_key_base64
        ),
    )
    assert await execute_step(step_id, worker_id="test-worker", context=context)
    object_count = len(store.objects)

    assert not await execute_step(step_id, worker_id="test-worker", context=context)
    assert len(store.objects) == object_count


@pytest.mark.asyncio
async def test_worker_respects_shared_global_and_provider_limits(session_factory, png_bytes) -> None:
    running_step_id, batch_id, store = await _queued_step(session_factory, png_bytes)
    async with session_factory() as session:
        running = await session.get(GenerationStep, running_step_id)
        source_batch = await session.get(GenerationBatch, batch_id)
        running.status = StepStatus.RUNNING.value
        running.lease_owner = "another-worker"
        running.lease_expires_at = datetime.now(UTC) + timedelta(minutes=2)
        queued_batch = GenerationBatch(
            product_id=source_batch.product_id,
            model_configuration_id=source_batch.model_configuration_id,
            requested_view="front",
            mode="strict",
            prompt="queued while capacity is full",
            width=64,
            height=64,
            status=BatchStatus.QUEUED.value,
            input_snapshot=source_batch.input_snapshot,
            created_by_user_id=source_batch.created_by_user_id,
        )
        session.add(queued_batch)
        await session.flush()
        queued_step = GenerationStep(
            batch_id=queued_batch.id,
            idempotency_key=f"queued-limit-{uuid4()}",
        )
        session.add(queued_step)
        await session.commit()
        queued_step_id = queued_step.id
    context = WorkerContext(
        session_factory=session_factory,
        object_store=store,
        provider_registry=ProviderRegistry(
            secret_key_base64=get_settings().secret_key_base64
        ),
        max_concurrency=4,
        provider_concurrency_limits={"mock": 1},
    )

    assert not await execute_step(queued_step_id, worker_id="limited-worker", context=context)
    global_context = WorkerContext(
        session_factory=session_factory,
        object_store=store,
        provider_registry=context.provider_registry,
        max_concurrency=1,
    )
    assert not await execute_step(
        queued_step_id, worker_id="globally-limited-worker", context=global_context
    )
    async with session_factory() as session:
        queued = await session.get(GenerationStep, queued_step_id)
        assert queued.status == StepStatus.QUEUED.value
        assert queued.lease_owner is None
