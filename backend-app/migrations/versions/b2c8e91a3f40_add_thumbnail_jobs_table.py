"""add thumbnail_jobs table

Revision ID: b2c8e91a3f40
Revises: 05500f5a0ddd
Create Date: 2026-04-05

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b2c8e91a3f40"
down_revision: str | None = "05500f5a0ddd"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "thumbnail_jobs",
        sa.Column(
            "id",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=20),
            server_default=sa.text("'pending'"),
            nullable=False,
        ),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("parent_job_id", sa.Uuid(), nullable=True),
        sa.Column("root_job_id", sa.Uuid(), nullable=True),
        sa.Column(
            "iteration",
            sa.Integer(),
            server_default=sa.text("1"),
            nullable=False,
        ),
        sa.Column("result_url", sa.Text(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["parent_job_id"],
            ["thumbnail_jobs.id"],
        ),
        sa.ForeignKeyConstraint(
            ["root_job_id"],
            ["thumbnail_jobs.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("thumbnail_jobs")
