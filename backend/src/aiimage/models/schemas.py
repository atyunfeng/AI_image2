from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from aiimage.models.domain import Capability


class ModelCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    provider: Literal["mock", "generic_http"]
    model_id: str = Field(min_length=1, max_length=200)
    base_url: str | None = None
    api_key: str | None = None
    capabilities: set[Capability]


class ModelResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    provider: str
    model_id: str
    base_url: str | None
    capabilities: list[Capability]
    has_key: bool
    key_suffix: str | None
    is_enabled: bool

