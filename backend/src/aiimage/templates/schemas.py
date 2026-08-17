from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel

from aiimage.templates.models import PackKind, PackStatus


class TemplatePackResponse(BaseModel):
    id: UUID
    version_id: UUID
    slug: str
    name: str
    kind: PackKind
    version: int
    status: PackStatus
    rules: dict[str, Any]
    source: str
    published_at: datetime
