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
    published_at: datetime | None


class TemplatePackVersionResponse(BaseModel):
    id: UUID
    version: int
    status: PackStatus
    rules: dict[str, Any]
    source: str
    published_at: datetime | None


class ManagedTemplatePackResponse(BaseModel):
    id: UUID
    slug: str
    name: str
    kind: PackKind
    versions: list[TemplatePackVersionResponse]


class TemplatePackCreate(BaseModel):
    slug: str = Field(min_length=2, max_length=100, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    name: str = Field(min_length=1, max_length=255)
    kind: PackKind
    rules: dict[str, Any]


class TemplatePackVersionCreate(BaseModel):
    source_version_id: UUID | None = None
    rules: dict[str, Any] | None = None


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
    model_configuration_id: UUID | None = None
    reference_ids: list[UUID] = []
    provider_parameters: dict[str, Any] = {}


class ProductionPlanItemCreate(BaseModel):
    slot: str = Field(min_length=1, max_length=100)
    label: str = Field(min_length=1, max_length=255)
    requested_view: str = Field(min_length=1, max_length=50)
    width: int = Field(ge=64, le=4096)
    height: int = Field(ge=64, le=4096)
    prompt: str = Field(min_length=1, max_length=4000)
    authoritative_copy: str | None = None
    rules: dict[str, Any] = {}
    model_configuration_id: UUID | None = None
    reference_ids: list[UUID] = []
    provider_parameters: dict[str, Any] = {}


class ProductionPlanItemUpdate(BaseModel):
    label: str | None = Field(default=None, min_length=1, max_length=255)
    requested_view: str | None = Field(default=None, min_length=1, max_length=50)
    width: int | None = Field(default=None, ge=64, le=4096)
    height: int | None = Field(default=None, ge=64, le=4096)
    prompt: str | None = Field(default=None, min_length=1, max_length=4000)
    authoritative_copy: str | None = None
    rules: dict[str, Any] | None = None
    model_configuration_id: UUID | None = None
    reference_ids: list[UUID] | None = None
    provider_parameters: dict[str, Any] | None = None


class ProductionPlanResponse(BaseModel):
    id: UUID
    product_id: UUID
    mode: str
    compiler_hash: str
    compiled_snapshot: dict[str, Any]
    created_at: datetime
    items: list[ProductionPlanItemResponse]
