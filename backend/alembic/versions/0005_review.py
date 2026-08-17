"""Create append-only review decisions."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0005_review"
down_revision: str | None = "0004_workflow"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "review_decisions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "batch_id", sa.Uuid(), sa.ForeignKey("generation_batches.id"), nullable=False
        ),
        sa.Column("step_id", sa.Uuid(), sa.ForeignKey("generation_steps.id"), nullable=False),
        sa.Column("output_asset_id", sa.Uuid(), sa.ForeignKey("assets.id"), nullable=True),
        sa.Column("reviewer_user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("decision", sa.String(20), nullable=False),
        sa.Column("rejection_reason", sa.String(50), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_review_decisions_batch_id", "review_decisions", ["batch_id"])


def downgrade() -> None:
    op.drop_index("ix_review_decisions_batch_id", table_name="review_decisions")
    op.drop_table("review_decisions")
