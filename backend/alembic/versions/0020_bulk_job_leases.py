"""add recoverable bulk job leases

Revision ID: 0020_bulk_job_leases
Revises: 0019_product_hardening
"""

import sqlalchemy as sa

from alembic import op

revision = "0020_bulk_job_leases"
down_revision = "0019_product_hardening"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("bulk_jobs", sa.Column("lease_owner", sa.String(length=255), nullable=True))
    op.add_column(
        "bulk_jobs",
        sa.Column("lease_expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_bulk_jobs_lease_expires_at", "bulk_jobs", ["lease_expires_at"])


def downgrade() -> None:
    op.drop_index("ix_bulk_jobs_lease_expires_at", table_name="bulk_jobs")
    op.drop_column("bulk_jobs", "lease_expires_at")
    op.drop_column("bulk_jobs", "lease_owner")
