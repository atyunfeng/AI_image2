"""Create durable workflow tables."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004_workflow"
down_revision: str | None = "0003_model_registry"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "generation_batches",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("product_id", sa.Uuid(), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("model_configuration_id", sa.Uuid(), sa.ForeignKey("model_configurations.id"), nullable=False),
        sa.Column("requested_view", sa.String(30), nullable=False),
        sa.Column("mode", sa.String(20), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("width", sa.Integer(), nullable=False),
        sa.Column("height", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("input_snapshot", sa.JSON(), nullable=False),
        sa.Column("created_by_user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "generation_steps",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("batch_id", sa.Uuid(), sa.ForeignKey("generation_batches.id", ondelete="CASCADE"), nullable=False),
        sa.Column("idempotency_key", sa.String(128), unique=True, nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("lease_owner", sa.String(100), nullable=True),
        sa.Column("lease_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("provider_request_id", sa.String(255), nullable=True),
        sa.Column("output_asset_id", sa.Uuid(), sa.ForeignKey("assets.id"), nullable=True),
        sa.Column("estimated_cost_minor", sa.Integer(), nullable=False),
        sa.Column("error_classification", sa.String(100), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("generation_steps")
    op.drop_table("generation_batches")

