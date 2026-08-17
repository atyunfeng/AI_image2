from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class CreateEditProjectRequest(BaseModel):
    source_batch_id: UUID
    name: str | None = Field(default=None, max_length=255)


class EditLayerCreate(BaseModel):
    layer_type: str = Field(pattern="^(source|background|text|image|logo)$")
    name: str = Field(min_length=1, max_length=255)
    visible: bool = True
    locked: bool = False
    opacity: int = Field(default=100, ge=0, le=100)
    content: dict[str, Any] = {}


class EditLayerUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    visible: bool | None = None
    locked: bool | None = None
    opacity: int | None = Field(default=None, ge=0, le=100)
    content: dict[str, Any] | None = None


class EditLayerResponse(BaseModel):
    id: UUID
    project_id: UUID
    position: int
    layer_type: str
    name: str
    visible: bool
    locked: bool
    opacity: int
    content: dict[str, Any]


class LayerReorderRequest(BaseModel):
    layer_ids: list[UUID]


class SelectionRequest(BaseModel):
    revision_id: UUID
    selection_type: str = Field(pattern="^(foreground|background|person|garment)$")
    threshold: int = Field(default=42, ge=1, le=255)


class SelectionResponse(BaseModel):
    selection_type: str
    mask_asset_id: UUID
    sha256: str
    width: int
    height: int


class EditRevisionResponse(BaseModel):
    id: UUID
    project_id: UUID
    parent_revision_id: UUID | None
    version: int
    snapshot_label: str | None
    operation: str
    capability: str | None
    status: str
    source_asset_id: UUID
    mask_asset_id: UUID | None
    output_asset_id: UUID | None
    prompt: str | None
    parameters: dict[str, Any]
    batch_id: UUID | None = None
    created_at: datetime


class EditProjectResponse(BaseModel):
    id: UUID
    name: str
    product_id: UUID
    source_batch_id: UUID
    source_asset_id: UUID
    created_at: datetime
    revisions: list[EditRevisionResponse]
    layers: list[EditLayerResponse] = []


class EditEvidenceResponse(BaseModel):
    id: UUID
    revision_id: UUID
    output_asset_id: UUID
    automated_passed: bool
    checks: dict[str, bool]
    measured: dict[str, Any]
    human_review_checks: list[str]
    created_at: datetime
