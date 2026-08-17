"""Create append-only fashion generation evidence."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0013_fashion_evidence"
down_revision: str | None = "0012_fashion_batches"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "fashion_evidence",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "batch_id",
            sa.Uuid(),
            sa.ForeignKey("generation_batches.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("output_asset_id", sa.Uuid(), sa.ForeignKey("assets.id"), nullable=False),
        sa.Column("capability", sa.String(50), nullable=False),
        sa.Column("inferred_view", sa.Boolean(), nullable=False),
        sa.Column("automated_passed", sa.Boolean(), nullable=False),
        sa.Column("checks", sa.JSON(), nullable=False),
        sa.Column("measured", sa.JSON(), nullable=False),
        sa.Column("human_review_checks", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_fashion_evidence_batch_id", "fashion_evidence", ["batch_id"])


def downgrade() -> None:
    op.drop_index("ix_fashion_evidence_batch_id", table_name="fashion_evidence")
    op.drop_table("fashion_evidence")
