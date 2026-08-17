from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class BulkJobRowResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    row_number: int
    sku: str
    status: str
    error: str | None
    input_data: dict[str, str]
    product_id: UUID | None
    production_plan_id: UUID | None
    batch_ids: list[str]


class BulkJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    filename: str
    dry_run: bool
    status: str
    model_configuration_id: UUID
    category_pack_version_id: UUID
    brand_pack_version_id: UUID
    total_rows: int
    succeeded_rows: int
    failed_rows: int
    created_at: datetime
    rows: list[BulkJobRowResponse]

