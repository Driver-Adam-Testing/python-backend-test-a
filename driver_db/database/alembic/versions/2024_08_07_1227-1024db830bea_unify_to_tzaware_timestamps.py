"""Unify to tzaware timestamps

Revision ID: 1024db830bea
Revises: ba2204f9ebda
Create Date: 2024-08-07 12:27:56.209289

"""

import datetime

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "1024db830bea"
down_revision = "ba2204f9ebda"
branch_labels = None
depends_on = None


def execute_update(statement: str, conn) -> None:
    result = conn.execute(sa.text(statement))
    rowcount = result.rowcount
    print(f"Executed: {statement}, Rows affected: {rowcount}")


def update_timestamps(
    table: str, created_at_col: str, updated_at_col: str, timestamp: datetime, conn
) -> None:
    if created_at_col != updated_at_col:
        execute_update(
            f"""
            UPDATE {table}
            SET {updated_at_col} = {created_at_col}
            WHERE {created_at_col} IS NOT NULL AND {updated_at_col} IS NULL;
        """,
            conn,
        )

    execute_update(
        f"""
        UPDATE {table}
        SET {created_at_col} = COALESCE({created_at_col}, '{timestamp}'), {updated_at_col} = COALESCE({updated_at_col}, '{timestamp}')
        WHERE {created_at_col} IS NULL OR {updated_at_col} IS NULL;
    """,
        conn,
    )


def update_created_at_only(
    table: str, created_at_col: str, timestamp: datetime, conn
) -> None:
    execute_update(
        f"""
        UPDATE {table}
        SET {created_at_col} = '{timestamp}'
        WHERE {created_at_col} IS NULL;
    """,
        conn,
    )


def upgrade():
    now = datetime.datetime.now(datetime.UTC)

    conn = op.get_bind()

    tables_with_updated_at = [
        ("chunk", "created_at", "updated_at"),
        ("codebases", "created_at", "updated_at"),
        ("contentmetadata", "created_at", "updated_at"),
        ("derived_content_types", "created_at", "updated_at"),
        ("derived_contents", "created_at", "updated_at"),
        ("runtimelogagentinstance", "created_at", "updated_at"),
        ("workspaces", "created_at", "updated_at"),
    ]

    tables_with_created_at_only = [
        ("runtimelogagenterror", "created_at"),
        ("runtimelogagentmessage", "created_at"),
    ]

    for table, created_at_col, updated_at_col in tables_with_updated_at:
        update_timestamps(table, created_at_col, updated_at_col, now, conn)

    for table, created_at_col in tables_with_created_at_only:
        update_created_at_only(table, created_at_col, now, conn)

    op.alter_column(
        "chunk",
        "created_at",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        nullable=False,
        server_default=sa.text("now()"),
    )
    op.alter_column(
        "chunk",
        "updated_at",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        nullable=False,
        server_default=sa.text("now()"),
    )

    op.alter_column(
        "codebases",
        "created_at",
        existing_type=postgresql.TIMESTAMP(),
        type_=sa.DateTime(timezone=True),
        nullable=False,
        existing_server_default=sa.text("now()"),
        server_default=sa.text("now()"),
    )
    op.alter_column(
        "codebases",
        "updated_at",
        existing_type=postgresql.TIMESTAMP(),
        type_=sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.text("now()"),
    )

    op.alter_column(
        "contentmetadata",
        "created_at",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        nullable=False,
        server_default=sa.text("now()"),
    )
    op.alter_column(
        "contentmetadata",
        "updated_at",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        nullable=False,
        server_default=sa.text("now()"),
    )

    op.alter_column(
        "derived_content_types",
        "created_at",
        existing_type=postgresql.TIMESTAMP(),
        type_=sa.DateTime(timezone=True),
        nullable=False,
        existing_server_default=sa.text("now()"),
        server_default=sa.text("now()"),
    )
    op.alter_column(
        "derived_content_types",
        "updated_at",
        existing_type=postgresql.TIMESTAMP(),
        type_=sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.text("now()"),
    )

    op.alter_column(
        "derived_contents",
        "created_at",
        existing_type=postgresql.TIMESTAMP(),
        type_=sa.DateTime(timezone=True),
        nullable=False,
        existing_server_default=sa.text("now()"),
        server_default=sa.text("now()"),
    )
    op.alter_column(
        "derived_contents",
        "updated_at",
        existing_type=postgresql.TIMESTAMP(),
        type_=sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.text("now()"),
    )

    op.alter_column(
        "runtimelogagenterror",
        "created_at",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        nullable=False,
        server_default=sa.text("now()"),
    )

    op.alter_column(
        "runtimelogagentinstance",
        "created_at",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        nullable=False,
        server_default=sa.text("now()"),
    )
    op.alter_column(
        "runtimelogagentinstance",
        "updated_at",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        nullable=False,
        server_default=sa.text("now()"),
    )

    op.alter_column(
        "runtimelogagentmessage",
        "created_at",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        nullable=False,
        server_default=sa.text("now()"),
    )

    op.alter_column(
        "workspaces",
        "created_at",
        existing_type=postgresql.TIMESTAMP(),
        type_=sa.DateTime(timezone=True),
        nullable=False,
        existing_server_default=sa.text("now()"),
        server_default=sa.text("now()"),
    )
    op.alter_column(
        "workspaces",
        "updated_at",
        existing_type=postgresql.TIMESTAMP(),
        type_=sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.text("now()"),
    )


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "workspaces",
        "updated_at",
        existing_type=sa.DateTime(timezone=True),
        type_=postgresql.TIMESTAMP(),
        nullable=True,
    )
    op.alter_column(
        "workspaces",
        "created_at",
        existing_type=sa.DateTime(timezone=True),
        type_=postgresql.TIMESTAMP(),
        nullable=True,
        existing_server_default=sa.text("now()"),
    )
    op.alter_column(
        "runtimelogagentmessage",
        "created_at",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        nullable=True,
    )
    op.alter_column(
        "runtimelogagentinstance",
        "updated_at",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        nullable=True,
    )
    op.alter_column(
        "runtimelogagentinstance",
        "created_at",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        nullable=True,
    )
    op.alter_column(
        "runtimelogagenterror",
        "created_at",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        nullable=True,
    )
    op.alter_column(
        "derived_contents",
        "updated_at",
        existing_type=sa.DateTime(timezone=True),
        type_=postgresql.TIMESTAMP(),
        nullable=True,
    )
    op.alter_column(
        "derived_contents",
        "created_at",
        existing_type=sa.DateTime(timezone=True),
        type_=postgresql.TIMESTAMP(),
        nullable=True,
        existing_server_default=sa.text("now()"),
    )
    op.alter_column(
        "derived_content_types",
        "updated_at",
        existing_type=sa.DateTime(timezone=True),
        type_=postgresql.TIMESTAMP(),
        nullable=True,
    )
    op.alter_column(
        "derived_content_types",
        "created_at",
        existing_type=sa.DateTime(timezone=True),
        type_=postgresql.TIMESTAMP(),
        nullable=True,
        existing_server_default=sa.text("now()"),
    )
    op.alter_column(
        "contentmetadata",
        "updated_at",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        nullable=True,
    )
    op.alter_column(
        "contentmetadata",
        "created_at",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        nullable=True,
    )
    op.alter_column(
        "codebases",
        "updated_at",
        existing_type=sa.DateTime(timezone=True),
        type_=postgresql.TIMESTAMP(),
        nullable=True,
    )
    op.alter_column(
        "codebases",
        "created_at",
        existing_type=sa.DateTime(timezone=True),
        type_=postgresql.TIMESTAMP(),
        nullable=True,
        existing_server_default=sa.text("now()"),
    )
    # ### end Alembic commands ###
