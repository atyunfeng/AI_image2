from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class QualityCheckResponse(BaseModel):
    code: str
    passed: bool
    blocking: bool
    expected: dict[str, Any]
    measured: dict[str, Any]
    message: str


class QualityRunResponse(BaseModel):
    id: UUID
    batch_id: UUID
    output_asset_id: UUID
    passed: bool
    created_at: datetime
    checks: list[QualityCheckResponse]
