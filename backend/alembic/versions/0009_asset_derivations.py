"""Record immutable asset derivation operations."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0009_asset_derivations"
down_revision: str | None = "0008_link_batches_to_plans"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "assets", sa.Column("derivation_operation", sa.String(100), nullable=True)
    )
    op.add_column("assets", sa.Column("derivation_parameters", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("assets", "derivation_parameters")
    op.drop_column("assets", "derivation_operation")
