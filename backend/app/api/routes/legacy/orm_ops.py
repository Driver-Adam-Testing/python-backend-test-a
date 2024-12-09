from database.models_v1 import (
    Codebase,
    DerivedContent,
    Workspace,
)
from database.models_v2 import NodeRow, PrimaryAssetRow, VersionRow
from sqlmodel import Session, delete, select


def get_workspace_related_entities(session: Session, org_id: str) -> list[Workspace]:
    statement = (
        select(Workspace)
        .join(Codebase, Workspace.id == Codebase.workspace_id)  # type: ignore
        .where(Workspace.organization_id == org_id)
    )
    result = session.exec(statement).all()
    return result  # type: ignore


# TODO remove me
def get_source_content_by_id(session: Session, id: str) -> DerivedContent | None:
    statement = select(DerivedContent).where(DerivedContent.id == id)
    result = session.exec(statement)
    return result.first()


def get_derived_content_by_id(session: Session, id: str) -> DerivedContent | None:
    statement = select(DerivedContent).where(DerivedContent.id == id)
    result = session.exec(statement)
    return result.first()


def delete_codebase_by_id(session: Session, codebase_id: str) -> bool:
    # TODO cascade delete from codebase to content
    with session.begin():
        # Delete all associated SourceContent
        session.exec(
            delete(DerivedContent).where(DerivedContent.codebase_id == codebase_id)  # type: ignore
        )
        # Finally, delete the codebase itself
        count = session.exec(delete(Codebase).where(Codebase.id == codebase_id))  # type: ignore
        return count > 0


def get_codebase_by_id(session: Session, codebase_id: str) -> Codebase | None:
    statement = select(Codebase).where(Codebase.id == codebase_id)
    result = session.exec(statement)
    return result.first()


def check_access(
    session: Session,
    organization_id: str,
    codebase_id: str | None = None,
    derived_content_id: str | None = None,
    node_id: str | None = None,
    version_id: str | None = None,
    primary_asset_id: str | None = None,
) -> bool:
    # TODO: undo this check
    access_checks = []

    if codebase_id:
        primary_asset = session.exec(
            select(PrimaryAssetRow).where(PrimaryAssetRow.id == codebase_id)
        ).first()
        access_checks.append(
            primary_asset and primary_asset.organization_id == organization_id
        )

    if derived_content_id:
        derived_content = session.exec(
            select(DerivedContent)
            .join(NodeRow, DerivedContent.node_id == NodeRow.id)
            .join(VersionRow, NodeRow.version_id == VersionRow.id)
            .join(PrimaryAssetRow, VersionRow.primary_asset_id == PrimaryAssetRow.id)
            .where(DerivedContent.id == derived_content_id)
            .where(PrimaryAssetRow.organization_id == organization_id)
        ).first()
        access_checks.append(
            derived_content
            and derived_content.primary_asset.organization_id == organization_id
        )

    if node_id:
        node = session.exec(select(NodeRow).where(NodeRow.id == node_id)).first()
        access_checks.append(
            node and node.version.primary_asset.organization_id == organization_id
        )

    if version_id:
        version = session.exec(
            select(VersionRow).where(VersionRow.id == version_id)
        ).first()
        access_checks.append(
            version and version.primary_asset.organization_id == organization_id
        )

    if primary_asset_id:
        primary_asset = session.exec(
            select(PrimaryAssetRow).where(PrimaryAssetRow.id == primary_asset_id)
        ).first()
        access_checks.append(
            primary_asset and primary_asset.organization_id == organization_id
        )

    return all(access_checks)
