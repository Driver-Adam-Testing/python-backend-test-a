# mypy: disable_error_code="call-arg"
import strawberry
from database.models_v1 import SourceContent, SourceContentType, Workspace
from sqlmodel import Session, select

from app.api.routes.legacy.scalars import ID


class NodeTypeEnum:
    Directory = "directory"
    File = "file"
    Resource = "resource"
    Workspace = "workspace"


@strawberry.type
class FlatNode:
    id: ID
    name: str | None
    path: str | None  # TODO: relative_path is renamed path. There's a lot of transformation.
    kind: str | None
    children: list[str] | None = strawberry.field(default_factory=list)


def get_codebase_tree(
    codebase_id: str, session: Session, organization_id: str
) -> list[FlatNode]:
    statement = (
        select(SourceContent, SourceContentType)
        .join(Workspace)
        .where(SourceContent.codebase_id == codebase_id)
        .where(Workspace.id == SourceContent.workspace_id)
        .where(Workspace.organization_id == organization_id)
        .where(SourceContentType.type_name.in_(["codebase-directory", "codebase-file"]))  # type: ignore
        .where(SourceContentType.id == SourceContent.content_type_id)
    )

    source_contents = session.exec(statement).all()

    directories_map = {}
    files = []

    for content, source_content_type in source_contents:
        path_parts = content.relative_path.rstrip("/").split("/")
        name = path_parts[-1]
        kind = (
            NodeTypeEnum.Directory
            if source_content_type.type_name == "codebase-directory"
            else NodeTypeEnum.File
        )
        node = FlatNode(  # type: ignore
            id=ID(content.id),
            name=name,
            path=content.relative_path,
            kind=kind,
            children=[],
        )
        if kind == NodeTypeEnum.File:
            files.append(node)
        else:
            directories_map[content.relative_path] = node

    for file in files:
        parent_path = file.path.rsplit("/", 1)[0]  # type: ignore
        if parent_path in directories_map:
            if directories_map[parent_path].children is None:
                directories_map[parent_path].children = []
            directories_map[parent_path].children.append(file.path)  # type: ignore
        if file.path:
            directories_map[file.path] = file

    result = []
    for _, dir_node in directories_map.items():
        if dir_node.children is not None:
            dir_node.children = [
                child
                for child in dir_node.children
                if child in directories_map  # type: ignore
            ]
        result.append(dir_node)

    return result
