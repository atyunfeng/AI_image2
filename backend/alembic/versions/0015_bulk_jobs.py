"""Create CSV bulk production jobs."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0015_bulk_jobs"
down_revision: str | None = "0014_edit_projects"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "bulk_jobs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("dry_run", sa.Boolean(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("model_configuration_id", sa.Uuid(), sa.ForeignKey("model_configurations.id"), nullable=False),
        sa.Column("category_pack_version_id", sa.Uuid(), sa.ForeignKey("template_pack_versions.id"), nullable=False),
        sa.Column("brand_pack_version_id", sa.Uuid(), sa.ForeignKey("template_pack_versions.id"), nullable=False),
        sa.Column("total_rows", sa.Integer(), nullable=False),
        sa.Column("succeeded_rows", sa.Integer(), nullable=False),
        sa.Column("failed_rows", sa.Integer(), nullable=False),
        sa.Column("created_by_user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "bulk_job_rows",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("job_id", sa.Uuid(), sa.ForeignKey("bulk_jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("row_number", sa.Integer(), nullable=False),
        sa.Column("sku", sa.String(100), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("error", sa.Text()),
        sa.Column("input_data", sa.JSON(), nullable=False),
        sa.Column("product_id", sa.Uuid(), sa.ForeignKey("products.id")),
        sa.Column("production_plan_id", sa.Uuid(), sa.ForeignKey("production_plans.id")),
        sa.Column("batch_ids", sa.JSON(), nullable=False),
        sa.UniqueConstraint("job_id", "row_number"),
    )
    op.create_index("ix_bulk_job_rows_job_id", "bulk_job_rows", ["job_id"])


def downgrade() -> None:
    op.drop_index("ix_bulk_job_rows_job_id", table_name="bulk_job_rows")
    op.drop_table("bulk_job_rows")
    op.drop_table("bulk_jobs")

