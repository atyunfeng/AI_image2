from datetime import datetime
from enum import StrEnum
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

from aiimage.workflow.schemas import BatchDetailResponse, BatchResponse


class FashionOutput(StrEnum):
    PRODUCT_FRONT = "product_front"
    MODEL_FRONT = "model_front"
    MODEL_SIDE = "model_side"
    MODEL_BACK = "model_back"
    DETAIL = "detail"
    VIRTUAL_TRY_ON = "virtual_try_on"


class CreateFashionPlanRequest(BaseModel):
    product_id: UUID
    model_profile_id: UUID
    model_configuration_id: UUID
    requested_outputs: list[FashionOutput] = Field(min_length=1, max_length=6)
    mode: Literal["strict", "creative"] = "strict"


class FashionPlanResponse(BaseModel):
    id: UUID
    product_id: UUID
    model_profile_id: UUID
    model_configuration_id: UUID
    category: str
    mode: str
    requested_outputs: list[FashionOutput]
    created_at: datetime
    batches: list[BatchResponse | BatchDetailResponse]


class FashionEvidenceResponse(BaseModel):
    id: UUID
    batch_id: UUID
    output_asset_id: UUID
    capability: str
    inferred_view: bool
    automated_passed: bool
    checks: dict[str, bool]
    measured: dict[str, Any]
    human_review_checks: list[str]
    created_at: datetime
