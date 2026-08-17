from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from aiimage.db import Base
from aiimage.workflow.state import BatchStatus, StepStatus


class GenerationBatch(Base):
    __tablename__ = "generation_batches"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    production_plan_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("production_plans.id"), nullable=True, index=True
    )
    production_plan_item_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("production_plan_items.id"), nullable=True, unique=True
    )
    fashion_plan_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("fashion_plans.id"), nullable=True, index=True
    )
    model_profile_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("model_profiles.id"), nullable=True, index=True
    )
    product_id: Mapped[UUID] = mapped_column(ForeignKey("products.id"))
    model_configuration_id: Mapped[UUID] = mapped_column(ForeignKey("model_configurations.id"))
    requested_view: Mapped[str] = mapped_column(String(30))
    capability: Mapped[str] = mapped_column(String(50), default="reference_to_image")
    mode: Mapped[str] = mapped_column(String(20), default="strict")
    prompt: Mapped[str] = mapped_column(Text)
    width: Mapped[int]
    height: Mapped[int]
    status: Mapped[str] = mapped_column(String(30), default=BatchStatus.DRAFT.value)
    input_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON)
    created_by_user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class GenerationStep(Base):
    __tablename__ = "generation_steps"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    batch_id: Mapped[UUID] = mapped_column(ForeignKey("generation_batches.id", ondelete="CASCADE"))
    idempotency_key: Mapped[str] = mapped_column(String(128), unique=True)
    status: Mapped[str] = mapped_column(String(30), default=StepStatus.QUEUED.value)
    attempt_count: Mapped[int] = mapped_column(default=0)
    lease_owner: Mapped[str | None] = mapped_column(String(100), nullable=True)
    lease_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    provider_request_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    output_asset_id: Mapped[UUID | None] = mapped_column(ForeignKey("assets.id"), nullable=True)
    estimated_cost_minor: Mapped[int] = mapped_column(default=0)
    error_classification: Mapped[str | None] = mapped_column(String(100), nullable=True)
