"""product hardening retry scheduling

Revision ID: 0019_product_hardening
Revises: 0018_product_completion
"""

import sqlalchemy as sa

from alembic import op

revision = "0019_product_hardening"
down_revision = "0018_product_completion"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "generation_steps",
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_generation_steps_next_attempt_at",
        "generation_steps",
        ["next_attempt_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_generation_steps_next_attempt_at", table_name="generation_steps")
    op.drop_column("generation_steps", "next_attempt_at")
