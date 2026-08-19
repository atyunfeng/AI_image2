from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Response,
    UploadFile,
    status,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from aiimage.api.dependencies import get_session
from aiimage.assets.models import Asset
from aiimage.assets.storage import ObjectStore, get_object_store
from aiimage.auth.dependencies import require_roles
from aiimage.auth.models import Role, User
from aiimage.catalog.models import Product, ProductReference, ReferenceView, TruthAnchor
from aiimage.catalog.schemas import (
    ProductCreate,
    ProductDetailResponse,
    ProductReferenceResponse,
    ProductResponse,
    ProductUpdate,
    TruthAnchorCreate,
    TruthAnchorResponse,
)
from aiimage.catalog.service import (
    DuplicateSkuError,
    add_reference,
    analyze_truth_anchor,
    archive_product,
    create_product,
    create_truth_anchor,
    get_product_history,
    update_product,
)

router = APIRouter(prefix="/products", tags=["products"])
CatalogUser = Annotated[
    User,
    Depends(require_roles(Role.ADMIN, Role.OPERATOR, Role.DESIGNER)),
]


@router.get("", response_model=list[ProductResponse])
async def list_products(
    user: CatalogUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
    query: Annotated[str | None, Query(max_length=100)] = None,
) -> list[ProductResponse]:
    del user
    statement = select(Product).where(Product.archived_at.is_(None))
    if query:
        normalized = f"%{query.strip()}%"
        statement = statement.where(
            Product.sku.ilike(normalized) | Product.name.ilike(normalized)
        )
    products = list(
        (
            await session.scalars(
                statement.order_by(Product.created_at.desc()).offset(offset).limit(limit)
            )
        ).all()
    )
    return [ProductResponse.model_validate(product) for product in products]


@router.get("/{product_id}", response_model=ProductDetailResponse)
async def get_product(
    product_id: UUID,
    user: CatalogUser,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ProductDetailResponse:
    del user
    product = await session.get(Product, product_id)
    if product is None or product.archived_at is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    references = list(
        (
            await session.scalars(
                select(ProductReference).where(ProductReference.product_id == product.id)
            )
        ).all()
    )
    assets = {
        asset.id: asset
        for asset in (
            await session.scalars(
                select(Asset).where(Asset.id.in_([reference.asset_id for reference in references]))
            )
        ).all()
    }
    anchors = list(
        (
            await session.scalars(
                select(TruthAnchor)
                .where(TruthAnchor.product_id == product.id)
                .order_by(TruthAnchor.version.desc())
            )
        ).all()
    )
    return ProductDetailResponse(
        id=product.id,
        sku=product.sku,
        name=product.name,
        category=product.category,
        brand=product.brand,
        references=[
            ProductReferenceResponse(
                id=reference.id,
                asset_id=reference.asset_id,
                view=reference.view,
                sha256=assets[reference.asset_id].sha256,
                mime_type=assets[reference.asset_id].mime_type,
                size_bytes=assets[reference.asset_id].size_bytes,
            )
            for reference in references
        ],
        latest_truth_anchor=TruthAnchorResponse.model_validate(anchors[0]) if anchors else None,
        truth_anchors=[TruthAnchorResponse.model_validate(anchor) for anchor in anchors],
        history=await get_product_history(session, product.id),
    )


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product_endpoint(
    payload: ProductCreate,
    user: CatalogUser,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ProductResponse:
    try:
        product = await create_product(session, payload=payload, user_id=user.id)
    except DuplicateSkuError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="SKU already exists") from error
    return ProductResponse.model_validate(product)


@router.patch("/{product_id}", response_model=ProductResponse)
async def update_product_endpoint(
    product_id: UUID,
    payload: ProductUpdate,
    user: CatalogUser,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ProductResponse:
    product = await session.get(Product, product_id)
    if product is None or product.archived_at is not None:
        raise HTTPException(status_code=404, detail="Product not found")
    return ProductResponse.model_validate(
        await update_product(session, product=product, payload=payload, user_id=user.id)
    )


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def archive_product_endpoint(
    product_id: UUID,
    user: CatalogUser,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Response:
    product = await session.get(Product, product_id)
    if product is None or product.archived_at is not None:
        raise HTTPException(status_code=404, detail="Product not found")
    await archive_product(session, product=product, user_id=user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{product_id}/truth-anchors",
    response_model=TruthAnchorResponse,
    status_code=status.HTTP_201_CREATED,
)
async def save_truth_anchor(
    product_id: UUID,
    payload: TruthAnchorCreate,
    user: CatalogUser,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> TruthAnchorResponse:
    product = await session.get(Product, product_id)
    if product is None or product.archived_at is not None:
        raise HTTPException(status_code=404, detail="Product not found")
    anchor = await create_truth_anchor(
        session, product=product, document=payload.document, user_id=user.id
    )
    return TruthAnchorResponse.model_validate(anchor)


@router.post(
    "/{product_id}/truth-anchors/analyze",
    response_model=TruthAnchorResponse,
    status_code=status.HTTP_201_CREATED,
)
async def analyze_product_truth_anchor(
    product_id: UUID,
    user: CatalogUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    store: Annotated[ObjectStore, Depends(get_object_store)],
) -> TruthAnchorResponse:
    product = await session.get(Product, product_id)
    if product is None or product.archived_at is not None:
        raise HTTPException(status_code=404, detail="Product not found")
    try:
        anchor = await analyze_truth_anchor(session, store, product=product, user_id=user.id)
    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return TruthAnchorResponse.model_validate(anchor)


@router.post(
    "/{product_id}/references",
    response_model=ProductReferenceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_reference(
    product_id: UUID,
    user: CatalogUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    store: Annotated[ObjectStore, Depends(get_object_store)],
    view: Annotated[ReferenceView, Form()],
    file: Annotated[UploadFile, File()],
) -> ProductReferenceResponse:
    del user
    try:
        reference, asset = await add_reference(
            session,
            store,
            product_id=product_id,
            view=view,
            content=await file.read(),
            mime_type=file.content_type or "application/octet-stream",
        )
    except LookupError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found") from error
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error
    return ProductReferenceResponse(
        id=reference.id,
        asset_id=asset.id,
        view=ReferenceView(reference.view),
        sha256=asset.sha256,
        mime_type=asset.mime_type,
        size_bytes=asset.size_bytes,
    )
