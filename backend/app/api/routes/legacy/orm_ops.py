from database.models_v1 import (
    DerivedContent,
)
from database.models_v2 import Node, PrimaryAsset, Version
from sqlmodel import Session, select


# TODO: do away with this?
def check_access(
    session: Session,
    organization_id: str,
    derived_content_id: str | None = None,
    node_id: str | None = None,
    version_id: str | None = None,
    primary_asset_id: str | None = None,
) -> bool:
    # TODO: undo this check
    access_checks = []

    if derived_content_id:
        derived_content = session.exec(
            select(DerivedContent)
            .join(Node, DerivedContent.node_id == Node.id)
            .join(Version, Node.version_id == Version.id)
            .join(PrimaryAsset, Version.primary_asset_id == PrimaryAsset.id)
            .where(DerivedContent.id == derived_content_id)
            .where(PrimaryAsset.organization_id == organization_id)
        ).first()
        access_checks.append(
            derived_content
            and derived_content.primary_asset.organization_id == organization_id
        )

    if node_id:
        node = session.exec(select(Node).where(Node.id == node_id)).first()
        access_checks.append(
            node and node.version.primary_asset.organization_id == organization_id
        )

    if version_id:
        version = session.exec(select(Version).where(Version.id == version_id)).first()
        access_checks.append(
            version and version.primary_asset.organization_id == organization_id
        )

    if primary_asset_id:
        primary_asset = session.exec(
            select(PrimaryAsset).where(PrimaryAsset.id == primary_asset_id)
        ).first()
        access_checks.append(
            primary_asset and primary_asset.organization_id == organization_id
        )

    return all(access_checks)
