from datetime import date, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import JSON, Boolean, Date, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from aiimage.db import Base


class ModelProfileType(StrEnum):
    SYSTEM_VIRTUAL = "system_virtual"
    BRAND_AUTHORIZED = "brand_authorized"


class AuthorizationStatus(StrEnum):
    NOT_REQUIRED = "not_required"
    VALID = "valid"
    EXPIRED = "expired"


class ModelReferenceView(StrEnum):
    FRONT = "front"
    SIDE = "side"
    BACK = "back"
    HALF_BODY = "half_body"
    FULL_BODY = "full_body"


class ModelProfile(Base):
    __tablename__ = "model_profiles"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), index=True)
    profile_type: Mapped[str] = mapped_column(String(30), index=True)
    authorization_status: Mapped[str] = mapped_column(String(30))
    authorization_expires_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    attributes: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by_user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class ModelReference(Base):
    __tablename__ = "model_references"
    __table_args__ = (UniqueConstraint("profile_id", "asset_id", "view"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    profile_id: Mapped[UUID] = mapped_column(
        ForeignKey("model_profiles.id", ondelete="CASCADE"), index=True
    )
    asset_id: Mapped[UUID] = mapped_column(ForeignKey("assets.id", ondelete="RESTRICT"))
    view: Mapped[str] = mapped_column(String(30))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
