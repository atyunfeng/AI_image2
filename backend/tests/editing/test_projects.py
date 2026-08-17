from sqlalchemy import select

from aiimage.assets.models import Asset
from aiimage.assets.storage import InMemoryObjectStore
from aiimage.auth.models import Role
from aiimage.auth.service import create_user
from aiimage.catalog.models import Product
from aiimage.editing.models import EditEvidence, EditRevision
from aiimage.editing.service import (
    EditValidationError,
    create_composed_revision,
    create_edit_project,
    project_response,
)
from aiimage.models.models import ModelConfiguration
from aiimage.workflow.models import GenerationBatch, GenerationStep
from aiimage.workflow.schemas import BatchDetailResponse
from aiimage.workflow.state import BatchStatus, StepStatus


async def test_create_project_starts_with_immutable_source_revision(session_factory) -> None:
    async with session_factory() as session:
        user = await create_user(
            session,
            email="editor@example.com",
            password="Editing-Password-2026",
            roles={Role.OPERATOR},
        )
        product = Product(sku="EDIT-1", name="Editable coat", category="apparel", created_by_user_id=user.id)
        model = ModelConfiguration(
            name="Mock edit",
            provider="mock",
            model_id="mock-edit",
            capabilities=["inpaint"],
            created_by_user_id=user.id,
        )
        asset = Asset(object_key="sha256/source", sha256="a" * 64, size_bytes=16, mime_type="image/png")
        session.add_all([product, model, asset])
        await session.flush()
        batch = GenerationBatch(
            product_id=product.id,
            model_configuration_id=model.id,
            requested_view="front",
            prompt="source",
            width=1024,
            height=1024,
            status=BatchStatus.REVIEW_PENDING.value,
            input_snapshot={},
            created_by_user_id=user.id,
        )
        session.add(batch)
        await session.flush()
        session.add(
            GenerationStep(
                batch_id=batch.id,
                idempotency_key="source-step",
                status=StepStatus.SUCCEEDED.value,
                output_asset_id=asset.id,
            )
        )
        await session.commit()

        project = await create_edit_project(
            session, source_batch_id=batch.id, name="秋季主图微调", user_id=user.id
        )
        response = await project_response(session, project)

        assert response.source_asset_id == asset.id
        assert len(response.revisions) == 1
        assert response.revisions[0].operation == "source"
        assert response.revisions[0].output_asset_id == asset.id
        assert await session.get(EditRevision, response.revisions[0].id) is not None


async def test_project_rejects_batch_without_output(session_factory) -> None:
    async with session_factory() as session:
        user = await create_user(
            session,
            email="empty-editor@example.com",
            password="Editing-Password-2026",
            roles={Role.OPERATOR},
        )
        product = Product(sku="EDIT-EMPTY", name="Empty", category="other", created_by_user_id=user.id)
        model = ModelConfiguration(
            name="Mock",
            provider="mock",
            model_id="mock",
            capabilities=["inpaint"],
            created_by_user_id=user.id,
        )
        session.add_all([product, model])
        await session.flush()
        batch = GenerationBatch(
            product_id=product.id,
            model_configuration_id=model.id,
            requested_view="front",
            prompt="source",
            width=1024,
            height=1024,
            status=BatchStatus.QUEUED.value,
            input_snapshot={},
            created_by_user_id=user.id,
        )
        session.add(batch)
        await session.commit()

        try:
            await create_edit_project(
                session, source_batch_id=batch.id, name=None, user_id=user.id
            )
        except EditValidationError as error:
            assert "does not have" in str(error)
        else:
            raise AssertionError("Expected an output validation error")


async def test_composed_revision_creates_derived_asset_evidence_and_review_batch(
    session_factory, png_bytes
) -> None:
    store = InMemoryObjectStore()
    stored = await store.put(content=png_bytes, mime_type="image/png")
    async with session_factory() as session:
        user = await create_user(
            session,
            email="compose-editor@example.com",
            password="Editing-Password-2026",
            roles={Role.OPERATOR},
        )
        product = Product(
            sku="EDIT-COMPOSE",
            name="Compose",
            category="apparel",
            created_by_user_id=user.id,
        )
        model = ModelConfiguration(
            name="Mock",
            provider="mock",
            model_id="mock",
            capabilities=["reference_to_image"],
            created_by_user_id=user.id,
        )
        asset = Asset(
            object_key=stored.object_key,
            sha256=stored.sha256,
            size_bytes=stored.size_bytes,
            mime_type=stored.mime_type,
        )
        session.add_all([product, model, asset])
        await session.flush()
        batch = GenerationBatch(
            product_id=product.id,
            model_configuration_id=model.id,
            requested_view="front",
            prompt="source",
            width=8,
            height=8,
            status=BatchStatus.REVIEW_PENDING.value,
            input_snapshot={},
            created_by_user_id=user.id,
        )
        session.add(batch)
        await session.flush()
        session.add(
            GenerationStep(
                batch_id=batch.id,
                idempotency_key="compose-source",
                status=StepStatus.SUCCEEDED.value,
                output_asset_id=asset.id,
            )
        )
        await session.commit()
        project = await create_edit_project(
            session, source_batch_id=batch.id, name="Compose project", user_id=user.id
        )
        root = await session.scalar(
            select(EditRevision).where(EditRevision.project_id == project.id)
        )
        revision = await create_composed_revision(
            session,
            store,
            project_id=project.id,
            parent_revision_id=root.id,
            parameters={"canvas_width": 96, "canvas_height": 80, "scale": 2},
            logo_content=None,
            user_id=user.id,
        )
        evidence = await session.scalar(
            select(EditEvidence).where(EditEvidence.revision_id == revision.id)
        )
        edit_batch = await session.scalar(
            select(GenerationBatch).where(GenerationBatch.edit_revision_id == revision.id)
        )
        assert revision.output_asset_id != asset.id
        assert revision.status == "ready"
        assert evidence.automated_passed
        assert edit_batch.status == BatchStatus.REVIEW_PENDING.value


def test_batch_response_accepts_edit_view() -> None:
    response = BatchDetailResponse(
        id="00000000-0000-0000-0000-000000000001",
        product_id="00000000-0000-0000-0000-000000000002",
        model_configuration_id="00000000-0000-0000-0000-000000000003",
        requested_view="edit",
        capability="inpaint",
        mode="strict",
        status=BatchStatus.REVIEW_PENDING,
        prompt="edit",
        width=1024,
        height=1024,
    )
    assert response.requested_view == "edit"
