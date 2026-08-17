"""Add non-secret provider options for local execution nodes."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0017_model_provider_options"
down_revision: str | None = "0016_model_billing_currency"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "model_configurations",
        sa.Column("provider_options", sa.JSON(), nullable=False, server_default="{}"),
    )


def downgrade() -> None:
    op.drop_column("model_configurations", "provider_options")

