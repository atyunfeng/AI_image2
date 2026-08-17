from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from aiimage.assets.models import Asset
from aiimage.assets.storage import ObjectStore
from aiimage.catalog.models import Product, ProductReference, ReferenceView, TruthAnchor
from aiimage.catalog.schemas import ProductCreate


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

