from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ExportRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    batch_id: UUID
    archive_asset_id: UUID
    manifest_sha256: str
    created_by_user_id: UUID
    created_at: datetime
