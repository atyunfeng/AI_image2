import hashlib
import json
from io import BytesIO
from uuid import UUID

from PIL import Image
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from aiimage.assets.models import Asset
from aiimage.assets.storage import ObjectStore
from aiimage.editing.evidence import create_edit_evidence
from aiimage.editing.images import compose_image, process_mask
from aiimage.editing.models import EditProject, EditRevision
from aiimage.editing.schemas import EditProjectResponse, EditRevisionResponse
from aiimage.models.domain import Capability
from aiimage.models.models import ModelConfiguration
from aiimage.workflow.models import GenerationBatch, GenerationStep
from aiimage.workflow.queue import QueueHints
from aiimage.workflow.state import BatchStatus, StepStatus


class EditValidationError(ValueError):
    pass


async def create_edit_project(
    session: AsyncSession,
    *,
    source_batch_id: UUID,
    name: str | None,
    user_id: UUID,
) -> EditProject:
    batch = await session.get(GenerationBatch, source_batch_id)
    if batch is None:
        raise EditValidationError("Source batch was not found")
    step = await session.scalar(
        select(GenerationStep)
        .where(GenerationStep.batch_id == batch.id, GenerationStep.output_asset_id.is_not(None))
        .order_by(desc(GenerationStep.attempt_count))
        .limit(1)
    )
    if step is None or step.output_asset_id is None:
        raise EditValidationError("Source batch does not have a generated output")
    project = EditProject(
        name=(name or f"Edit {str(batch.id)[:8]}").strip(),
        product_id=batch.product_id,
        source_batch_id=batch.id,
        source_asset_id=step.output_asset_id,
        created_by_user_id=user_id,
    )
    session.add(project)
    await session.flush()
    root = EditRevision(
        project_id=project.id,
        version=0,
        snapshot_label="原始生成图",
        operation="source",
        status="ready",
        source_asset_id=step.output_asset_id,
        output_asset_id=step.output_asset_id,
        parameters={},
        created_by_user_id=user_id,
    )
    session.add(root)
    await session.commit()
    await session.refresh(project)
    return project


async def next_version(session: AsyncSession, project_id: UUID) -> int:
    current = await session.scalar(
        select(func.max(EditRevision.version)).where(EditRevision.project_id == project_id)
    )
    return int(current or 0) + 1


async def _asset_from_content(
    session: AsyncSession, store: ObjectStore, *, content: bytes, mime_type: str
) -> Asset:
    stored = await store.put(content=content, mime_type=mime_type)
    asset = await session.scalar(select(Asset).where(Asset.sha256 == stored.sha256))
    if asset is None:
        asset = Asset(
            object_key=stored.object_key,
            sha256=stored.sha256,
            size_bytes=stored.size_bytes,
            mime_type=stored.mime_type,
        )
        session.add(asset)
        await session.flush()
    return asset


async def _ready_parent(
    session: AsyncSession, project_id: UUID, parent_revision_id: UUID
) -> tuple[EditProject, EditRevision, Asset]:
    project = await session.get(EditProject, project_id)
    parent = await session.get(EditRevision, parent_revision_id)
    if project is None or parent is None or parent.project_id != project.id:
        raise EditValidationError("Edit project or parent revision was not found")
    if parent.status != "ready" or parent.output_asset_id is None:
        raise EditValidationError("Parent revision is not ready")
    source = await session.get(Asset, parent.output_asset_id)
    if source is None:
        raise EditValidationError("Parent output asset was not found")
    return project, parent, source


async def create_ai_revision(
    session: AsyncSession,
    queue: QueueHints,
    store: ObjectStore,
    *,
    project_id: UUID,
    parent_revision_id: UUID,
    operation: str,
    prompt: str,
    model_configuration_id: UUID,
    parameters: dict,
    mask_content: bytes | None,
    user_id: UUID,
) -> EditRevision:
    project, parent, source = await _ready_parent(session, project_id, parent_revision_id)
    capability_by_operation = {
        "replace": Capability.INPAINT,
        "remove": Capability.INPAINT,
        "replace_background": Capability.INPAINT,
        "outpaint": Capability.OUTPAINT,
        "remove_background": Capability.REMOVE_BACKGROUND,
    }
    capability = capability_by_operation.get(operation)
    if capability is None:
        raise EditValidationError("Unsupported AI edit operation")
    model = await session.get(ModelConfiguration, model_configuration_id)
    if model is None or not model.is_enabled or capability.value not in model.capabilities:
        raise EditValidationError(f"Model does not support enabled {capability.value}")
    with Image.open(BytesIO(await store.get(object_key=source.object_key))) as image:
        source_width, source_height = image.size
    mask_asset = None
    if capability == Capability.INPAINT and not mask_content:
        raise EditValidationError("Inpaint operations require a mask")
    if mask_content:
        processed = process_mask(
            mask_content,
            width=source_width,
            height=source_height,
            invert=bool(parameters.get("invert_mask", False)),
            dilation=int(parameters.get("mask_dilation", 0)),
            feather=float(parameters.get("mask_feather", 0)),
        )
        mask_asset = await _asset_from_content(
            session, store, content=processed, mime_type="image/png"
        )
    width = int(parameters.get("canvas_width", source_width))
    height = int(parameters.get("canvas_height", source_height))
    version = await next_version(session, project.id)
    revision = EditRevision(
        project_id=project.id,
        parent_revision_id=parent.id,
        version=version,
        snapshot_label=parameters.get("snapshot_label") or f"{operation} v{version}",
        operation=operation,
        capability=capability.value,
        status="queued",
        source_asset_id=source.id,
        mask_asset_id=mask_asset.id if mask_asset else None,
        prompt=prompt.strip(),
        parameters=parameters,
        created_by_user_id=user_id,
    )
    session.add(revision)
    await session.flush()
    snapshot = {
        "edit_project_id": str(project.id),
        "edit_revision_id": str(revision.id),
        "edit_source_asset_id": str(source.id),
        "edit_mask_asset_id": str(mask_asset.id) if mask_asset else None,
        "edit_operation": operation,
        "edit_parameters": parameters,
        "reference_ids": [],
    }
    batch = GenerationBatch(
        edit_revision_id=revision.id,
        product_id=project.product_id,
        model_configuration_id=model.id,
        requested_view="edit",
        capability=capability.value,
        mode="strict",
        prompt=prompt.strip(),
        width=width,
        height=height,
        status=BatchStatus.QUEUED.value,
        input_snapshot=snapshot,
        created_by_user_id=user_id,
    )
    session.add(batch)
    await session.flush()
    canonical = json.dumps(snapshot, sort_keys=True) + str(model.id) + prompt
    step = GenerationStep(
        batch_id=batch.id,
        idempotency_key=hashlib.sha256(canonical.encode()).hexdigest(),
    )
    session.add(step)
    await session.commit()
    await queue.publish(step.id)
    return revision


async def create_composed_revision(
    session: AsyncSession,
    store: ObjectStore,
    *,
    project_id: UUID,
    parent_revision_id: UUID,
    parameters: dict,
    logo_content: bytes | None,
    user_id: UUID,
) -> EditRevision:
    project, parent, source = await _ready_parent(session, project_id, parent_revision_id)
    source_content = await store.get(object_key=source.object_key)
    output_content, mime_type = compose_image(
        source_content, parameters=parameters, logo=logo_content
    )
    stored_asset = await _asset_from_content(
        session, store, content=output_content, mime_type=mime_type
    )
    if stored_asset.parent_asset_id is None and stored_asset.id != source.id:
        stored_asset.parent_asset_id = source.id
        stored_asset.derivation_operation = "deterministic_edit"
        stored_asset.derivation_parameters = parameters
    version = await next_version(session, project.id)
    revision = EditRevision(
        project_id=project.id,
        parent_revision_id=parent.id,
        version=version,
        snapshot_label=parameters.get("snapshot_label") or f"版式编辑 v{version}",
        operation="compose",
        status="ready",
        source_asset_id=source.id,
        parameters=parameters,
        created_by_user_id=user_id,
    )
    session.add(revision)
    await session.flush()
    source_batch = await session.get(GenerationBatch, project.source_batch_id)
    if source_batch is None:
        raise EditValidationError("Source batch was not found")
    with Image.open(BytesIO(output_content)) as output_image:
        width, height = output_image.size
    batch = GenerationBatch(
        edit_revision_id=revision.id,
        product_id=project.product_id,
        model_configuration_id=source_batch.model_configuration_id,
        requested_view="edit",
        capability="reference_to_image",
        mode="strict",
        prompt="Deterministic composition",
        width=width,
        height=height,
        status=BatchStatus.REVIEW_PENDING.value,
        input_snapshot={"edit_revision_id": str(revision.id), "deterministic": True},
        created_by_user_id=user_id,
    )
    session.add(batch)
    await session.flush()
    session.add(
        GenerationStep(
            batch_id=batch.id,
            idempotency_key=f"deterministic-{revision.id}",
            status=StepStatus.SUCCEEDED.value,
            provider_request_id=f"deterministic-{revision.id}",
            output_asset_id=stored_asset.id,
        )
    )
    evidence = await create_edit_evidence(
        session,
        store,
        revision=revision,
        output_asset=stored_asset,
        expected_width=width,
        expected_height=height,
    )
    revision.output_asset_id = stored_asset.id
    revision.status = "ready" if evidence.automated_passed else "failed"
    if not evidence.automated_passed:
        batch.status = BatchStatus.FAILED.value
    await session.commit()
    return revision


async def project_response(
    session: AsyncSession, project: EditProject
) -> EditProjectResponse:
    revisions = list(
        (
            await session.scalars(
                select(EditRevision)
                .where(EditRevision.project_id == project.id)
                .order_by(EditRevision.version)
            )
        ).all()
    )
    batches = {
        batch.edit_revision_id: batch.id
        for batch in (
            await session.scalars(
                select(GenerationBatch).where(
                    GenerationBatch.edit_revision_id.in_([revision.id for revision in revisions])
                )
            )
        ).all()
        if batch.edit_revision_id is not None
    }
    return EditProjectResponse(
        id=project.id,
        name=project.name,
        product_id=project.product_id,
        source_batch_id=project.source_batch_id,
        source_asset_id=project.source_asset_id,
        created_at=project.created_at,
        revisions=[
            EditRevisionResponse(
                id=revision.id,
                project_id=revision.project_id,
                parent_revision_id=revision.parent_revision_id,
                version=revision.version,
                snapshot_label=revision.snapshot_label,
                operation=revision.operation,
                capability=revision.capability,
                status=revision.status,
                source_asset_id=revision.source_asset_id,
                mask_asset_id=revision.mask_asset_id,
                output_asset_id=revision.output_asset_id,
                prompt=revision.prompt,
                parameters=revision.parameters,
                batch_id=batches.get(revision.id),
                created_at=revision.created_at,
            )
            for revision in revisions
        ],
    )
