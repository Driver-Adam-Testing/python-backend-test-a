from datetime import datetime
from typing import Generic, TypeVar
from uuid import UUID

from app.api.auth import UserToken
from app.api.routes.v2.node_schemas import (
    DocumentSourceRead,
    NodeReadWithRelationships,
    PrimaryAssetCreate,
    PrimaryAssetRead,
    PrimaryAssetUpdate,
    TagCreate,
    TagRead,
    VersionCreate,
    VersionUpdate,
)
from app.api.session import CurrentSession
from database.models_v1 import DerivedContent, DocumentSource, Tag
from database.models_v2 import (
    Node,
    NodeKind,
    PrimaryAsset,
    PrimaryAssetKind,
    PrimaryAssetTag,
    Version,
)
from database.models_v2_enums import VersionStatus
from fastapi import APIRouter, Body, HTTPException, Path, Request, Response
from pydantic import BaseModel
from sqlalchemy.orm import selectinload
from sqlmodel import func, select

T = TypeVar("T")


class ListWithCount(BaseModel, Generic[T]):
    results: list[T]
    total_count: int


router = APIRouter()


@router.get("/primary_assets", response_model=ListWithCount[PrimaryAssetRead])
def list_primary_assets(
    request: Request,
    session: CurrentSession,
    user: UserToken,
    limit: int = 10,
    offset: int = 0,
    sort_by: str = "updated_at",
    sort_direction: str = "DESC",
) -> ListWithCount[PrimaryAssetRead]:
    query = select(PrimaryAsset).where(
        PrimaryAsset.organization_id == user.organization_id
    )
    # TODO these should be explicit in the function parameters so they get properly validated. See old content endpoint
    filters = dict(request.query_params)
    filters.pop("limit", None)
    filters.pop("offset", None)
    filters.pop("sort_by", None)
    filters.pop("sort_direction", None)
    tag_ids = filters.pop("tag_ids", None)
    kind = filters.pop("primary_asset_type", None)
    if not kind:
        kind = filters.pop("kind", None)

    if kind:
        if isinstance(kind, str):
            kind = kind.split(",")
            query = query.where(PrimaryAsset.kind == PrimaryAssetKind(kind))
        if isinstance(kind, list):
            kind = [
                PrimaryAssetKind(k) for k in kind
            ]  # TODO these may be invalid. If we move it to the endpoint parameters, fastapi will validate them
            query = query.where(PrimaryAsset.kind.in_(kind))

    if tag_ids:
        query = query.where(
            select(PrimaryAssetTag)
            .where(PrimaryAssetTag.primary_asset_id == PrimaryAsset.id)
            .where(PrimaryAssetTag.tag_id.in_(tag_ids.split(",")))
            .exists()
        )

    for key, value in filters.items():
        print(key, value)
        if hasattr(PrimaryAsset, key):
            query = query.where(getattr(PrimaryAsset, key) == value)
        elif key.startswith("version.") and hasattr(Version, key.split(".", 1)[1]):
            version_key = key.split(".", 1)[1]
            query = query.where(
                select(Version)
                .where(getattr(Version, version_key) == value)
                .where(Version.primary_asset_id == PrimaryAsset.id)
                .exists()
            )
        elif key.startswith("node.") and hasattr(Node, key.split(".", 1)[1]):
            node_key = key.split(".", 1)[1]
            query = query.where(
                select(Node)
                .join(Version)
                .where(getattr(Node, node_key) == value)
                .where(Version.primary_asset_id == PrimaryAsset.id)
                .exists()
            )

    if hasattr(PrimaryAsset, sort_by):
        if sort_direction.upper() == "ASC":
            query = query.order_by(getattr(PrimaryAsset, sort_by).asc())
        elif sort_direction.upper() == "DESC":
            query = query.order_by(getattr(PrimaryAsset, sort_by).desc())
        else:
            raise HTTPException(status_code=400, detail="Invalid sort direction")
    else:
        raise HTTPException(status_code=400, detail="Invalid sort field")

    count_query = select(func.count()).select_from(query.subquery())
    total_count = session.exec(count_query).one()

    query = query.limit(limit).offset(offset)
    result = session.exec(query)
    primary_assets = result.all()

    return ListWithCount(results=primary_assets, total_count=total_count)


@router.get("/document_sources", response_model=ListWithCount[DocumentSourceRead])
async def list_document_sources(
    request: Request,
    session: CurrentSession,
    user: UserToken,
    limit: int = 10,
    offset: int = 0,
    sort_direction: str = "DESC",
    sort_by: str | None = None,
) -> ListWithCount[DocumentSourceRead]:
    query = select(DocumentSource).options(
        selectinload(DocumentSource.source_node)
        .selectinload(Node.version)
        .selectinload(Version.primary_asset)
    )
    filters = dict(request.query_params)
    filters.pop("limit", None)
    filters.pop("offset", None)
    filters.pop("sort_by", None)
    filters.pop("sort_direction", None)

    for key, value in filters.items():
        if hasattr(DocumentSource, key):
            query = query.where(getattr(DocumentSource, key) == value)

    if sort_by:
        if hasattr(DocumentSource, sort_by):
            if sort_direction.upper() == "ASC":
                query = query.order_by(getattr(DocumentSource, sort_by).asc())
            elif sort_direction.upper() == "DESC":
                query = query.order_by(getattr(DocumentSource, sort_by).desc())
            else:
                raise HTTPException(status_code=400, detail="Invalid sort direction")
        else:
            raise HTTPException(status_code=400, detail="Invalid sort field")

    count_query = select(func.count()).select_from(query.subquery())
    total_count = session.exec(count_query).one()

    query = query.limit(limit).offset(offset)
    result = session.exec(query)
    document_sources = result.all()

    return ListWithCount(results=document_sources, total_count=total_count)


@router.get("/versions", response_model=ListWithCount[Version])
def list_versions(
    request: Request,
    session: CurrentSession,
    user: UserToken,
    limit: int = 10,
    offset: int = 0,
    sort_by: str = "updated_at",
    sort_direction: str = "DESC",
) -> ListWithCount[Version]:
    query = (
        select(Version)
        .join(PrimaryAsset)
        .where(PrimaryAsset.organization_id == user.organization_id)
    )

    filters = dict(request.query_params)
    filters.pop("limit", None)
    filters.pop("offset", None)
    filters.pop("sort_by", None)
    filters.pop("sort_direction", None)

    for key, value in filters.items():
        if hasattr(Version, key):
            query = query.where(getattr(Version, key) == value)

    if hasattr(Version, sort_by):
        if sort_direction.upper() == "ASC":
            query = query.order_by(getattr(Version, sort_by).asc())
        elif sort_direction.upper() == "DESC":
            query = query.order_by(getattr(Version, sort_by).desc())
        else:
            raise HTTPException(status_code=400, detail="Invalid sort direction")
    else:
        raise HTTPException(status_code=400, detail="Invalid sort field")

    count_query = select(func.count()).select_from(query.subquery())
    total_count = session.exec(count_query).one()

    query = query.limit(limit).offset(offset)
    result = session.exec(query)
    versions = result.all()

    if not versions:
        raise HTTPException(status_code=404, detail="No versions found")

    return ListWithCount(results=versions, total_count=total_count)


@router.get("/nodes", response_model=ListWithCount[NodeReadWithRelationships])
def list_nodes(
    request: Request,
    session: CurrentSession,
    user: UserToken,
    limit: int = 10,
    offset: int = 0,
    sort_by: str = "updated_at",
    sort_direction: str = "DESC",
) -> ListWithCount[Node]:
    query = (
        select(Node)
        .join(Version)
        .join(PrimaryAsset)
        .where(PrimaryAsset.organization_id == user.organization_id)
    )

    filters = dict(request.query_params)
    filters.pop("limit", None)
    filters.pop("offset", None)
    filters.pop("sort_by", None)
    filters.pop("sort_direction", None)

    for key, value in filters.items():
        if hasattr(Node, key):
            query = query.where(getattr(Node, key) == value)

    if hasattr(Node, sort_by):
        if sort_direction.upper() == "ASC":
            query = query.order_by(getattr(Node, sort_by).asc())
        elif sort_direction.upper() == "DESC":
            query = query.order_by(getattr(Node, sort_by).desc())
        else:
            raise HTTPException(status_code=400, detail="Invalid sort direction")
    else:
        raise HTTPException(status_code=400, detail="Invalid sort field")

    count_query = select(func.count()).select_from(query.subquery())
    total_count = session.exec(count_query).one()

    query = query.limit(limit).offset(offset)
    result = session.exec(query)
    nodes = result.all()

    if not nodes:
        raise HTTPException(status_code=404, detail="No nodes found")

    return ListWithCount(results=nodes, total_count=total_count)


# TODO: Put this in enums and make all the classes "Read" Classes
class DerivedContentResponse(BaseModel):
    id: UUID | None
    node_id: UUID | None
    content: str | None
    misc_metadata: dict | None
    created_at: datetime | None
    updated_at: datetime | None
    node: Node
    version: Version
    primary_asset: PrimaryAsset

    @classmethod
    def from_derived_content(
        cls, derived_content: DerivedContent
    ) -> "DerivedContentResponse":
        return cls(
            id=derived_content.id,
            node_id=derived_content.node_id,
            relative_path=derived_content.relative_path,
            content=derived_content.content,
            content_name=derived_content.content_name,
            misc_metadata=derived_content.misc_metadata,
            created_at=derived_content.created_at,
            updated_at=derived_content.updated_at,
            order=derived_content.order,
            version_id=derived_content.node.version_id,
            status=derived_content.node.version.status,
            node=derived_content.node,
            version=derived_content.node.version,
            primary_asset=derived_content.node.version.primary_asset,
        )


@router.get("/contents", response_model=ListWithCount[DerivedContentResponse])
def list_contents(
    request: Request,
    session: CurrentSession,
    user: UserToken,
    limit: int = 10,
    offset: int = 0,
    sort_by: str = "updated_at",
    sort_direction: str = "DESC",
) -> ListWithCount[DerivedContentResponse]:
    query = (
        select(DerivedContent)
        .options(
            selectinload(DerivedContent.node)
            .selectinload(Node.version)
            .selectinload(Version.primary_asset)
            .selectinload(PrimaryAsset.tags)
        )
        .where(
            DerivedContent.node.has(
                Node.version.has(
                    Version.primary_asset.has(
                        PrimaryAsset.organization_id == user.organization_id
                    )
                )
            )
        )
    )

    filters = dict(request.query_params)
    filters.pop("limit", None)
    filters.pop("offset", None)
    filters.pop("sort_by", None)
    filters.pop("sort_direction", None)

    for key, value in filters.items():
        if hasattr(DerivedContent, key):
            query = query.where(getattr(DerivedContent, key) == value)

    if hasattr(DerivedContent, sort_by):
        if sort_direction.upper() == "ASC":
            query = query.order_by(getattr(DerivedContent, sort_by).asc())
        elif sort_direction.upper() == "DESC":
            query = query.order_by(getattr(DerivedContent, sort_by).desc())
        else:
            raise HTTPException(status_code=400, detail="Invalid sort direction")
    else:
        raise HTTPException(status_code=400, detail="Invalid sort field")

    count_query = select(func.count()).select_from(query.subquery())
    total_count = session.exec(count_query).one()

    query = query.limit(limit).offset(offset)
    result = session.exec(query)
    contents_with_full_node = result.all()

    if not contents_with_full_node:
        raise HTTPException(status_code=404, detail="No contents found")

    # Use DerivedContentResponse to populate the response
    contents = [
        DerivedContentResponse.from_derived_content(derived_content)
        for derived_content in contents_with_full_node
    ]

    return ListWithCount(results=contents, total_count=total_count)


@router.post("/primary_assets", response_model=PrimaryAsset)
def create_primary_asset(
    session: CurrentSession,
    user: UserToken,
    payload: PrimaryAssetCreate = Body(...),
) -> PrimaryAsset:
    new_asset = PrimaryAsset(
        display_name=payload.display_name,
        organization_id=user.organization_id,
        kind=payload.kind,
    )
    session.add(new_asset)
    session.commit()
    session.refresh(new_asset)
    return new_asset


@router.put("/primary_assets/{asset_id}", response_model=PrimaryAsset)
def update_primary_asset(
    session: CurrentSession,
    user: UserToken,
    asset_id: UUID = Path(...),
    payload: PrimaryAssetUpdate = Body(...),
) -> PrimaryAsset:
    # Fetch the asset to be updated
    asset = session.exec(
        select(PrimaryAsset)
        .where(PrimaryAsset.id == asset_id)
        .where(PrimaryAsset.organization_id == user.organization_id)
    ).one_or_none()

    if not asset:
        raise HTTPException(status_code=404, detail="Primary asset not found")

    # Update fields if provided
    if payload.display_name is not None:
        asset.display_name = payload.display_name
    if payload.kind is not None:
        asset.kind = payload.kind

    session.add(asset)
    session.commit()
    session.refresh(asset)
    return asset


@router.post("/versions", response_model=Version)
def create_version(
    session: CurrentSession,
    user: UserToken,
    payload: VersionCreate = Body(...),
) -> Version:
    # Ensure that the primary asset belongs to the user's organization
    primary_asset = session.exec(
        select(PrimaryAsset)
        .where(PrimaryAsset.id == payload.primary_asset_id)
        .where(PrimaryAsset.organization_id == user.organization_id)
    ).one_or_none()

    if not primary_asset:
        raise HTTPException(status_code=404, detail="Primary asset not found")

    new_version = Version(**payload.dict())
    session.add(new_version)
    session.commit()
    session.refresh(new_version)
    return new_version


@router.put("/versions/{version_id}", response_model=Version)
def update_version(
    session: CurrentSession,
    user: UserToken,
    version_id: UUID = Path(...),
    payload: VersionUpdate = Body(...),
) -> Version:
    version = session.exec(
        select(Version)
        .join(PrimaryAsset)
        .where(Version.id == version_id)
        .where(PrimaryAsset.organization_id == user.organization_id)
    ).one_or_none()

    if not version:
        raise HTTPException(status_code=404, detail="Version not found")

    if payload.display_name is not None:
        version.display_name = payload.display_name
    if payload.status is not None:
        version.status = payload.status

    session.add(version)
    session.commit()
    session.refresh(version)
    return version


class NodeCreate(BaseModel):
    version_id: UUID
    relative_path: str


class NodeUpdate(BaseModel):
    relative_path: str | None = None


@router.post("/nodes", response_model=Node)
def create_node(
    session: CurrentSession, user: UserToken, payload: NodeCreate = Body(...)
) -> Node:
    # Verify version belongs to user's organization
    version = session.exec(
        select(Version)
        .join(PrimaryAsset)
        .where(Version.id == payload.version_id)
        .where(PrimaryAsset.organization_id == user.organization_id)
    ).one_or_none()

    if not version:
        raise HTTPException(
            status_code=404, detail="Version not found or not authorized"
        )

    new_node = Node(
        version_id=payload.version_id,
        relative_path=payload.relative_path,
    )
    session.add(new_node)
    session.commit()
    session.refresh(new_node)
    return new_node


@router.put("/nodes/{node_id}", response_model=Node)
def update_node(
    session: CurrentSession,
    user: UserToken,
    node_id: UUID = Path(...),
    payload: NodeUpdate = Body(...),
) -> Node:
    # Fetch the node and ensure it belongs to the user's organization
    node = session.exec(
        select(Node)
        .join(Version)
        .join(PrimaryAsset)
        .where(Node.id == node_id)
        .where(PrimaryAsset.organization_id == user.organization_id)
    ).one_or_none()

    if not node:
        raise HTTPException(status_code=404, detail="Node not found or not authorized")

    if payload.relative_path is not None:
        node.relative_path = payload.relative_path

    session.add(node)
    session.commit()
    session.refresh(node)
    return node


class DerivedContentCreate(BaseModel):
    node_id: UUID
    content_type_id: UUID
    relative_path: str
    content: str | None = None
    content_name: str | None = None
    misc_metadata: dict | None = None
    status: str | None = None
    order: int | None = None
    # For tags, you might want to create them separately or link existing tags.
    # Here we assume tags are handled elsewhere or via another endpoint.


class DerivedContentUpdate(BaseModel):
    content: str | None = None
    content_name: str | None = None


@router.post("/contents", response_model=DerivedContentResponse)
def create_derived_content(
    session: CurrentSession, user: UserToken, payload: DerivedContentCreate = Body(...)
) -> DerivedContentResponse:
    # Verify node belongs to user's organization
    node = session.exec(
        select(Node)
        .join(Version)
        .join(PrimaryAsset)
        .where(Node.id == payload.node_id)
        .where(PrimaryAsset.organization_id == user.organization_id)
    ).one_or_none()

    if not node:
        raise HTTPException(status_code=404, detail="Node not found or not authorized")

    new_content = DerivedContent(
        node_id=payload.node_id,
        content_type_id=payload.content_type_id,
        relative_path=payload.relative_path,
        content=payload.content,
        content_name=payload.content_name,
        misc_metadata=payload.misc_metadata,
        status=payload.status,
        order=payload.order,
    )
    session.add(new_content)
    session.commit()
    session.refresh(new_content)

    return DerivedContentResponse.from_derived_content(new_content)


# TODO: I want this to be explicitly operating on a CONCEPTUAL entity of a PAGE, rather than an explicit entity in the DB
@router.put("/edit_page/{node_id}", response_model=DerivedContentResponse)
def edit_page_CONVENIENCE_METHOD(
    session: CurrentSession,
    user: UserToken,
    node_id: UUID = Path(...),
    payload: DerivedContentUpdate = Body(...),
) -> Response:
    # Fetch the derived content and ensure it belongs to the user's organization
    derived_content = session.exec(
        select(DerivedContent)
        .join(Node)
        .join(Version)
        .join(PrimaryAsset)
        .where(Node.id == node_id)
        .where(PrimaryAsset.organization_id == user.organization_id)
    ).one_or_none()

    if not derived_content:
        raise HTTPException(
            status_code=404, detail="Content not found or not authorized"
        )

    if payload.content is not None:
        derived_content.content = payload.content
    if payload.content_name is not None:
        derived_content.content_name = payload.content_name
        primary_asset = session.exec(
            select(PrimaryAsset)
            .join(Version)
            .join(Node)
            .where(Node.id == derived_content.node_id)
            .where(
                PrimaryAsset.kind.in_(
                    [PrimaryAssetKind.PAGE, PrimaryAssetKind.PAGE_TEMPLATE]
                )
            )
        ).one_or_none()

        if primary_asset:
            primary_asset.display_name = payload.content_name
            session.add(primary_asset)

    session.add(derived_content)
    session.commit()
    session.refresh(derived_content)

    return Response(status_code=202)


## ALERT: THIS IS A CONVENIENCE METHOD


@router.post("/new_page", response_model=DerivedContentResponse)
def new_page(session: CurrentSession, user: UserToken) -> DerivedContentResponse:
    # Find all PrimaryAssetRows with the name "Untitled Page X" where X is any number for the user's organization
    existing_assets = session.exec(
        select(PrimaryAsset).where(
            PrimaryAsset.display_name.like("Untitled Page %"),
            PrimaryAsset.organization_id == user.organization_id,
        )
    ).all()

    # Extract numbers from the existing asset names and find the maximum
    max_number = 0
    for asset in existing_assets:
        try:
            number = int(asset.display_name.split(" ")[-1])
            if number > max_number:
                max_number = number
        except ValueError:
            continue

    # Create a new PrimaryAssetRow with the incremented number
    new_display_name = f"Untitled Page {max_number + 1}"
    new_primary_asset = PrimaryAsset(
        display_name=new_display_name,
        organization_id=user.organization_id,
        kind=PrimaryAssetKind.PAGE,
    )
    session.add(new_primary_asset)
    session.commit()

    new_version = Version(
        primary_asset_id=new_primary_asset.id,
        display_name="0",
        status=VersionStatus.GENERATION_COMPLETE,
    )
    session.add(new_version)
    session.commit()

    new_node = Node(
        version_id=new_version.id, relative_path="/page", kind=NodeKind.OTHER
    )
    session.add(new_node)
    session.commit()

    new_derived_content = DerivedContent(
        content_type_id=None,
        content_kind="application_note",
        node_id=new_node.id,
        relative_path="/page",
        content="",
        content_name=new_display_name,
        misc_metadata={},
        status="generation-complete",
        version_id=None,
    )
    session.add(new_derived_content)
    session.commit()
    return DerivedContentResponse.from_derived_content(new_derived_content)


@router.post("/new_template", response_model=DerivedContentResponse)
def new_template(
    session: CurrentSession,
    user: UserToken,
) -> DerivedContentResponse:
    # Query existing assets with similar names
    existing_assets = session.exec(
        select(PrimaryAsset).where(
            PrimaryAsset.display_name.like("Untitled Template %"),
            PrimaryAsset.organization_id == user.organization_id,
        )
    ).all()

    # Extract numbers from the existing asset names and find the maximum
    max_number = 0
    for asset in existing_assets:
        try:
            number = int(asset.display_name.split(" ")[-1])
            if number > max_number:
                max_number = number
        except ValueError:
            continue

    # Create a new PrimaryAssetRow with the incremented number
    new_display_name = f"Untitled Template {max_number + 1}"
    new_primary_asset = PrimaryAsset(
        display_name=new_display_name,
        organization_id=user.organization_id,
        kind=PrimaryAssetKind.PAGE_TEMPLATE,
    )
    session.add(new_primary_asset)
    session.commit()

    new_version = Version(
        primary_asset_id=new_primary_asset.id,
        display_name="0",
        status=VersionStatus.GENERATION_COMPLETE,
    )
    session.add(new_version)
    session.commit()

    new_node = Node(
        version_id=new_version.id, relative_path="/template", kind=NodeKind.OTHER
    )
    session.add(new_node)
    session.commit()

    new_derived_content = DerivedContent(
        content_type_id=None,
        content_kind="template",
        node_id=new_node.id,
        relative_path="/template",
        content="",
        content_name=new_display_name,
        misc_metadata={},
        status="generation-complete",
        version_id=None,
    )

    session.add(new_derived_content)
    session.commit()
    return DerivedContentResponse.from_derived_content(new_derived_content)


@router.get("/tags", response_model=ListWithCount[TagRead])
def list_tags(
    request: Request,
    session: CurrentSession,
    user: UserToken,
    limit: int = 10,
    offset: int = 0,
    sort_by: str = "created_at",
    sort_direction: str = "DESC",
) -> ListWithCount[TagRead]:
    query = select(Tag).where(Tag.organization_id == user.organization_id)

    filters = dict(request.query_params)
    filters.pop("limit", None)
    filters.pop("offset", None)
    filters.pop("sort_by", None)
    filters.pop("sort_direction", None)

    for key, value in filters.items():
        if hasattr(Tag, key):
            query = query.where(getattr(Tag, key) == value)

    if hasattr(Tag, sort_by):
        if sort_direction.upper() == "ASC":
            query = query.order_by(getattr(Tag, sort_by).asc())
        elif sort_direction.upper() == "DESC":
            query = query.order_by(getattr(Tag, sort_by).desc())
        else:
            raise HTTPException(status_code=400, detail="Invalid sort direction")
    else:
        raise HTTPException(status_code=400, detail="Invalid sort field")

    count_query = select(func.count()).select_from(query.subquery())
    total_count = session.exec(count_query).one()

    query = query.limit(limit).offset(offset)
    result = session.exec(query)
    tags = result.all()

    if not tags:
        raise HTTPException(status_code=404, detail="No tags found")

    return ListWithCount(results=tags, total_count=total_count)


@router.post("/tags", response_model=TagRead)
def create_tag(
    session: CurrentSession,
    user: UserToken,
    payload: TagCreate = Body(...),
) -> TagRead:
    # Create a new Tag
    new_tag = Tag(
        name=payload.name,
        organization_id=user.organization_id,
        hex_color=payload.hex_color,
        type="tag",
        created_by=user.user_id,
        updated_by=user.user_id,
    )
    session.add(new_tag)
    session.commit()
    session.refresh(new_tag)
    return new_tag


@router.put("/tags/{tag_id}", response_model=TagRead)
def update_tag(
    session: CurrentSession,
    user: UserToken,
    tag_id: UUID = Path(...),
    payload: TagCreate = Body(...),
) -> TagRead:
    tag = session.exec(
        select(Tag)
        .where(Tag.id == tag_id)
        .where(Tag.organization_id == user.organization_id)
    ).one_or_none()

    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    if payload.name is not None:
        tag.name = payload.name
    if payload.hex_color is not None:
        tag.hex_color = payload.hex_color
    if payload.type is not None:
        tag.type = payload.type

    tag.updated_by = user.user_id

    session.add(tag)
    session.commit()
    session.refresh(tag)
    return tag


@router.post("/primary_asset_tags", response_model=PrimaryAssetTag)
def create_primary_asset_tag(
    session: CurrentSession,
    user: UserToken,
    payload: PrimaryAssetTag = Body(...),
) -> PrimaryAssetTag:
    new_primary_asset_tag = PrimaryAssetTag(
        tag_id=payload.tag_id,
        primary_asset_id=payload.primary_asset_id,
    )
    session.add(new_primary_asset_tag)
    session.commit()
    session.refresh(new_primary_asset_tag)
    return new_primary_asset_tag


@router.delete("/primary_asset_tags/{primary_asset_id}/{tag_id}", response_model=None)
def delete_primary_asset_tag(
    session: CurrentSession,
    user: UserToken,
    tag_id: UUID = Path(...),
    primary_asset_id: UUID = Path(...),
) -> Response:
    primary_asset_tag = session.exec(
        select(PrimaryAssetTag)
        .join(PrimaryAsset)
        .where(PrimaryAssetTag.tag_id == tag_id)
        .where(PrimaryAssetTag.primary_asset_id == primary_asset_id)
        .where(PrimaryAsset.organization_id == user.organization_id)
    ).one_or_none()

    if not primary_asset_tag:
        raise HTTPException(
            status_code=404, detail="PrimaryAssetTag not found or not authorized"
        )

    session.delete(primary_asset_tag)
    session.commit()
    return Response(status_code=204)
