from uuid import UUID

from database.models_v1 import DerivedContent
from database.models_v2 import (
    Node,
    NodeKind,
    PrimaryAsset,
    PrimaryAssetKind,
    UserCache,
    Version,
    VersionCreator,
)
from database.models_v2_enums import PrimaryAssetProvider, VersionStatus
from fastapi import Body, HTTPException, Path, Response
from sqlmodel import select

from app.api.auth import UserToken
from app.api.routes.v2.router import router
from app.api.routes.v2.schemas import (
    ContentDetailRead,
    DerivedContentUpdate,
)
from app.api.session import CurrentSession


@router.put("/edit_page/{node_id}", response_model=None)
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


@router.post("/new_page", response_model=ContentDetailRead)
def new_page(session: CurrentSession, user: UserToken) -> ContentDetailRead:
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
        provider=PrimaryAssetProvider.USER,
    )
    session.add(new_primary_asset)
    session.commit()

    creator = session.exec(
        select(UserCache).where(UserCache.id == user.user_id)
    ).one_or_none()
    if creator is None:
        creator = UserCache(id=user.user_id, full_name=user.full_name, email=user.email)
        session.add(creator)
        session.commit()
        session.refresh(creator)

    new_version = Version(
        primary_asset_id=new_primary_asset.id,
        vcs_hash=None,
        status=VersionStatus.GENERATION_COMPLETE,
        vcs_metadata=None,
    )
    session.add(new_version)
    session.commit()

    new_version_creator = VersionCreator(version_id=new_version.id, user_id=creator.id)
    session.add(new_version_creator)
    session.commit()

    new_node = Node(
        version_id=new_version.id, relative_path="page", kind=NodeKind.OTHER
    )
    session.add(new_node)
    session.commit()

    new_derived_content = DerivedContent(
        content_kind="application_note",
        node_id=new_node.id,
        relative_path="page",
        content="",
        content_name=new_display_name,
        misc_metadata={},
    )
    session.add(new_derived_content)
    session.commit()
    session.refresh(new_derived_content)

    # Ensure the node relationship is populated
    new_derived_content.node = new_node

    return ContentDetailRead.model_validate(new_derived_content)


@router.post("/new_template", response_model=ContentDetailRead)
def new_template(
    session: CurrentSession,
    user: UserToken,
) -> ContentDetailRead:
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
        provider=PrimaryAssetProvider.USER,
    )
    session.add(new_primary_asset)
    session.commit()

    new_version = Version(
        vcs_hash=None,
        status=VersionStatus.GENERATION_COMPLETE,
        vcs_metadata=None,
    )
    new_version.primary_asset = new_primary_asset
    session.add(new_version)
    session.commit()

    new_node = Node(
        relative_path="template",
        kind=NodeKind.OTHER,
    )
    new_node.version = new_version
    session.add(new_node)
    session.commit()

    new_derived_content = DerivedContent(
        content_kind="template",
        relative_path="template",
        content="",
        content_name=new_display_name,
        misc_metadata={},
    )
    new_derived_content.node = new_node
    session.add(new_derived_content)
    session.commit()
    session.refresh(new_derived_content)

    return ContentDetailRead.model_validate(new_derived_content)
