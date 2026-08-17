from datetime import UTC, datetime
from io import BytesIO
from uuid import UUID

from PIL import Image, ImageStat
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from aiimage.assets.models import Asset
from aiimage.assets.storage import ObjectStore
from aiimage.audit.service import record_audit_event
from aiimage.catalog.models import Product, ProductReference, ReferenceView, TruthAnchor
from aiimage.catalog.schemas import ProductCreate, ProductHistoryResponse, ProductUpdate
from aiimage.editing.models import EditProject
from aiimage.export.models import ExportRecord
from aiimage.review.models import ReviewDecision
from aiimage.workflow.models import GenerationBatch


class DuplicateSkuError(RuntimeError):
    pass


async def create_product(
    session: AsyncSession,
    *,
    payload: ProductCreate,
    user_id: UUID,
) -> Product:
    sku = payload.sku.strip().upper()
    existing = await session.scalar(select(Product.id).where(Product.sku == sku))
    if existing is not None:
        raise DuplicateSkuError(sku)
    product = Product(
        sku=sku,
        name=payload.name.strip(),
        category=payload.category.value,
        brand=payload.brand.strip() if payload.brand else None,
        created_by_user_id=user_id,
    )
    session.add(product)
    await session.flush()
    session.add(
        TruthAnchor(
            product_id=product.id,
            version=1,
            document={},
            created_by_user_id=user_id,
        )
    )
    await session.commit()
    return product


async def update_product(
    session: AsyncSession,
    *,
    product: Product,
    payload: ProductUpdate,
    user_id: UUID,
) -> Product:
    changes: dict[str, str | None] = {}
    fields = payload.model_fields_set
    if "name" in fields and payload.name is not None:
        product.name = payload.name.strip()
        changes["name"] = product.name
    if "category" in fields and payload.category is not None:
        product.category = payload.category.value
        changes["category"] = product.category
    if "brand" in fields:
        product.brand = payload.brand.strip() if payload.brand else None
        changes["brand"] = product.brand
    await record_audit_event(
        session,
        event_type="product.updated",
        actor_user_id=user_id,
        details={"product_id": str(product.id), "changes": changes},
    )
    await session.commit()
    return product


async def archive_product(session: AsyncSession, *, product: Product, user_id: UUID) -> None:
    product.archived_at = datetime.now(UTC)
    await record_audit_event(
        session,
        event_type="product.archived",
        actor_user_id=user_id,
        details={"product_id": str(product.id), "sku": product.sku},
    )
    await session.commit()


async def create_truth_anchor(
    session: AsyncSession,
    *,
    product: Product,
    document: dict,
    user_id: UUID,
) -> TruthAnchor:
    latest = await session.scalar(
        select(func.max(TruthAnchor.version)).where(TruthAnchor.product_id == product.id)
    )
    anchor = TruthAnchor(
        product_id=product.id,
        version=(latest or 0) + 1,
        document=document,
        created_by_user_id=user_id,
    )
    session.add(anchor)
    await record_audit_event(
        session,
        event_type="product.truth_anchor.created",
        actor_user_id=user_id,
        details={"product_id": str(product.id), "version": anchor.version},
    )
    await session.commit()
    await session.refresh(anchor)
    return anchor


async def analyze_truth_anchor(
    session: AsyncSession,
    store: ObjectStore,
    *,
    product: Product,
    user_id: UUID,
) -> TruthAnchor:
    references = list(
        (
            await session.execute(
                select(ProductReference, Asset)
                .join(Asset, Asset.id == ProductReference.asset_id)
                .where(ProductReference.product_id == product.id)
                .order_by(ProductReference.view, ProductReference.id)
            )
        ).all()
    )
    if not references:
        raise ValueError("At least one product reference is required")
    analyzed: list[dict] = []
    weighted = [0.0, 0.0, 0.0]
    for reference, asset in references:
        content = await store.get(object_key=asset.object_key)
        with Image.open(BytesIO(content)) as image:
            rgb = image.convert("RGB")
            mean = ImageStat.Stat(rgb.resize((32, 32))).mean[:3]
            analyzed.append(
                {
                    "reference_id": str(reference.id),
                    "view": reference.view,
                    "width": image.width,
                    "height": image.height,
                    "sha256": asset.sha256,
                    "mean_color": "#" + "".join(f"{round(channel):02x}" for channel in mean),
                }
            )
            for index, value in enumerate(mean):
                weighted[index] += value
    dominant = "#" + "".join(
        f"{round(value / len(references)):02x}" for value in weighted
    )
    return await create_truth_anchor(
        session,
        product=product,
        document={
            "source": "deterministic_reference_analysis",
            "reference_count": len(references),
            "dominant_color": dominant,
            "references": analyzed,
        },
        user_id=user_id,
    )


async def get_product_history(session: AsyncSession, product_id: UUID) -> ProductHistoryResponse:
    generations = await session.scalar(
        select(func.count(GenerationBatch.id)).where(GenerationBatch.product_id == product_id)
    )
    edits = await session.scalar(
        select(func.count(EditProject.id)).where(EditProject.product_id == product_id)
    )
    reviews = await session.scalar(
        select(func.count(ReviewDecision.id))
        .join(GenerationBatch, GenerationBatch.id == ReviewDecision.batch_id)
        .where(GenerationBatch.product_id == product_id)
    )
    exports = await session.scalar(
        select(func.count(ExportRecord.id))
        .join(GenerationBatch, GenerationBatch.id == ExportRecord.batch_id)
        .where(GenerationBatch.product_id == product_id)
    )
    return ProductHistoryResponse(
        generations=generations or 0,
        edits=edits or 0,
        reviews=reviews or 0,
        exports=exports or 0,
    )


async def add_reference(
    session: AsyncSession,
    store: ObjectStore,
    *,
    product_id: UUID,
    view: ReferenceView,
    content: bytes,
    mime_type: str,
) -> tuple[ProductReference, Asset]:
    if await session.get(Product, product_id) is None:
        raise LookupError(product_id)
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
    reference = ProductReference(product_id=product_id, asset_id=asset.id, view=view.value)
    session.add(reference)
    await session.commit()
    return reference, asset
