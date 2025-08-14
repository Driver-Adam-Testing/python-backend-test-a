import time

import modal
from database.db import get_session
from database.models_v2 import PrimaryAsset, Version
from sqlalchemy.orm import selectinload
from sqlmodel import select


def run_all_version_cleanup():
    with get_session() as session:
        # Get the most recent version for each primary asset
        most_recent_versions = session.exec(
            select(Version)
            .join(PrimaryAsset)
            .where(PrimaryAsset.kind == "CODEBASE")
            .options(selectinload(Version.primary_asset))
        ).all()

        # Group versions by primary asset and get the most recent one for each
        most_recent_versions_dict = {}
        for version in most_recent_versions:
            if (
                version.primary_asset_id not in most_recent_versions_dict
                or version.created_at
                > most_recent_versions_dict[version.primary_asset_id].created_at
            ):
                most_recent_versions_dict[version.primary_asset_id] = version

        most_recent_versions = list(most_recent_versions_dict.values())
        print(
            f"DEBUG: Most recent versions: {[v.primary_asset.display_name for v in most_recent_versions]}"
        )
        # Filter to get the most recent version for each primary asset

        # Get the cleanup_old_versions function as a modal function lookup
        cleanup_old_versions = modal.Function.lookup(
            app_name="inspector-v2", name="cleanup_old_versions"
        )

        # Run cleanup_old_versions for each most recent version
        for version in most_recent_versions:
            print(f"DEBUG: Version id: {version.id}")
            print(f"DEBUG: Version created at: {version.created_at}")
            print(f"DEBUG: Version primary name: {version.primary_asset.display_name}")
            print(f"DEBUG: Version primary id: {version.primary_asset.id}")
            print(f"DEBUG: Version primary kind: {version.primary_asset.kind}")

            time.sleep(1)
            if version:
                try:
                    cleanup_old_versions.remote(version.id)
                except Exception as e:
                    print(f"Error while cleaning up version {version.id}: {e}")


if __name__ == "__main__":
    run_all_version_cleanup()
