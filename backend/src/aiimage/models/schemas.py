from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from aiimage.models.domain import Capability


class ModelCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    provider: Literal["mock", "generic_http", "comfyui"]
    model_id: str = Field(min_length=1, max_length=200)
    base_url: str | None = None
    billing_currency: str = Field(default="USD", pattern="^[A-Z]{3}$")
    provider_options: dict[str, Any] = Field(default_factory=dict)
    api_key: str | None = None
    capabilities: set[Capability]

    @field_validator("billing_currency", mode="before")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return value.strip().upper()


class ModelUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    provider: Literal["mock", "generic_http", "comfyui"] | None = None
    model_id: str | None = Field(default=None, min_length=1, max_length=200)
    base_url: str | None = None
    billing_currency: str | None = Field(default=None, pattern="^[A-Z]{3}$")
    provider_options: dict[str, Any] | None = None
    api_key: str | None = None
    clear_api_key: bool = False
    capabilities: set[Capability] | None = None
    is_enabled: bool | None = None

    @field_validator("billing_currency", mode="before")
    @classmethod
    def normalize_optional_currency(cls, value: str | None) -> str | None:
        return value.strip().upper() if value is not None else None


class ModelResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    provider: str
    model_id: str
    base_url: str | None
    billing_currency: str
    provider_options: dict[str, Any]
    capabilities: list[Capability]
    has_key: bool
    key_suffix: str | None
    is_enabled: bool
