from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from aiimage.db import Base


class FashionEvidence(Base):
    __tablename__ = "fashion_evidence"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    batch_id: Mapped[UUID] = mapped_column(
        ForeignKey("generation_batches.id", ondelete="CASCADE"), index=True
    )
    output_asset_id: Mapped[UUID] = mapped_column(ForeignKey("assets.id"))
    capability: Mapped[str] = mapped_column(String(50))
    inferred_view: Mapped[bool] = mapped_column(Boolean, default=False)
    automated_passed: Mapped[bool] = mapped_column(Boolean)
    checks: Mapped[dict[str, bool]] = mapped_column(JSON)
    measured: Mapped[dict[str, Any]] = mapped_column(JSON)
    human_review_checks: Mapped[list[str]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
