from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from aiimage.models.domain import Capability


class ModelCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    provider: Literal["mock", "generic_http"]
    model_id: str = Field(min_length=1, max_length=200)
    base_url: str | None = None
    billing_currency: str = Field(default="USD", pattern="^[A-Z]{3}$")
    api_key: str | None = None
    capabilities: set[Capability]

    @field_validator("billing_currency", mode="before")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return value.strip().upper()


class ModelResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    provider: str
    model_id: str
    base_url: str | None
    billing_currency: str
    capabilities: list[Capability]
    has_key: bool
    key_suffix: str | None
    is_enabled: bool
