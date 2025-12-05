import logging

from database.db import engine
from database.models import Organization, PrimaryAsset, PrimaryAssetRoleGrant
from database.models_enums import PrimaryAssetKind, PrimaryAssetRole, PrincipalKind
from sqlmodel import Session, select

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def create_acl_for_existing_assets() -> None:
    logger.info("Starting ACL creation for existing assets...")
    with Session(engine) as session:
        existing_primary_assets = session.exec(
            select(PrimaryAsset)
            .join(Organization, PrimaryAsset.organization_id == Organization.id)
            .where(
                PrimaryAsset.kind.in_(
                    [PrimaryAssetKind.CODEBASE, PrimaryAssetKind.FILE]
                )
            )
        ).all()

        logger.info(
            f"Found {len(existing_primary_assets)} primary assets with valid organizations."
        )

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
                logger.info(
                    f"PrimaryAsset {asset.id} already has {len(existing_grants)} grants, skipping..."
                )
                continue

            logger.info(f"Creating default grant for PrimaryAsset {asset.id}...")
            new_grant = PrimaryAssetRoleGrant(
                primary_asset_id=asset.id,
                organization_id=asset.organization_id,
                principal_kind=PrincipalKind.org,
                role=PrimaryAssetRole.asset_member,
            )
            session.add(new_grant)
            session.commit()

    logger.info("Finished ACL creation for existing assets.")


if __name__ == "__main__":
    create_acl_for_existing_assets()
