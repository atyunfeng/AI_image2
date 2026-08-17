from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, model_validator

RejectionReason = Literal[
    "product_drift",
    "color_error",
    "text_error",
    "model_anatomy",
    "platform_rule",
    "other",
]


class ReviewRequest(BaseModel):
    decision: Literal["approve", "reject"]
    rejection_reason: RejectionReason | None = None
    note: str | None = None

    @model_validator(mode="after")
    def validate_rejection(self) -> "ReviewRequest":
        if self.decision == "approve" and self.rejection_reason is not None:
            raise ValueError("Approval cannot include a rejection reason")
        if self.decision == "reject" and self.rejection_reason is None:
            raise ValueError("Rejection reason is required")
        if self.rejection_reason == "other" and not (self.note or "").strip():
            raise ValueError("A note is required for rejection reason 'other'")
        return self


class ReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    batch_id: UUID
    step_id: UUID
    output_asset_id: UUID | None
    reviewer_user_id: UUID
    decision: str
    rejection_reason: str | None
    note: str | None
