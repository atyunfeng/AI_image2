from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from aiimage.db import Base


class ExportRecord(Base):
    __tablename__ = "export_records"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    batch_id: Mapped[UUID] = mapped_column(ForeignKey("generation_batches.id"), index=True)
    archive_asset_id: Mapped[UUID] = mapped_column(ForeignKey("assets.id"))
    manifest_sha256: Mapped[str] = mapped_column(String(64), index=True)
    created_by_user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
