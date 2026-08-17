from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
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
