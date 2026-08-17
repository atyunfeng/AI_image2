"""Add explicit model billing currency."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0016_model_billing_currency"
down_revision: str | None = "0015_bulk_jobs"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "model_configurations",
        sa.Column("billing_currency", sa.String(3), nullable=False, server_default="USD"),
    )


def downgrade() -> None:
    op.drop_column("model_configurations", "billing_currency")

