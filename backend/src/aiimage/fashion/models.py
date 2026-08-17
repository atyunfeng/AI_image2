from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from aiimage.db import Base


class FashionPlan(Base):
    __tablename__ = "fashion_plans"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    product_id: Mapped[UUID] = mapped_column(ForeignKey("products.id", ondelete="RESTRICT"))
    model_profile_id: Mapped[UUID] = mapped_column(
        ForeignKey("model_profiles.id", ondelete="RESTRICT")
    )
    model_configuration_id: Mapped[UUID] = mapped_column(
        ForeignKey("model_configurations.id", ondelete="RESTRICT")
    )
    category: Mapped[str] = mapped_column(String(30))
    mode: Mapped[str] = mapped_column(String(30))
    requested_outputs: Mapped[list[str]] = mapped_column(JSON)
    input_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON)
    created_by_user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
