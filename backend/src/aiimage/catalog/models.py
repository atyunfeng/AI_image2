from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from aiimage.db import Base


class ProductCategory(StrEnum):
    APPAREL = "apparel"
    SHOES = "shoes"
    HATS = "hats"
    OTHER = "other"


class ReferenceView(StrEnum):
    FRONT = "front"
    SIDE = "side"
    BACK = "back"
    DETAIL = "detail"
    LOGO = "logo"


class Product(Base):
    __tablename__ = "products"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    sku: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    category: Mapped[str] = mapped_column(String(30))
    created_by_user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


class ProductReference(Base):
    __tablename__ = "product_references"
    __table_args__ = (UniqueConstraint("product_id", "asset_id", "view"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    product_id: Mapped[UUID] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"))
    asset_id: Mapped[UUID] = mapped_column(ForeignKey("assets.id", ondelete="RESTRICT"))
    view: Mapped[str] = mapped_column(String(30))


class TruthAnchor(Base):
    __tablename__ = "truth_anchors"
    __table_args__ = (UniqueConstraint("product_id", "version"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    product_id: Mapped[UUID] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"))
    version: Mapped[int]
    document: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_by_user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

