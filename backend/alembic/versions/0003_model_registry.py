"""Create model configuration table."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0003_model_registry"
down_revision: str | None = "0002_assets_catalog"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "model_configurations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("model_id", sa.String(length=200), nullable=False),
        sa.Column("base_url", sa.String(length=500), nullable=True),
        sa.Column("capabilities", sa.JSON(), nullable=False),
        sa.Column("encrypted_api_key", sa.LargeBinary(), nullable=True),
        sa.Column("api_key_nonce", sa.LargeBinary(), nullable=True),
        sa.Column("key_suffix", sa.String(length=4), nullable=True),
        sa.Column("is_enabled", sa.Boolean(), nullable=False),
        sa.Column("created_by_user_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )


def downgrade() -> None:
    op.drop_table("model_configurations")

