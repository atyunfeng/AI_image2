from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from aiimage.auth.models import Role


class AdminUserCreate(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=12, max_length=256)
    roles: set[Role] = Field(min_length=1)


class AdminUserUpdate(BaseModel):
    roles: set[Role] | None = Field(default=None, min_length=1)
    is_active: bool | None = None
    password: str | None = Field(default=None, min_length=12, max_length=256)


class AdminUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    roles: list[Role]
    is_active: bool
    created_at: datetime


class AuditEventResponse(BaseModel):
    id: UUID
    actor_user_id: UUID | None
    event_type: str
    details: dict[str, Any]
    created_at: datetime


class AuditEventPage(BaseModel):
    total: int
    items: list[AuditEventResponse]
