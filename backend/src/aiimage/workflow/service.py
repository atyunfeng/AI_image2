import hashlib
import json
from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from aiimage.catalog.models import Product, ProductReference, TruthAnchor
from aiimage.models.domain import Capability
from aiimage.models.models import ModelConfiguration
from aiimage.templates.models import ProductionPlan, ProductionPlanItem
from aiimage.workflow.models import GenerationBatch, GenerationStep
from aiimage.workflow.queue import QueueHints
from aiimage.workflow.schemas import CreateBatchRequest
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
        snapshot = {
            "product_id": str(product.id),
            "sku": product.sku,
            "reference_ids": [str(reference.id) for reference in references],
            "truth_anchor_id": str(anchor.id) if anchor else None,
            "truth_anchor_version": anchor.version if anchor else None,
            "production_plan_id": str(plan.id),
            "production_plan_item_id": str(item.id),
            "compiler_hash": plan.compiler_hash,
            "pack_versions": plan.compiled_snapshot["packs"],
            "slot": item.slot,
            "slot_rules": item.rules,
            "authoritative_copy": item.authoritative_copy,
        }
        batch = GenerationBatch(
            production_plan_id=plan.id,
            production_plan_item_id=item.id,
            product_id=product.id,
            model_configuration_id=model.id,
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
        key_source = json.dumps(snapshot, sort_keys=True) + str(model.id) + item.prompt
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
