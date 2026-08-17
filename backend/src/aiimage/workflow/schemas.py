from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from aiimage.catalog.models import ReferenceView
from aiimage.workflow.state import BatchStatus


class CreateBatchRequest(BaseModel):
    product_id: UUID
    model_configuration_id: UUID
    requested_view: ReferenceView
    mode: Literal["strict", "creative"] = "strict"
    prompt: str = Field(min_length=1, max_length=4000)
    width: int = Field(ge=64, le=4096)
    height: int = Field(ge=64, le=4096)


class BatchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    product_id: UUID
    model_configuration_id: UUID
    requested_view: ReferenceView
    mode: str
    status: BatchStatus
    prompt: str
    width: int
    height: int


class BatchDetailResponse(BatchResponse):
    output_asset_id: UUID | None = None
    provider_request_id: str | None = None
    estimated_cost_minor: int = 0
    error_classification: str | None = None
