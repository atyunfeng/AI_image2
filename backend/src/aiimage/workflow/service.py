import hashlib
import json
from uuid import UUID, uuid4

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from aiimage.audit.service import record_audit_event
from aiimage.catalog.models import Product, ProductReference, TruthAnchor
from aiimage.models.domain import Capability
from aiimage.models.models import ModelConfiguration
from aiimage.templates.models import ProductionPlan, ProductionPlanItem
from aiimage.workflow.models import GenerationBatch, GenerationStep
from aiimage.workflow.queue import QueueHints
from aiimage.workflow.schemas import CloneBatchRequest, CreateBatchRequest
from aiimage.workflow.state import BatchStatus


class BatchValidationError(RuntimeError):
    pass


async def create_batch(
    session: AsyncSession,
    queue: QueueHints,
    *,
    payload: CreateBatchRequest,
    user_id: UUID,
) -> GenerationBatch:
    product = await session.get(Product, payload.product_id)
    model = await session.get(ModelConfiguration, payload.model_configuration_id)
    if product is None or model is None:
        raise BatchValidationError("Product or model configuration not found")
    if Capability.REFERENCE_TO_IMAGE.value not in model.capabilities:
        raise BatchValidationError("Model does not support reference_to_image")
    references = list(
        (
            await session.scalars(
                select(ProductReference).where(ProductReference.product_id == product.id)
            )
        ).all()
    )
    if (
        payload.mode == "strict"
        and payload.requested_view.value in {"side", "back"}
        and payload.requested_view.value not in {reference.view for reference in references}
    ):
        raise BatchValidationError(
            f"Strict mode requires a {payload.requested_view.value} reference"
        )
    anchor = await session.scalar(
        select(TruthAnchor)
        .where(TruthAnchor.product_id == product.id)
        .order_by(desc(TruthAnchor.version))
        .limit(1)
    )
    snapshot = {
        "product_id": str(product.id),
        "sku": product.sku,
        "reference_ids": [str(reference.id) for reference in references],
        "truth_anchor_id": str(anchor.id) if anchor else None,
        "truth_anchor_version": anchor.version if anchor else None,
    }
    batch = GenerationBatch(
        product_id=product.id,
        model_configuration_id=model.id,
        requested_view=payload.requested_view.value,
        mode=payload.mode,
        prompt=payload.prompt,
        width=payload.width,
        height=payload.height,
        status=BatchStatus.QUEUED.value,
        input_snapshot=snapshot,
        created_by_user_id=user_id,
    )
    session.add(batch)
    await session.flush()
    key_source = json.dumps(snapshot, sort_keys=True) + str(model.id) + payload.prompt
    step = GenerationStep(
        batch_id=batch.id,
        idempotency_key=hashlib.sha256(key_source.encode()).hexdigest(),
    )
    session.add(step)
    await session.commit()
    await queue.publish(step.id)
    return batch


async def execute_production_plan(
    session: AsyncSession,
    queue: QueueHints,
    *,
    plan_id: UUID,
    model_configuration_id: UUID,
    user_id: UUID,
) -> list[GenerationBatch]:
    plan = await session.get(ProductionPlan, plan_id)
    model = await session.get(ModelConfiguration, model_configuration_id)
    if plan is None or model is None:
        raise BatchValidationError("Production plan or model configuration not found")
    if Capability.REFERENCE_TO_IMAGE.value not in model.capabilities or not model.is_enabled:
        raise BatchValidationError("Model does not support enabled reference_to_image")
    existing = await session.scalar(
        select(GenerationBatch.id).where(GenerationBatch.production_plan_id == plan.id).limit(1)
    )
    if existing is not None:
        raise BatchValidationError("Production plan has already been executed")
    product = await session.get(Product, plan.product_id)
    if product is None:
        raise BatchValidationError("Production plan product not found")
    items = list(
        (
            await session.scalars(
                select(ProductionPlanItem)
                .where(ProductionPlanItem.plan_id == plan.id)
                .order_by(ProductionPlanItem.position)
            )
        ).all()
    )
    references = list(
        (
            await session.scalars(
                select(ProductReference).where(ProductReference.product_id == product.id)
            )
        ).all()
    )
    anchor = await session.scalar(
        select(TruthAnchor)
        .where(TruthAnchor.product_id == product.id)
        .order_by(desc(TruthAnchor.version))
        .limit(1)
    )
    batches: list[GenerationBatch] = []
    steps: list[GenerationStep] = []
    for item in items:
        selected_model = model
        if item.model_configuration_id:
            item_model = await session.get(ModelConfiguration, item.model_configuration_id)
            if item_model is None:
                raise BatchValidationError(f"Model override for {item.label} was not found")
            selected_model = item_model
        if (
            not selected_model.is_enabled
            or Capability.REFERENCE_TO_IMAGE.value not in selected_model.capabilities
        ):
            raise BatchValidationError(f"Model override for {item.label} is not eligible")
        selected_reference_ids = set(item.reference_ids or [])
        selected_references = [
            reference
            for reference in references
            if not selected_reference_ids or str(reference.id) in selected_reference_ids
        ]
        if selected_reference_ids and len(selected_references) != len(selected_reference_ids):
            raise BatchValidationError(f"Reference override for {item.label} is invalid")
        if (
            plan.mode == "strict"
            and item.requested_view in {"side", "back"}
            and item.requested_view not in {reference.view for reference in selected_references}
        ):
            raise BatchValidationError(
                f"Strict mode requires a {item.requested_view} reference for {item.label}"
            )
        snapshot = {
            "product_id": str(product.id),
            "sku": product.sku,
            "reference_ids": [str(reference.id) for reference in selected_references],
            "truth_anchor_id": str(anchor.id) if anchor else None,
            "truth_anchor_version": anchor.version if anchor else None,
            "production_plan_id": str(plan.id),
            "production_plan_item_id": str(item.id),
            "compiler_hash": plan.compiler_hash,
            "pack_versions": plan.compiled_snapshot["packs"],
            "slot": item.slot,
            "slot_rules": item.rules,
            "authoritative_copy": item.authoritative_copy,
            "provider_parameters": item.provider_parameters,
        }
        batch = GenerationBatch(
            production_plan_id=plan.id,
            production_plan_item_id=item.id,
            product_id=product.id,
            model_configuration_id=selected_model.id,
            requested_view=item.requested_view,
            mode=plan.mode,
            prompt=item.prompt,
            width=item.width,
            height=item.height,
            status=BatchStatus.QUEUED.value,
            input_snapshot=snapshot,
            created_by_user_id=user_id,
        )
        session.add(batch)
        await session.flush()
        key_source = json.dumps(snapshot, sort_keys=True) + str(selected_model.id) + item.prompt
        step = GenerationStep(
            batch_id=batch.id,
            idempotency_key=hashlib.sha256(key_source.encode()).hexdigest(),
        )
        session.add(step)
        batches.append(batch)
        steps.append(step)
    await session.commit()
    for step in steps:
        await queue.publish(step.id)
    return batches


async def clone_batch(
    session: AsyncSession,
    queue: QueueHints,
    *,
    batch_id: UUID,
    payload: CloneBatchRequest,
    user_id: UUID,
    retry: bool,
) -> GenerationBatch:
    source = await session.get(GenerationBatch, batch_id)
    if source is None:
        raise LookupError(batch_id)
    if retry and source.status not in {
        BatchStatus.FAILED.value,
        BatchStatus.REJECTED.value,
        BatchStatus.CANCELED.value,
    }:
        raise BatchValidationError("Only failed, rejected, or canceled batches can be retried")
    model_id = payload.model_configuration_id or source.model_configuration_id
    model = await session.get(ModelConfiguration, model_id)
    if (
        model is None
        or not model.is_enabled
        or source.capability not in model.capabilities
    ):
        raise BatchValidationError("Selected model does not support this batch capability")
    prompt = payload.prompt or source.prompt
    width = payload.width or source.width
    height = payload.height or source.height
    snapshot = {
        **source.input_snapshot,
        "source_batch_id": str(source.id),
        "clone_kind": "retry" if retry else "duplicate",
        "provider_parameters": source.input_snapshot.get("provider_parameters", {}),
    }
    batch = GenerationBatch(
        source_batch_id=source.id,
        product_id=source.product_id,
        model_configuration_id=model_id,
        requested_view=source.requested_view,
        capability=source.capability,
        mode=source.mode,
        prompt=prompt,
        width=width,
        height=height,
        status=BatchStatus.QUEUED.value,
        input_snapshot=snapshot,
        created_by_user_id=user_id,
    )
    session.add(batch)
    await session.flush()
    nonce = str(uuid4())
    key_source = json.dumps(snapshot, sort_keys=True) + str(model_id) + prompt + nonce
    step = GenerationStep(
        batch_id=batch.id,
        idempotency_key=hashlib.sha256(key_source.encode()).hexdigest(),
    )
    session.add(step)
    await record_audit_event(
        session,
        event_type=f"batch.{'retried' if retry else 'duplicated'}",
        actor_user_id=user_id,
        details={"source_batch_id": str(source.id), "batch_id": str(batch.id)},
    )
    await session.commit()
    await queue.publish(step.id)
    return batch
