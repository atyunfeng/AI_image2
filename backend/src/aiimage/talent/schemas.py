from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from aiimage.talent.models import (
    AuthorizationStatus,
    ModelProfileType,
    ModelReferenceView,
)


class ModelProfileCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    profile_type: ModelProfileType
    authorization_status: AuthorizationStatus
    authorization_expires_on: date | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)


class ModelReferenceResponse(BaseModel):
    id: UUID
    asset_id: UUID
    view: ModelReferenceView
    sha256: str
    mime_type: str
    size_bytes: int


class ModelProfileResponse(BaseModel):
    id: UUID
    name: str
    profile_type: ModelProfileType
    authorization_status: AuthorizationStatus
    authorization_expires_on: date | None
    attributes: dict[str, Any]
    is_active: bool
    is_selectable: bool
    created_at: datetime
    references: list[ModelReferenceResponse]
