"""add thumbnail_folders table + folder_id/candidate_urls on thumbnail_jobs

Revision ID: a1f4c8d92b06
Revises: c3d9f02b4e51
Create Date: 2026-07-11

thumbnail_folders is shared org-wide (any authenticated user can read/use any
folder) — created_by is kept for audit only, not for access scoping.

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a1f4c8d92b06"
down_revision: str | None = "c3d9f02b4e51"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "thumbnail_folders",
        sa.Column(
            "id",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column(
            "style_prompt",
            sa.Text(),
            server_default=sa.text("''"),
            nullable=False,
        ),
        sa.Column("created_by", sa.Uuid(), nullable=False),
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
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.add_column(
        "thumbnail_jobs",
        sa.Column("folder_id", sa.Uuid(), nullable=True),
    )
    op.add_column(
        "thumbnail_jobs",
        sa.Column("candidate_urls", sa.ARRAY(sa.Text()), nullable=True),
    )
    op.create_foreign_key(
        "fk_thumbnail_jobs_folder_id",
        "thumbnail_jobs",
        "thumbnail_folders",
        ["folder_id"],
        ["id"],
    )
    op.create_index(
        "idx_thumbnail_jobs_folder_id",
        "thumbnail_jobs",
        ["folder_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_thumbnail_jobs_folder_id", table_name="thumbnail_jobs")
    op.drop_constraint(
        "fk_thumbnail_jobs_folder_id", "thumbnail_jobs", type_="foreignkey"
    )
    op.drop_column("thumbnail_jobs", "candidate_urls")
    op.drop_column("thumbnail_jobs", "folder_id")
    op.drop_table("thumbnail_folders")
