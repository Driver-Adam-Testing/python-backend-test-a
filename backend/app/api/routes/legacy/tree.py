# mypy: disable_error_code="call-arg"

import strawberry
from app.api.routes.legacy.scalars import ID
from database.models_v2 import NodeRow, PrimaryAssetRow, VersionRow
from sqlmodel import Session, select


class NodeTypeEnum:
    Directory = "directory"
    File = "file"
    Resource = "resource"
    Workspace = "workspace"


@strawberry.type
class FlatNode:
    id: ID
    name: str | None
    path: str | None  # relative_path renamed to path
    kind: str | None
    children: list[str] | None = strawberry.field(default_factory=list)


def get_codebase_tree(
    codebase_id: str,  # codebase_id now corresponds to PrimaryAssetRow.id
    session: Session,
    organization_id: str,
    version_id: str | None = None,
) -> list[FlatNode]:
    # INSERT_YOUR_REWRITE_HERE
    # Perform a single query to fetch all necessary data
    if not version_id:
        # Fetch the most recent version if version_id is not provided
        most_recent_version = session.exec(
            select(VersionRow.id)
            .join(PrimaryAssetRow, VersionRow.primary_asset_id == PrimaryAssetRow.id)
            .where(PrimaryAssetRow.id == codebase_id)
            .where(PrimaryAssetRow.organization_id == organization_id)
            .order_by(VersionRow.created_at.desc())
            .limit(1)
        ).first()
        version_id = most_recent_version if most_recent_version else None

    nodes = session.exec(
        select(NodeRow, VersionRow, PrimaryAssetRow)
        .join(VersionRow, NodeRow.version_id == VersionRow.id)
        .join(PrimaryAssetRow, VersionRow.primary_asset_id == PrimaryAssetRow.id)
        .where(PrimaryAssetRow.id == codebase_id)
        .where(PrimaryAssetRow.organization_id == organization_id)
        .where((VersionRow.id == version_id) if version_id else True)
    ).all()

    # If no nodes found, return an empty list
    if not nodes:
        return []

    # Construct the node tree
    directories_map = {}
    files = []

    for node, _, _ in nodes:
        # Determine if it's a directory or file
        if node.relative_path.endswith("/"):
            kind = NodeTypeEnum.Directory
            name = (
                node.relative_path.rstrip("/").split("/")[-1]
                if node.relative_path
                else ""
            )
        else:
            kind = NodeTypeEnum.File
            name = node.relative_path.split("/")[-1] if node.relative_path else ""

        flat_node = FlatNode(
            id=ID(str(node.id)),
            name=name,
            path=node.relative_path,
            kind=kind,
            children=[],
        )

        if kind == NodeTypeEnum.File:
            files.append(flat_node)
        else:
            directories_map[node.relative_path] = flat_node

    for file_node in files:
        if file_node.path and "/" in file_node.path:
            parent_path = file_node.path.rsplit("/", 1)[0] + "/"
        else:
            parent_path = ""

        if parent_path in directories_map:
            if directories_map[parent_path].children is None:
                directories_map[parent_path].children = []
            directories_map[parent_path].children.append(file_node.path)

        directories_map[file_node.path] = file_node

    result = []
    for _, dir_node in directories_map.items():
        if dir_node.children is not None:
            dir_node.children = [
                child_path
                for child_path in dir_node.children
                if child_path in directories_map
            ]
        result.append(dir_node)

    return result
