from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from aiimage.db import Base


class BulkJob(Base):
    __tablename__ = "bulk_jobs"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    filename: Mapped[str] = mapped_column(String(255))
    dry_run: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(30), default="processing")
    model_configuration_id: Mapped[UUID] = mapped_column(ForeignKey("model_configurations.id"))
    category_pack_version_id: Mapped[UUID] = mapped_column(ForeignKey("template_pack_versions.id"))
    brand_pack_version_id: Mapped[UUID] = mapped_column(ForeignKey("template_pack_versions.id"))
    total_rows: Mapped[int] = mapped_column(Integer, default=0)
    succeeded_rows: Mapped[int] = mapped_column(Integer, default=0)
    failed_rows: Mapped[int] = mapped_column(Integer, default=0)
    lease_owner: Mapped[str | None] = mapped_column(String(255), nullable=True)
    lease_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_by_user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class BulkJobRow(Base):
    __tablename__ = "bulk_job_rows"
    __table_args__ = (UniqueConstraint("job_id", "row_number"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    job_id: Mapped[UUID] = mapped_column(ForeignKey("bulk_jobs.id", ondelete="CASCADE"), index=True)
    row_number: Mapped[int] = mapped_column(Integer)
    sku: Mapped[str] = mapped_column(String(100), default="")
    status: Mapped[str] = mapped_column(String(30))
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    input_data: Mapped[dict[str, Any]] = mapped_column(JSON)
    product_id: Mapped[UUID | None] = mapped_column(ForeignKey("products.id"), nullable=True)
    production_plan_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("production_plans.id"), nullable=True
    )
    batch_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
