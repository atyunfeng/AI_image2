from io import BytesIO
from uuid import UUID

from PIL import Image
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from aiimage.assets.models import Asset
from aiimage.assets.storage import ObjectStore
from aiimage.editing.models import EditEvidence, EditRevision


async def create_edit_evidence(
    session: AsyncSession,
    store: ObjectStore,
    *,
    revision: EditRevision,
    output_asset: Asset,
    expected_width: int,
    expected_height: int,
) -> EditEvidence:
    content = await store.get(object_key=output_asset.object_key)
    with Image.open(BytesIO(content)) as image:
        measured = {"width": image.width, "height": image.height, "format": image.format}
    checks = {
        "source_recorded": revision.source_asset_id is not None,
        "mask_recorded_when_required": revision.capability not in {"inpaint"} or revision.mask_asset_id is not None,
        "output_dimensions": measured["width"] == expected_width and measured["height"] == expected_height,
        "immutable_derivation": revision.output_asset_id is None,
    }
    evidence = EditEvidence(
        revision_id=revision.id,
        output_asset_id=output_asset.id,
        automated_passed=all(checks.values()),
        checks=checks,
        measured=measured,
        human_review_checks=[
            "product_identity",
            "edit_boundary",
            "visual_artifacts",
            "authoritative_copy",
            "platform_compliance",
        ],
    )
    session.add(evidence)
    await session.flush()
    return evidence


async def latest_edit_evidence(
    session: AsyncSession, revision_id: UUID
) -> EditEvidence | None:
    return await session.scalar(
        select(EditEvidence)
        .where(EditEvidence.revision_id == revision_id)
        .order_by(desc(EditEvidence.created_at))
        .limit(1)
    )
