from database.db import engine
from database.models import PrimaryAsset, PrimaryAssetRoleGrant
from database.models_enums import PrimaryAssetKind, PrimaryAssetRole, PrincipalKind
from sqlmodel import Session, select


def create_acl_for_existing_assets() -> None:
    with Session(engine) as session:
        existing_primary_assets = session.exec(
            select(PrimaryAsset).where(
                PrimaryAsset.kind.in_(
                    [PrimaryAssetKind.CODEBASE, PrimaryAssetKind.FILE]
                )
            )
        ).all()

        for asset in existing_primary_assets:
            # If ANY grants, just skip it, but if none, create a viewer grant for the org level
            existing_grants = session.exec(
                select(PrimaryAssetRoleGrant).where(
                    PrimaryAssetRoleGrant.primary_asset_id == asset.id
                )
                # .where(
                #     PrimaryAssetRoleGrant.principal_kind == PrincipalKind.org
                # )
                # .where(
                #     PrimaryAssetRoleGrant.role == PrimaryAssetRole.viewer
                # )
            ).all()

            if existing_grants:
                print(
                    f"PrimaryAsset {asset.id} already has {len(existing_grants)} grants, skipping..."
                )
                continue

            new_grant = PrimaryAssetRoleGrant(
                primary_asset_id=asset.id,
                organization_id=asset.organization_id,
                principal_kind=PrincipalKind.org,
                role=PrimaryAssetRole.asset_viewer,
            )
            session.add(new_grant)
            session.commit()


if __name__ == "__main__":
    create_acl_for_existing_assets()
