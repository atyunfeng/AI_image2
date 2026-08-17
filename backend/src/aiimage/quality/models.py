from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from aiimage.db import Base


class QualityRun(Base):
    __tablename__ = "quality_runs"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    batch_id: Mapped[UUID] = mapped_column(
        ForeignKey("generation_batches.id", ondelete="CASCADE"), index=True
    )
    output_asset_id: Mapped[UUID] = mapped_column(ForeignKey("assets.id"))
    passed: Mapped[bool] = mapped_column(Boolean)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class QualityCheck(Base):
    __tablename__ = "quality_checks"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    run_id: Mapped[UUID] = mapped_column(
        ForeignKey("quality_runs.id", ondelete="CASCADE"), index=True
    )
    code: Mapped[str] = mapped_column(String(100))
    passed: Mapped[bool] = mapped_column(Boolean)
    blocking: Mapped[bool] = mapped_column(Boolean, default=True)
    expected: Mapped[dict[str, Any]] = mapped_column(JSON)
    measured: Mapped[dict[str, Any]] = mapped_column(JSON)
    message: Mapped[str] = mapped_column(Text)
