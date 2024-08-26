from pathlib import Path
from uuid import UUID

from database.models_v1 import DerivedContent, Workspace
from sqlalchemy import func
from sqlmodel import Session, or_, select


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
        # The relative path for the current include_id, trimmed of any trailing slashes
        content_path_query = (
            select(func.rtrim(DerivedContent.relative_path, "/"))
            .where(DerivedContent.id == include_id)
            .limit(1)
        ).scalar_subquery()

        path = func.rtrim(DerivedContent.relative_path, "/")
        exact_path_match_condition = path == content_path_query
        child_path_match_condition = path.startswith(content_path_query + "/")
        path_conditions.extend([exact_path_match_condition, child_path_match_condition])

    if path_conditions:
        content_for_org_query = content_for_org_query.where(or_(*path_conditions))

    return content_for_org_query


def build_resolve_paths_query(
    org_id: str,
    include_ids: list[UUID] | None = None,
):
    """
    Constructs a SQL query to fetch unique, normalized relative paths associated with the given content IDs.

    This function generates a query that retrieves distinct `relative_path` entries associated with a specific
    organization (`org_id`) based on a list of `include_ids`. Paths are normalized to remove trailing slashes.

    This function does NOT smartly attempt find the shortest path to include. It simply includes the paths as they are.
    """

    if not org_id:
        raise ValueError("Organization ID cannot be empty.")

    path_query = (
        select(func.distinct(func.rtrim(DerivedContent.relative_path, "/")))
        .join(Workspace, DerivedContent.workspace_id == Workspace.id)
        .where(Workspace.organization_id == org_id)
    )

    if include_ids:
        path_query = path_query.where(DerivedContent.id.in_(include_ids))

    return path_query


def find_minimal_inclusion_paths(paths: list[str]) -> set[str]:
    """
    Given a list of paths, returns the minimal set of paths to include, filtering out any paths
    that are already included by a parent path.
    """
    path_objects = [Path(path) for path in paths]
    path_objects.sort()

    minimal_paths = []
    for path in path_objects:
        if not any(path.is_relative_to(parent) for parent in minimal_paths):
            minimal_paths.append(path)

    return {str(path) for path in minimal_paths}


def content_ids_to_minimal_paths(
    sesh: Session,
    org_id: str,
    include_ids: list[UUID],
) -> set[str]:
    """
    Given a list of content IDs, returns the minimal set of associated paths to include, filtering out any paths
    that are already included by a parent path.
    """
    query = build_resolve_paths_query(org_id, include_ids)
    paths = sesh.exec(query).all()
    return find_minimal_inclusion_paths(paths)


if __name__ == "__main__":
    """
    Test script for content resolution.
    """

    from pprint import PrettyPrinter

    from database.db import dev_engine
    from sqlalchemy.orm import selectinload
    from sqlmodel import Session

    pp = PrettyPrinter(indent=4)

    with Session(dev_engine) as session:
        org_id = ""
        include_ids = []
        query = build_resolve_content_query(org_id, include_ids).options(
            selectinload(DerivedContent.content_type)
        )
        results = session.exec(query).all()

        for result in results:
            print(f"{result.content_type.type_name:<20} {result.relative_path}")
