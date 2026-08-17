from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from aiimage.templates.models import PackKind, PackStatus


class TemplatePackResponse(BaseModel):
    id: UUID
    version_id: UUID
    slug: str
    name: str
    kind: PackKind
    version: int
    status: PackStatus
    rules: dict[str, Any]
    source: str
    published_at: datetime


class CompilePlanRequest(BaseModel):
    product_id: UUID
    platform_pack_version_id: UUID
    category_pack_version_id: UUID
    brand_pack_version_id: UUID
    mode: str = Field(default="strict", pattern="^(strict|creative)$")


class ProductionPlanItemResponse(BaseModel):
    id: UUID
    position: int
    slot: str
    label: str
    requested_view: str
    width: int
    height: int
    prompt: str
    authoritative_copy: str | None
    rules: dict[str, Any]


class ProductionPlanResponse(BaseModel):
    id: UUID
    product_id: UUID
    mode: str
    compiler_hash: str
    compiled_snapshot: dict[str, Any]
    created_at: datetime
    items: list[ProductionPlanItemResponse]
