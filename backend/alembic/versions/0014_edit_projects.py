"""Create immutable edit projects, revisions, and evidence."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0014_edit_projects"
down_revision: str | None = "0013_fashion_evidence"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "edit_projects",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("product_id", sa.Uuid(), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("source_batch_id", sa.Uuid(), sa.ForeignKey("generation_batches.id"), nullable=False),
        sa.Column("source_asset_id", sa.Uuid(), sa.ForeignKey("assets.id"), nullable=False),
        sa.Column("created_by_user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_edit_projects_product_id", "edit_projects", ["product_id"])
    op.create_table(
        "edit_revisions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("project_id", sa.Uuid(), sa.ForeignKey("edit_projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("parent_revision_id", sa.Uuid(), sa.ForeignKey("edit_revisions.id", ondelete="RESTRICT")),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("snapshot_label", sa.String(255)),
        sa.Column("operation", sa.String(50), nullable=False),
        sa.Column("capability", sa.String(50)),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("source_asset_id", sa.Uuid(), sa.ForeignKey("assets.id"), nullable=False),
        sa.Column("mask_asset_id", sa.Uuid(), sa.ForeignKey("assets.id")),
        sa.Column("output_asset_id", sa.Uuid(), sa.ForeignKey("assets.id")),
        sa.Column("prompt", sa.Text()),
        sa.Column("parameters", sa.JSON(), nullable=False),
        sa.Column("created_by_user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("project_id", "version"),
    )
    op.create_index("ix_edit_revisions_project_id", "edit_revisions", ["project_id"])
    op.create_table(
        "edit_evidence",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("revision_id", sa.Uuid(), sa.ForeignKey("edit_revisions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("output_asset_id", sa.Uuid(), sa.ForeignKey("assets.id"), nullable=False),
        sa.Column("automated_passed", sa.Boolean(), nullable=False),
        sa.Column("checks", sa.JSON(), nullable=False),
        sa.Column("measured", sa.JSON(), nullable=False),
        sa.Column("human_review_checks", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_edit_evidence_revision_id", "edit_evidence", ["revision_id"])
    op.add_column("generation_batches", sa.Column("edit_revision_id", sa.Uuid()))
    op.create_foreign_key("fk_generation_batches_edit_revision_id", "generation_batches", "edit_revisions", ["edit_revision_id"], ["id"])
    op.create_unique_constraint("uq_generation_batches_edit_revision_id", "generation_batches", ["edit_revision_id"])


def downgrade() -> None:
    op.drop_constraint("uq_generation_batches_edit_revision_id", "generation_batches", type_="unique")
    op.drop_constraint("fk_generation_batches_edit_revision_id", "generation_batches", type_="foreignkey")
    op.drop_column("generation_batches", "edit_revision_id")
    op.drop_index("ix_edit_evidence_revision_id", table_name="edit_evidence")
    op.drop_table("edit_evidence")
    op.drop_index("ix_edit_revisions_project_id", table_name="edit_revisions")
    op.drop_table("edit_revisions")
    op.drop_index("ix_edit_projects_product_id", table_name="edit_projects")
    op.drop_table("edit_projects")
