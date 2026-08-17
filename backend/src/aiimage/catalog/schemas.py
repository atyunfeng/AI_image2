from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from aiimage.catalog.models import ProductCategory, ReferenceView


class ProductCreate(BaseModel):
    sku: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=255)
    category: ProductCategory


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    sku: str
    name: str
    category: ProductCategory


class ProductReferenceResponse(BaseModel):
    id: UUID
    asset_id: UUID
    view: ReferenceView
    sha256: str
    mime_type: str
    size_bytes: int

