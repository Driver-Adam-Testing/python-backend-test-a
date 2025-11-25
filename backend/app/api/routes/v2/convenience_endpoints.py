from uuid import UUID

from database.models import (
    DerivedContent,
    DocumentSource,
    Node,
    PrimaryAsset,
    UserCache,
    Version,
    VersionCreator,
    VersionNode,
)
from database.models_enums import (
    NodeKind,
    PrimaryAssetKind,
    PrimaryAssetProvider,
    VersionStatus,
)
from fastapi import Body, HTTPException, Path, Response
from sqlalchemy.orm import selectinload
from sqlmodel import select

from app.api.auth import UserToken
from app.api.routes.v2.router import router
from app.api.routes.v2.schemas import (
    DerivedContentUpdate,
    NewPageResponse,
)
from app.api.session import CurrentSession
from app.authorization.fastapi import enforce_asset_action, enforce_org_membership


@router.put("/edit_page/{version_node_id}", response_model=None)
def edit_page_CONVENIENCE_METHOD(
    session: CurrentSession,
    user: UserToken,
    version_node_id: UUID = Path(...),
    payload: DerivedContentUpdate = Body(...),
) -> Response:
    # Fetch the derived content and ensure it belongs to the user's organization
    query = (
        select(DocumentSource)
        .join(DocumentSource.source_version_node)
        .join(VersionNode.version)
        .join(Version.primary_asset)
        .options(
            selectinload(DocumentSource.source_version_node).selectinload(
                VersionNode.version
            ),
        )
        .where(PrimaryAsset.organization_id == user.organization_id)
        .where(DocumentSource.page_version_node_id == version_node_id)
    )
    doc_sources = session.exec(query).all()
    for doc_source in doc_sources:
        enforce_asset_action(
            db=session,
            user=user,
            asset_id=doc_source.source_version_node.version.primary_asset_id,
            action_key="asset.use_as_source",
        )

    version_node = session.exec(
        select(VersionNode)
        .where(VersionNode.id == version_node_id)
        .options(
            selectinload(VersionNode.version).selectinload(Version.primary_asset),
            selectinload(VersionNode.node).selectinload(Node.contents),
        )
    ).one_or_none()

    if not version_node:
        raise HTTPException(status_code=404, detail="Version node not found")

    derived_content = version_node.node.contents[0]

    if payload.content is not None:
        derived_content.content = payload.content
    if payload.content_name is not None:
        derived_content.content_name = payload.content_name
        primary_asset = version_node.version.primary_asset

        if primary_asset:
            primary_asset.display_name = payload.content_name
            session.add(primary_asset)

    session.add(derived_content)
    session.commit()
    session.refresh(derived_content)

    return Response(status_code=202)


@router.post("/new_page", response_model=NewPageResponse)
def new_page(session: CurrentSession, user: UserToken) -> NewPageResponse:
    enforce_org_membership(session, user)

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
        vcs_auto_update_policy=None,
    )
    session.add(new_primary_asset)

    creator = session.exec(
        select(UserCache).where(UserCache.id == user.user_id)
    ).one_or_none()
    if creator is None:
        creator = UserCache(id=user.user_id, full_name=user.full_name, email=user.email)
        session.add(creator)
    session.flush()

    new_version = Version(
        primary_asset_id=new_primary_asset.id,
        vcs_hash=None,
        status=VersionStatus.GENERATION_COMPLETE,
        vcs_metadata=None,
    )
    session.add(new_version)

    new_version_creator = VersionCreator(version_id=new_version.id, user_id=creator.id)
    session.add(new_version_creator)

    new_node = Node(
        kind=NodeKind.OTHER,
        primary_asset_id=new_primary_asset.id,
        version_id=new_version.id,
        relative_path="NODE",
        source_hash=None,
    )
    session.add(new_node)
    session.flush()

    new_version_node = VersionNode(
        version_id=new_version.id,
        node_id=new_node.id,
        relative_path="NODE",
    )
    session.add(new_version_node)

    new_derived_content = DerivedContent(
        content_kind="application_note",
        node_id=new_node.id,
        relative_path="NODE",
        content="",
        content_name=new_display_name,
        misc_metadata={},
    )
    session.add(new_derived_content)

    session.commit()
    session.refresh(new_derived_content)

    return NewPageResponse(
        version_node_id=new_version_node.id,
        display_name=new_display_name,
    )
