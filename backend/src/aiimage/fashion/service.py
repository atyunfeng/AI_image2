import hashlib
import json
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from aiimage.catalog.models import Product, ProductReference
from aiimage.fashion.compiler import FashionCompilationError, compile_fashion_plan
from aiimage.fashion.models import FashionPlan
from aiimage.fashion.schemas import CreateFashionPlanRequest, FashionPlanResponse
from aiimage.models.models import ModelConfiguration
from aiimage.talent.models import ModelProfile, ModelReference
from aiimage.talent.service import authorization_is_current
from aiimage.workflow.models import GenerationBatch, GenerationStep
from aiimage.workflow.queue import QueueHints
from aiimage.workflow.schemas import BatchDetailResponse, BatchResponse
from aiimage.workflow.state import BatchStatus


async def create_fashion_plan(
    session: AsyncSession,
    queue: QueueHints,
    *,
    payload: CreateFashionPlanRequest,
    user_id: UUID,
) -> FashionPlanResponse:
    product = await session.get(Product, payload.product_id)
    profile = await session.get(ModelProfile, payload.model_profile_id)
    model = await session.get(ModelConfiguration, payload.model_configuration_id)
    if product is None or profile is None or model is None:
        raise FashionCompilationError("Product, model profile, or provider model was not found")
    if not authorization_is_current(profile):
        raise FashionCompilationError("Model profile authorization is not current")
    if not model.is_enabled:
        raise FashionCompilationError("Provider model is disabled")
    product_references = list(
        (
            await session.scalars(
                select(ProductReference).where(ProductReference.product_id == product.id)
            )
        ).all()
    )
    model_references = list(
        (
            await session.scalars(
                select(ModelReference).where(ModelReference.profile_id == profile.id)
            )
        ).all()
    )
    slots = compile_fashion_plan(
        category=product.category,
        requested_outputs=payload.requested_outputs,
        product_views={reference.view for reference in product_references},
        model_views={reference.view for reference in model_references},
        mode=payload.mode,
    )
    missing_capabilities = {
        slot.capability.value for slot in slots if slot.capability.value not in model.capabilities
    }
    if missing_capabilities:
        raise FashionCompilationError(
            "Provider model lacks capabilities: " + ", ".join(sorted(missing_capabilities))
        )
    plan = FashionPlan(
        product_id=product.id,
        model_profile_id=profile.id,
        model_configuration_id=model.id,
        category=product.category,
        mode=payload.mode,
        requested_outputs=[output.value for output in payload.requested_outputs],
        input_snapshot={
            "authorization_status": profile.authorization_status,
            "authorization_expires_on": (
                profile.authorization_expires_on.isoformat()
                if profile.authorization_expires_on
                else None
            ),
            "model_profile_type": profile.profile_type,
        },
        created_by_user_id=user_id,
    )
    session.add(plan)
    await session.flush()
    batches: list[GenerationBatch] = []
    steps: list[GenerationStep] = []
    for slot in slots:
        snapshot = {
            "fashion_plan_id": str(plan.id),
            "fashion_output": slot.output.value,
            "product_id": str(product.id),
            "sku": product.sku,
            "reference_ids": [str(reference.id) for reference in product_references],
            "model_profile_id": str(profile.id),
            "model_reference_ids": [str(reference.id) for reference in model_references],
            "required_product_views": sorted(slot.required_product_views),
            "required_model_views": sorted(slot.required_model_views),
            "authorization": plan.input_snapshot,
            "inferred_view": slot.inferred_view,
            "human_review_checks": [
                "model_identity",
                "anatomy",
                "garment_penetration",
                "product_structure",
                "cross_view_consistency",
            ],
        }
        batch = GenerationBatch(
            fashion_plan_id=plan.id,
            model_profile_id=profile.id,
            product_id=product.id,
            model_configuration_id=model.id,
            requested_view=slot.requested_view,
            capability=slot.capability.value,
            mode=payload.mode,
            prompt=slot.prompt,
            width=1024,
            height=1024,
            status=BatchStatus.QUEUED.value,
            input_snapshot=snapshot,
            created_by_user_id=user_id,
        )
        session.add(batch)
        await session.flush()
        canonical = json.dumps(snapshot, sort_keys=True) + str(model.id) + slot.prompt
        step = GenerationStep(
            batch_id=batch.id,
            idempotency_key=hashlib.sha256(canonical.encode()).hexdigest(),
        )
        session.add(step)
        batches.append(batch)
        steps.append(step)
    await session.commit()
    for step in steps:
        await queue.publish(step.id)
    return FashionPlanResponse(
        id=plan.id,
        product_id=plan.product_id,
        model_profile_id=plan.model_profile_id,
        model_configuration_id=plan.model_configuration_id,
        category=plan.category,
        mode=plan.mode,
        requested_outputs=plan.requested_outputs,
        created_at=plan.created_at,
        batches=[BatchDetailResponse.model_validate(batch) for batch in batches],
    )


async def get_fashion_plan(session: AsyncSession, plan_id: UUID) -> FashionPlanResponse | None:
    plan = await session.get(FashionPlan, plan_id)
    if plan is None:
        return None
    batches = list(
        (
            await session.scalars(
                select(GenerationBatch).where(GenerationBatch.fashion_plan_id == plan.id)
            )
        ).all()
    )
    return FashionPlanResponse(
        id=plan.id,
        product_id=plan.product_id,
        model_profile_id=plan.model_profile_id,
        model_configuration_id=plan.model_configuration_id,
        category=plan.category,
        mode=plan.mode,
        requested_outputs=plan.requested_outputs,
        created_at=plan.created_at,
        batches=[BatchResponse.model_validate(batch) for batch in batches],
    )
