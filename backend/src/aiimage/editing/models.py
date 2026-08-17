from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from aiimage.db import Base


class EditProject(Base):
    __tablename__ = "edit_projects"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255))
    product_id: Mapped[UUID] = mapped_column(ForeignKey("products.id"), index=True)
    source_batch_id: Mapped[UUID] = mapped_column(ForeignKey("generation_batches.id"))
    source_asset_id: Mapped[UUID] = mapped_column(ForeignKey("assets.id"))
    created_by_user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EditRevision(Base):
    __tablename__ = "edit_revisions"
    __table_args__ = (UniqueConstraint("project_id", "version"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(
        ForeignKey("edit_projects.id", ondelete="CASCADE"), index=True
    )
    parent_revision_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("edit_revisions.id", ondelete="RESTRICT"), nullable=True
    )
    version: Mapped[int]
    snapshot_label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    operation: Mapped[str] = mapped_column(String(50))
    capability: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="ready")
    source_asset_id: Mapped[UUID] = mapped_column(ForeignKey("assets.id"))
    mask_asset_id: Mapped[UUID | None] = mapped_column(ForeignKey("assets.id"), nullable=True)
    output_asset_id: Mapped[UUID | None] = mapped_column(ForeignKey("assets.id"), nullable=True)
    prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    parameters: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_by_user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EditEvidence(Base):
    __tablename__ = "edit_evidence"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    revision_id: Mapped[UUID] = mapped_column(
        ForeignKey("edit_revisions.id", ondelete="CASCADE"), index=True
    )
    output_asset_id: Mapped[UUID] = mapped_column(ForeignKey("assets.id"))
    automated_passed: Mapped[bool]
    checks: Mapped[dict[str, bool]] = mapped_column(JSON)
    measured: Mapped[dict[str, Any]] = mapped_column(JSON)
    human_review_checks: Mapped[list[str]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
