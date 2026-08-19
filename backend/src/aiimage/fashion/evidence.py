from io import BytesIO
from uuid import UUID

from PIL import Image
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from aiimage.assets.models import Asset
from aiimage.assets.storage import ObjectStore
from aiimage.catalog.models import ProductReference
from aiimage.fashion.evidence_models import FashionEvidence
from aiimage.talent.models import ModelProfile, ModelReference
from aiimage.talent.service import authorization_is_current
from aiimage.workflow.models import GenerationBatch


async def create_fashion_evidence(
    session: AsyncSession,
    store: ObjectStore,
    *,
    batch: GenerationBatch,
    output_asset: Asset,
) -> FashionEvidence:
    product_reference_ids = [UUID(value) for value in batch.input_snapshot["reference_ids"]]
    model_reference_ids = [UUID(value) for value in batch.input_snapshot["model_reference_ids"]]
    product_views = set(
        (
            await session.scalars(
                select(ProductReference.view).where(ProductReference.id.in_(product_reference_ids))
            )
        ).all()
    )
    model_views = set(
        (
            await session.scalars(
                select(ModelReference.view).where(ModelReference.id.in_(model_reference_ids))
            )
        ).all()
    )
    required_product = set(batch.input_snapshot.get("required_product_views", []))
    required_model = set(batch.input_snapshot.get("required_model_views", []))
    product_satisfied = bool(required_product.intersection(product_views))
    model_satisfied = not required_model or bool(required_model.intersection(model_views))
    profile = await session.get(ModelProfile, batch.model_profile_id)
    authorization_current = profile is not None and authorization_is_current(profile)
    content = await store.get(object_key=output_asset.object_key)
    with Image.open(BytesIO(content)) as image:
        dimensions_match = image.size == (batch.width, batch.height)
        measured = {"width": image.width, "height": image.height, "format": image.format}
    inferred = bool(batch.input_snapshot.get("inferred_view"))
    checks = {
        "authorization_current": authorization_current,
        "product_reference_satisfied": product_satisfied or inferred,
        "model_reference_satisfied": model_satisfied,
        "dimensions_match": dimensions_match,
        "inferred_view_labeled": not inferred or batch.mode == "creative",
    }
    evidence = FashionEvidence(
        batch_id=batch.id,
        output_asset_id=output_asset.id,
        capability=batch.capability,
        inferred_view=inferred,
        automated_passed=all(checks.values()),
        checks=checks,
        measured={**measured, "semantic_quality": "human_review_required"},
        human_review_checks=batch.input_snapshot.get("human_review_checks", []),
    )
    session.add(evidence)
    await session.flush()
    return evidence


async def latest_fashion_evidence(
    session: AsyncSession, batch_id: UUID
) -> FashionEvidence | None:
    return await session.scalar(
        select(FashionEvidence)
        .where(FashionEvidence.batch_id == batch_id)
        .order_by(desc(FashionEvidence.created_at))
        .limit(1)
    )
