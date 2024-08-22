from uuid import UUID

from database.models_v1 import DerivedContent, Workspace
from sqlmodel import or_, select


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

    content_for_org_query = (
        select(DerivedContent)
        .join(Workspace, DerivedContent.workspace_id == Workspace.id)
        .where(Workspace.organization_id == org_id)
    )

    path_conditions = []
    for include_id in include_ids:
        # The relative path for the current include_id
        path = (
            select(DerivedContent.relative_path)
            .where(DerivedContent.id == include_id)
            .limit(1)
        ).scalar_subquery()

        exact_path_match_condition = DerivedContent.relative_path == path
        child_path_match_condition = DerivedContent.relative_path.startswith(path + "/")
        path_conditions.extend([exact_path_match_condition, child_path_match_condition])

    if path_conditions:
        content_for_org_query = content_for_org_query.where(or_(*path_conditions))

    return content_for_org_query
