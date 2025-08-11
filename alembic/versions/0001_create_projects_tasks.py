from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0001_create_projects_tasks"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name
    schema = "tasks" if dialect != "sqlite" else None

    if dialect == "postgresql":
        op.execute(
            sa.schema.CreateSequence(sa.Sequence("projects_id_seq", schema="tasks"))
        )
        op.execute(
            sa.schema.CreateSequence(sa.Sequence("tasks_id_seq", schema="tasks"))
        )

    op.create_table(
        "projects",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("slug", sa.String(), nullable=False, unique=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        schema=schema,
    )

    op.create_table(
        "tasks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "project_id",
            sa.Integer(),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("tags", sa.JSON(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        schema=schema,
    )

    op.create_index(
        "ix_projects_slug", "projects", ["slug"], unique=True, schema=schema
    )
    op.create_index(
        "ix_tasks_project_status", "tasks", ["project_id", "status"], schema=schema
    )
    if dialect == "postgresql":
        op.create_index(
            "ix_tasks_tags",
            "tasks",
            ["tags"],
            postgresql_using="gin",
            schema=schema,
        )


def downgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name
    schema = "tasks" if dialect != "sqlite" else None

    if dialect == "postgresql":
        op.drop_index("ix_tasks_tags", table_name="tasks", schema=schema)
    op.drop_index("ix_tasks_project_status", table_name="tasks", schema=schema)
    op.drop_index("ix_projects_slug", table_name="projects", schema=schema)
    op.drop_table("tasks", schema=schema)
    op.drop_table("projects", schema=schema)

    if dialect == "postgresql":
        op.execute(sa.schema.DropSequence(sa.Sequence("tasks_id_seq", schema="tasks")))
        op.execute(
            sa.schema.DropSequence(sa.Sequence("projects_id_seq", schema="tasks"))
        )
