from uuid import uuid4

from sqlalchemy import select

from aiimage.assets.models import Asset
from aiimage.assets.storage import InMemoryObjectStore
from aiimage.auth.models import Role
from aiimage.auth.service import create_user
from aiimage.catalog.models import Product
from aiimage.editing.models import EditEvidence, EditProject, EditRevision
from aiimage.models.domain import Capability, GenerationRequest
from aiimage.models.models import ModelConfiguration
from aiimage.providers.mock import MockProvider
from aiimage.worker.executor import WorkerContext, execute_step
from aiimage.workflow.models import GenerationBatch, GenerationStep
from aiimage.workflow.state import BatchStatus


class RecordingEditProvider:
    def __init__(self) -> None:
        self.request: GenerationRequest | None = None
        self.mock = MockProvider()

    async def generate(self, request: GenerationRequest):
        self.request = request
        return await self.mock.generate(request)


class EditRegistry:
    def __init__(self, provider: RecordingEditProvider) -> None:
        self.provider = provider

    def get(self, configuration):
        return self.provider


async def test_inpaint_receives_exact_source_and_mask_and_records_evidence(
    session_factory, png_bytes
) -> None:
    store = InMemoryObjectStore()
    stored = await store.put(content=png_bytes, mime_type="image/png")
    async with session_factory() as session:
        user = await create_user(
            session,
            email=f"edit-worker-{uuid4()}@aiimage.local",
            password="Edit-Worker-2026",
            roles={Role.OPERATOR},
        )
        source = Asset(
            object_key=stored.object_key,
            sha256=stored.sha256,
            size_bytes=stored.size_bytes,
            mime_type=stored.mime_type,
        )
        product = Product(
            sku=f"EDIT-WORKER-{uuid4()}",
            name="Edit worker product",
            category="apparel",
            created_by_user_id=user.id,
        )
        model = ModelConfiguration(
            name="edit-mock",
            provider="mock",
            model_id="mock-inpaint",
            capabilities=[Capability.INPAINT.value],
            created_by_user_id=user.id,
        )
        session.add_all([source, product, model])
        await session.flush()
        source_batch = GenerationBatch(
            product_id=product.id,
            model_configuration_id=model.id,
            requested_view="front",
            prompt="source",
            width=64,
            height=64,
            status=BatchStatus.REVIEW_PENDING.value,
            input_snapshot={},
            created_by_user_id=user.id,
        )
        session.add(source_batch)
        await session.flush()
        project = EditProject(
            name="Edit",
            product_id=product.id,
            source_batch_id=source_batch.id,
            source_asset_id=source.id,
            created_by_user_id=user.id,
        )
        session.add(project)
        await session.flush()
        revision = EditRevision(
            project_id=project.id,
            version=1,
            operation="replace",
            capability=Capability.INPAINT.value,
            status="queued",
            source_asset_id=source.id,
            mask_asset_id=source.id,
            prompt="replace the selected region",
            parameters={},
            created_by_user_id=user.id,
        )
        session.add(revision)
        await session.flush()
        batch = GenerationBatch(
            edit_revision_id=revision.id,
            product_id=product.id,
            model_configuration_id=model.id,
            requested_view="edit",
            capability=Capability.INPAINT.value,
            mode="strict",
            prompt="replace the selected region",
            width=64,
            height=64,
            status=BatchStatus.QUEUED.value,
            input_snapshot={
                "edit_source_asset_id": str(source.id),
                "edit_mask_asset_id": str(source.id),
                "edit_operation": "replace",
                "edit_parameters": {"mask_feather": 2},
                "reference_ids": [],
            },
            created_by_user_id=user.id,
        )
        session.add(batch)
        await session.flush()
        step = GenerationStep(batch_id=batch.id, idempotency_key=f"edit-{uuid4()}")
        session.add(step)
        await session.commit()
        step_id, batch_id, revision_id = step.id, batch.id, revision.id

    provider = RecordingEditProvider()
    context = WorkerContext(
        session_factory=session_factory,
        object_store=store,
        provider_registry=EditRegistry(provider),
    )
    assert await execute_step(step_id, "edit-worker", context)
    assert provider.request is not None
    assert provider.request.capability == Capability.INPAINT
    assert provider.request.parameters["edit_reference_roles"] == ["source", "mask"]
    assert len(provider.request.reference_images) == 2
    async with session_factory() as session:
        batch = await session.get(GenerationBatch, batch_id)
        revision = await session.get(EditRevision, revision_id)
        evidence = await session.scalar(
            select(EditEvidence).where(EditEvidence.revision_id == revision_id)
        )
        assert batch.status == BatchStatus.REVIEW_PENDING.value
        assert revision.status == "ready"
        assert revision.output_asset_id is not None
        assert evidence.automated_passed
