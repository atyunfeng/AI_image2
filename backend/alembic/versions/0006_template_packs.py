"""Create immutable template pack versions."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0006_template_packs"
down_revision: str | None = "0005_review"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "template_packs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("kind", sa.String(30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("slug"),
    )
    op.create_index("ix_template_packs_slug", "template_packs", ["slug"], unique=True)
    op.create_index("ix_template_packs_kind", "template_packs", ["kind"])
    op.create_table(
        "template_pack_versions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "pack_id",
            sa.Uuid(),
            sa.ForeignKey("template_packs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("rules", sa.JSON(), nullable=False),
        sa.Column("source", sa.String(100), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("pack_id", "version"),
    )
    op.create_index(
        "ix_template_pack_versions_pack_id", "template_pack_versions", ["pack_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_template_pack_versions_pack_id", table_name="template_pack_versions")
    op.drop_table("template_pack_versions")
    op.drop_index("ix_template_packs_kind", table_name="template_packs")
    op.drop_index("ix_template_packs_slug", table_name="template_packs")
    op.drop_table("template_packs")
