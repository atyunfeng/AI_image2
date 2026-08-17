"""Create authorized model profiles and immutable references."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0011_model_profiles"
down_revision: str | None = "0010_quality_results"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "model_profiles",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("profile_type", sa.String(30), nullable=False),
        sa.Column("authorization_status", sa.String(30), nullable=False),
        sa.Column("authorization_expires_on", sa.Date(), nullable=True),
        sa.Column("attributes", sa.JSON(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_by_user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_model_profiles_name", "model_profiles", ["name"])
    op.create_index("ix_model_profiles_profile_type", "model_profiles", ["profile_type"])
    op.create_table(
        "model_references",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "profile_id",
            sa.Uuid(),
            sa.ForeignKey("model_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("asset_id", sa.Uuid(), sa.ForeignKey("assets.id"), nullable=False),
        sa.Column("view", sa.String(30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("profile_id", "asset_id", "view"),
    )
    op.create_index("ix_model_references_profile_id", "model_references", ["profile_id"])


def downgrade() -> None:
    op.drop_index("ix_model_references_profile_id", table_name="model_references")
    op.drop_table("model_references")
    op.drop_index("ix_model_profiles_profile_type", table_name="model_profiles")
    op.drop_index("ix_model_profiles_name", table_name="model_profiles")
    op.drop_table("model_profiles")
