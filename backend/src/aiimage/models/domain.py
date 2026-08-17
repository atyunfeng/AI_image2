from enum import StrEnum
from typing import Any, Literal, Protocol

from pydantic import BaseModel, Field


class Capability(StrEnum):
    TEXT_TO_IMAGE = "text_to_image"
    REFERENCE_TO_IMAGE = "reference_to_image"
    MULTI_REFERENCE_TO_IMAGE = "multi_reference_to_image"
    INPAINT = "inpaint"
    OUTPAINT = "outpaint"
    VIRTUAL_TRY_ON = "virtual_try_on"
    REMOVE_BACKGROUND = "remove_background"
    SEGMENT = "segment"
    UPSCALE = "upscale"
    VISION_ANALYZE = "vision_analyze"
    QUALITY_INSPECT = "quality_inspect"


class ReferenceImage(BaseModel):
    content: bytes
    mime_type: Literal["image/png", "image/jpeg", "image/webp"]


class GenerationRequest(BaseModel):
    idempotency_key: str
    capability: Capability
    prompt: str
    reference_images: list[ReferenceImage]
    width: int = Field(ge=64, le=4096)
    height: int = Field(ge=64, le=4096)
    parameters: dict[str, Any]


class GenerationResult(BaseModel):
    content: bytes
    mime_type: Literal["image/png", "image/jpeg", "image/webp"]
    content_sha256: str
    provider_request_id: str
    estimated_cost_minor: int = 0


class ProviderAdapter(Protocol):
    async def test_connection(self) -> None:
        raise NotImplementedError

    async def generate(self, request: GenerationRequest) -> GenerationResult:
        raise NotImplementedError

