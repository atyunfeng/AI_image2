"""Complete product governance, production, editing, and export persistence."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0018_product_completion"
down_revision: str | None = "0017_model_provider_options"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("products", sa.Column("brand", sa.String(255)))
    op.add_column("products", sa.Column("archived_at", sa.DateTime(timezone=True)))
    op.alter_column("template_pack_versions", "published_at", nullable=True)
    op.add_column(
        "production_plan_items",
        sa.Column("model_configuration_id", sa.Uuid(), sa.ForeignKey("model_configurations.id")),
    )
    op.add_column(
        "production_plan_items",
        sa.Column("reference_ids", sa.JSON(), nullable=False, server_default="[]"),
    )
    op.add_column(
        "production_plan_items",
        sa.Column("provider_parameters", sa.JSON(), nullable=False, server_default="{}"),
    )
    op.add_column(
        "generation_batches",
        sa.Column("source_batch_id", sa.Uuid(), sa.ForeignKey("generation_batches.id")),
    )
    op.create_index("ix_generation_batches_source_batch_id", "generation_batches", ["source_batch_id"])
    op.add_column("generation_steps", sa.Column("started_at", sa.DateTime(timezone=True)))
    op.add_column("generation_steps", sa.Column("completed_at", sa.DateTime(timezone=True)))
    op.create_table(
        "edit_layers",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "project_id",
            sa.Uuid(),
            sa.ForeignKey("edit_projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("layer_type", sa.String(30), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("visible", sa.Boolean(), nullable=False),
        sa.Column("locked", sa.Boolean(), nullable=False),
        sa.Column("opacity", sa.Integer(), nullable=False),
        sa.Column("content", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("project_id", "position"),
    )
    op.create_index("ix_edit_layers_project_id", "edit_layers", ["project_id"])
    op.create_table(
        "export_records",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("batch_id", sa.Uuid(), sa.ForeignKey("generation_batches.id"), nullable=False),
        sa.Column("archive_asset_id", sa.Uuid(), sa.ForeignKey("assets.id"), nullable=False),
        sa.Column("manifest_sha256", sa.String(64), nullable=False),
        sa.Column("created_by_user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_export_records_batch_id", "export_records", ["batch_id"])
    op.create_index("ix_export_records_manifest_sha256", "export_records", ["manifest_sha256"])


def downgrade() -> None:
    op.drop_index("ix_export_records_manifest_sha256", table_name="export_records")
    op.drop_index("ix_export_records_batch_id", table_name="export_records")
    op.drop_table("export_records")
    op.drop_index("ix_edit_layers_project_id", table_name="edit_layers")
    op.drop_table("edit_layers")
    op.drop_column("generation_steps", "completed_at")
    op.drop_column("generation_steps", "started_at")
    op.drop_index("ix_generation_batches_source_batch_id", table_name="generation_batches")
    op.drop_column("generation_batches", "source_batch_id")
    op.drop_column("production_plan_items", "provider_parameters")
    op.drop_column("production_plan_items", "reference_ids")
    op.drop_column("production_plan_items", "model_configuration_id")
    op.alter_column("template_pack_versions", "published_at", nullable=False)
    op.drop_column("products", "archived_at")
    op.drop_column("products", "brand")
