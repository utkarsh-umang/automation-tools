"""add thumbnail_jobs indexes for query patterns

Revision ID: c3d9f02b4e51
Revises: b2c8e91a3f40
Create Date: 2026-04-05

Indexes (SBL-05):
- listing a user's jobs: created_by
- iteration history: root_job_id
- filter by status: status

After upgrade, verify with e.g.::

    EXPLAIN ANALYZE SELECT * FROM thumbnail_jobs WHERE created_by = $1;

Expect an index scan on ``idx_thumbnail_jobs_created_by``.

"""
from collections.abc import Sequence

from alembic import op

revision: str = "c3d9f02b4e51"
down_revision: str | None = "b2c8e91a3f40"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "idx_thumbnail_jobs_created_by",
        "thumbnail_jobs",
        ["created_by"],
        unique=False,
    )
    op.create_index(
        "idx_thumbnail_jobs_root_job_id",
        "thumbnail_jobs",
        ["root_job_id"],
        unique=False,
    )
    op.create_index(
        "idx_thumbnail_jobs_status",
        "thumbnail_jobs",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_thumbnail_jobs_status", table_name="thumbnail_jobs")
    op.drop_index("idx_thumbnail_jobs_root_job_id", table_name="thumbnail_jobs")
    op.drop_index("idx_thumbnail_jobs_created_by", table_name="thumbnail_jobs")
