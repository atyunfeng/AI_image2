from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from aiimage.db import Base


class PackKind(StrEnum):
    PLATFORM = "platform"
    CATEGORY = "category"
    BRAND = "brand"


class PackStatus(StrEnum):
    PUBLISHED = "published"


class TemplatePack(Base):
    __tablename__ = "template_packs"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    kind: Mapped[str] = mapped_column(String(30), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class TemplatePackVersion(Base):
    __tablename__ = "template_pack_versions"
    __table_args__ = (UniqueConstraint("pack_id", "version"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    pack_id: Mapped[UUID] = mapped_column(
        ForeignKey("template_packs.id", ondelete="CASCADE"), index=True
    )
    version: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(30), default=PackStatus.PUBLISHED.value)
    rules: Mapped[dict[str, Any]] = mapped_column(JSON)
    source: Mapped[str] = mapped_column(String(100), default="first_party_default")
    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class ProductionPlan(Base):
    __tablename__ = "production_plans"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    product_id: Mapped[UUID] = mapped_column(ForeignKey("products.id", ondelete="RESTRICT"))
    platform_pack_version_id: Mapped[UUID] = mapped_column(
        ForeignKey("template_pack_versions.id", ondelete="RESTRICT")
    )
    category_pack_version_id: Mapped[UUID] = mapped_column(
        ForeignKey("template_pack_versions.id", ondelete="RESTRICT")
    )
    brand_pack_version_id: Mapped[UUID] = mapped_column(
        ForeignKey("template_pack_versions.id", ondelete="RESTRICT")
    )
    mode: Mapped[str] = mapped_column(String(30), default="strict")
    compiled_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON)
    compiler_hash: Mapped[str] = mapped_column(String(64), index=True)
    created_by_user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class ProductionPlanItem(Base):
    __tablename__ = "production_plan_items"
    __table_args__ = (UniqueConstraint("plan_id", "position"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    plan_id: Mapped[UUID] = mapped_column(
        ForeignKey("production_plans.id", ondelete="CASCADE"), index=True
    )
    position: Mapped[int] = mapped_column(Integer)
    slot: Mapped[str] = mapped_column(String(100))
    label: Mapped[str] = mapped_column(String(255))
    requested_view: Mapped[str] = mapped_column(String(50))
    width: Mapped[int] = mapped_column(Integer)
    height: Mapped[int] = mapped_column(Integer)
    prompt: Mapped[str] = mapped_column(Text)
    authoritative_copy: Mapped[str | None] = mapped_column(Text, nullable=True)
    rules: Mapped[dict[str, Any]] = mapped_column(JSON)
