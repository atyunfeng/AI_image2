"""Create append-only structural quality evidence."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0010_quality_results"
down_revision: str | None = "0009_asset_derivations"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "quality_runs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "batch_id",
            sa.Uuid(),
            sa.ForeignKey("generation_batches.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("output_asset_id", sa.Uuid(), sa.ForeignKey("assets.id"), nullable=False),
        sa.Column("passed", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_quality_runs_batch_id", "quality_runs", ["batch_id"])
    op.create_table(
        "quality_checks",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "run_id",
            sa.Uuid(),
            sa.ForeignKey("quality_runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("code", sa.String(100), nullable=False),
        sa.Column("passed", sa.Boolean(), nullable=False),
        sa.Column("blocking", sa.Boolean(), nullable=False),
        sa.Column("expected", sa.JSON(), nullable=False),
        sa.Column("measured", sa.JSON(), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
    )
    op.create_index("ix_quality_checks_run_id", "quality_checks", ["run_id"])


def downgrade() -> None:
    op.drop_index("ix_quality_checks_run_id", table_name="quality_checks")
    op.drop_table("quality_checks")
    op.drop_index("ix_quality_runs_batch_id", table_name="quality_runs")
    op.drop_table("quality_runs")
