from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from aiimage.catalog.models import ProductCategory, ReferenceView


class ProductCreate(BaseModel):
    sku: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=255)
    category: ProductCategory
    brand: str | None = Field(default=None, max_length=255)


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    category: ProductCategory | None = None
    brand: str | None = Field(default=None, max_length=255)


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    sku: str
    name: str
    category: ProductCategory
    brand: str | None = None


class TruthAnchorCreate(BaseModel):
    document: dict[str, Any]


class TruthAnchorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    version: int
    document: dict[str, Any]
    created_by_user_id: UUID
    created_at: datetime


class ProductHistoryResponse(BaseModel):
    generations: int = 0
    edits: int = 0
    reviews: int = 0
    exports: int = 0


class ProductReferenceResponse(BaseModel):
    id: UUID
    asset_id: UUID
    view: ReferenceView
    sha256: str
    mime_type: str
    size_bytes: int


class ProductDetailResponse(ProductResponse):
    references: list[ProductReferenceResponse]
    latest_truth_anchor: TruthAnchorResponse | None = None
    truth_anchors: list[TruthAnchorResponse] = []
    history: ProductHistoryResponse = ProductHistoryResponse()
