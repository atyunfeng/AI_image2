from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from aiimage.api.dependencies import get_session
from aiimage.assets.storage import ObjectStore, get_object_store
from aiimage.auth.dependencies import require_roles
from aiimage.auth.models import Role, User
from aiimage.catalog.models import ReferenceView
from aiimage.catalog.schemas import ProductCreate, ProductReferenceResponse, ProductResponse
from aiimage.catalog.service import DuplicateSkuError, add_reference, create_product

router = APIRouter(prefix="/products", tags=["products"])
CatalogUser = Annotated[
    User,
    Depends(require_roles(Role.ADMIN, Role.OPERATOR, Role.DESIGNER)),
]


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

