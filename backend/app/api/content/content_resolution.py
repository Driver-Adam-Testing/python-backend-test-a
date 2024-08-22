from uuid import UUID

from database.models_v1 import DerivedContent, Workspace
from sqlalchemy.sql import exists
from sqlmodel import select


def build_resolve_content_query(
    org_id: str,
    include_ids: list[UUID],
):
    """
    Constructs a SQL query to fetch `DerivedContent` rows that match the given inclusion criteria.

    This function generates a query that retrieves `DerivedContent` entries associated with a specific organization
    (`org_id`). The query includes content based on a list of `include_ids`.

    The inclusion is determined based on the `relative_path` of the `DerivedContent`. The function supports hierarchical
    path structures, meaning:
      - Including a parent path will automatically include all its sub-paths.
    """

    include_subquery = (
        select(DerivedContent.relative_path)
        .join(Workspace, DerivedContent.workspace_id == Workspace.id)
        .where(
            DerivedContent.id.in_(include_ids),
            Workspace.organization_id == org_id,
        )
    ).subquery()

    query = (
        select(DerivedContent)
        .join(Workspace, DerivedContent.workspace_id == Workspace.id)
        .where(
            Workspace.organization_id == org_id,
            (
                exists(
                    select(DerivedContent.relative_path).where(
                        DerivedContent.relative_path == include_subquery.c.relative_path
                    )
                )
            )
            | (
                exists(
                    select(DerivedContent.relative_path).where(
                        DerivedContent.relative_path.startswith(
                            include_subquery.c.relative_path + "/"
                        )
                    )
                )
            ),
        )
    )
    return query
