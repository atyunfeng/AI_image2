"""Create fashion plans and capability-aware generation batches."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0012_fashion_batches"
down_revision: str | None = "0011_model_profiles"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "fashion_plans",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("product_id", sa.Uuid(), sa.ForeignKey("products.id"), nullable=False),
        sa.Column(
            "model_profile_id", sa.Uuid(), sa.ForeignKey("model_profiles.id"), nullable=False
        ),
        sa.Column(
            "model_configuration_id",
            sa.Uuid(),
            sa.ForeignKey("model_configurations.id"),
            nullable=False,
        ),
        sa.Column("category", sa.String(30), nullable=False),
        sa.Column("mode", sa.String(30), nullable=False),
        sa.Column("requested_outputs", sa.JSON(), nullable=False),
        sa.Column("input_snapshot", sa.JSON(), nullable=False),
        sa.Column("created_by_user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.add_column(
        "generation_batches", sa.Column("fashion_plan_id", sa.Uuid(), nullable=True)
    )
    op.add_column(
        "generation_batches", sa.Column("model_profile_id", sa.Uuid(), nullable=True)
    )
    op.add_column(
        "generation_batches",
        sa.Column("capability", sa.String(50), nullable=False, server_default="reference_to_image"),
    )
    op.create_foreign_key(
        "fk_generation_batches_fashion_plan",
        "generation_batches",
        "fashion_plans",
        ["fashion_plan_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_generation_batches_model_profile",
        "generation_batches",
        "model_profiles",
        ["model_profile_id"],
        ["id"],
    )
    op.create_index(
        "ix_generation_batches_fashion_plan_id", "generation_batches", ["fashion_plan_id"]
    )
    op.create_index(
        "ix_generation_batches_model_profile_id", "generation_batches", ["model_profile_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_generation_batches_model_profile_id", table_name="generation_batches")
    op.drop_index("ix_generation_batches_fashion_plan_id", table_name="generation_batches")
    op.drop_constraint(
        "fk_generation_batches_model_profile", "generation_batches", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_generation_batches_fashion_plan", "generation_batches", type_="foreignkey"
    )
    op.drop_column("generation_batches", "capability")
    op.drop_column("generation_batches", "model_profile_id")
    op.drop_column("generation_batches", "fashion_plan_id")
    op.drop_table("fashion_plans")
