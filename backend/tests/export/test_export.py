import json
from io import BytesIO
from uuid import uuid4
from zipfile import ZipFile

import pytest

from aiimage.assets.models import Asset
from aiimage.assets.storage import InMemoryObjectStore
from aiimage.auth.models import Role
from aiimage.auth.service import create_user
from aiimage.catalog.models import Product, ProductReference
from aiimage.export.service import ExportConflictError, build_export_zip
from aiimage.models.domain import Capability
from aiimage.models.models import ModelConfiguration
from aiimage.review.models import ReviewDecision
from aiimage.workflow.models import GenerationBatch, GenerationStep
from aiimage.workflow.state import BatchStatus, StepStatus


async def _export_fixture(session_factory, png_bytes, status: BatchStatus):
    store = InMemoryObjectStore()
    stored = await store.put(content=png_bytes, mime_type="image/png")
    async with session_factory() as session:
        reviewer = await create_user(
            session,
            email=f"export-{uuid4()}@aiimage.local",
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
            name="Export product",
            category="shoes",
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
        reference = ProductReference(product_id=product.id, asset_id=asset.id, view="front")
        session.add(reference)
        await session.flush()
        batch = GenerationBatch(
            product_id=product.id,
            model_configuration_id=model.id,
            requested_view="front",
            mode="strict",
            prompt="marketplace white background",
            width=1024,
            height=1024,
            status=status.value,
            input_snapshot={
                "reference_ids": [str(reference.id)],
                "truth_anchor_version": 3,
            },
            created_by_user_id=reviewer.id,
        )
        session.add(batch)
        await session.flush()
        step = GenerationStep(
            batch_id=batch.id,
            idempotency_key=f"export-{uuid4()}",
            status=StepStatus.SUCCEEDED.value,
            output_asset_id=asset.id,
            provider_request_id="mock-export",
            estimated_cost_minor=0,
        )
        session.add(step)
        await session.flush()
        if status == BatchStatus.APPROVED:
            session.add(
                ReviewDecision(
                    batch_id=batch.id,
                    step_id=step.id,
                    output_asset_id=asset.id,
                    reviewer_user_id=reviewer.id,
                    decision="approve",
                )
            )
        await session.commit()
        return batch.id, product.sku, stored.sha256, store


@pytest.mark.asyncio
async def test_rejected_batch_cannot_export(session_factory, png_bytes) -> None:
    batch_id, _, _, store = await _export_fixture(
        session_factory, png_bytes, BatchStatus.REJECTED
    )
    async with session_factory() as session:
        with pytest.raises(ExportConflictError):
            await build_export_zip(session, store, batch_id=batch_id)


@pytest.mark.asyncio
async def test_approved_export_contains_provenance_manifest(session_factory, png_bytes) -> None:
    batch_id, sku, digest, store = await _export_fixture(
        session_factory, png_bytes, BatchStatus.APPROVED
    )
    async with session_factory() as session:
        content = await build_export_zip(session, store, batch_id=batch_id)

    with ZipFile(BytesIO(content)) as archive:
        manifest = json.loads(archive.read("manifest.json"))
        assert manifest["batch_id"] == str(batch_id)
        assert manifest["product"]["sku"] == sku
        assert manifest["input_asset_sha256"] == [digest]
        assert manifest["assets"][0]["sha256"] == digest
        assert archive.read(manifest["assets"][0]["filename"]) == png_bytes
