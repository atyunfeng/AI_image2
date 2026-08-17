"""Link generation batches to compiled production plans."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0008_link_batches_to_plans"
down_revision: str | None = "0007_production_plans"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "generation_batches", sa.Column("production_plan_id", sa.Uuid(), nullable=True)
    )
    op.add_column(
        "generation_batches", sa.Column("production_plan_item_id", sa.Uuid(), nullable=True)
    )
    op.create_foreign_key(
        "fk_generation_batches_production_plan",
        "generation_batches",
        "production_plans",
        ["production_plan_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_generation_batches_production_plan_item",
        "generation_batches",
        "production_plan_items",
        ["production_plan_item_id"],
        ["id"],
    )
    op.create_index(
        "ix_generation_batches_production_plan_id",
        "generation_batches",
        ["production_plan_id"],
    )
    op.create_unique_constraint(
        "uq_generation_batches_production_plan_item_id",
        "generation_batches",
        ["production_plan_item_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_generation_batches_production_plan_item_id",
        "generation_batches",
        type_="unique",
    )
    op.drop_index(
        "ix_generation_batches_production_plan_id", table_name="generation_batches"
    )
    op.drop_constraint(
        "fk_generation_batches_production_plan_item",
        "generation_batches",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_generation_batches_production_plan",
        "generation_batches",
        type_="foreignkey",
    )
    op.drop_column("generation_batches", "production_plan_item_id")
    op.drop_column("generation_batches", "production_plan_id")
