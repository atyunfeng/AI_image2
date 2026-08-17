from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class CreateEditProjectRequest(BaseModel):
    source_batch_id: UUID
    name: str | None = Field(default=None, max_length=255)


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


class EditEvidenceResponse(BaseModel):
    id: UUID
    revision_id: UUID
    output_asset_id: UUID
    automated_passed: bool
    checks: dict[str, bool]
    measured: dict[str, Any]
    human_review_checks: list[str]
    created_at: datetime
