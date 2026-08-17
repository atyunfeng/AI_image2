"""Create immutable compiled production plans."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0007_production_plans"
down_revision: str | None = "0006_template_packs"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "production_plans",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("product_id", sa.Uuid(), sa.ForeignKey("products.id"), nullable=False),
        sa.Column(
            "platform_pack_version_id",
            sa.Uuid(),
            sa.ForeignKey("template_pack_versions.id"),
            nullable=False,
        ),
        sa.Column(
            "category_pack_version_id",
            sa.Uuid(),
            sa.ForeignKey("template_pack_versions.id"),
            nullable=False,
        ),
        sa.Column(
            "brand_pack_version_id",
            sa.Uuid(),
            sa.ForeignKey("template_pack_versions.id"),
            nullable=False,
        ),
        sa.Column("mode", sa.String(30), nullable=False),
        sa.Column("compiled_snapshot", sa.JSON(), nullable=False),
        sa.Column("compiler_hash", sa.String(64), nullable=False),
        sa.Column("created_by_user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_production_plans_compiler_hash", "production_plans", ["compiler_hash"])
    op.create_table(
        "production_plan_items",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "plan_id",
            sa.Uuid(),
            sa.ForeignKey("production_plans.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("slot", sa.String(100), nullable=False),
        sa.Column("label", sa.String(255), nullable=False),
        sa.Column("requested_view", sa.String(50), nullable=False),
        sa.Column("width", sa.Integer(), nullable=False),
        sa.Column("height", sa.Integer(), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("authoritative_copy", sa.Text(), nullable=True),
        sa.Column("rules", sa.JSON(), nullable=False),
        sa.UniqueConstraint("plan_id", "position"),
    )
    op.create_index("ix_production_plan_items_plan_id", "production_plan_items", ["plan_id"])


def downgrade() -> None:
    op.drop_index("ix_production_plan_items_plan_id", table_name="production_plan_items")
    op.drop_table("production_plan_items")
    op.drop_index("ix_production_plans_compiler_hash", table_name="production_plans")
    op.drop_table("production_plans")
