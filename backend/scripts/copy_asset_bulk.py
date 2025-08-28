"""
Copy CODEBASE primary assets and all their related data to a different database instance.
Uses bulk operations for much better performance.

Usage:
    export SOURCE_DATABASE_URL="postgresql://..."
    export DESTINATION_DATABASE_URL="postgresql://..."

    python copy_asset_bulk.py \
        --asset-ids "uuid1" "uuid2" "uuid3" \
        --destination-org-id "org-id" \
        [--skip-embeddings] \
        [--dry-run]
"""

import argparse
import os
import sys
from uuid import UUID

from database.models_v2 import InspectorRun
from sqlmodel import Session, create_engine, select

from driver_db.database.models_v1 import ChunkAndEmbedding, DerivedContent
from driver_db.database.models_v2 import (
    Node,
    NodeKind,
    PrimaryAsset,
    PrimaryAssetKind,
    Version,
)


class BulkAssetCopier:
    def __init__(self, source_engine, dest_engine, dry_run=False):
        self.source_engine = source_engine
        self.dest_engine = dest_engine
        self.dry_run = dry_run

    def copy_assets(
        self,
        asset_ids: list[UUID],
        destination_org_id: str,
        skip_embeddings: bool = False,
    ) -> bool:
        with Session(self.source_engine) as source_session:
            # 1. Fetch all primary assets
            assets = source_session.exec(
                select(PrimaryAsset).where(
                    PrimaryAsset.id.in_(asset_ids),
                    PrimaryAsset.kind == PrimaryAssetKind.CODEBASE,
                )
            ).all()

            if not assets:
                print("No valid CODEBASE assets found")
                return False

            valid_asset_ids = [a.id for a in assets]
            print(f"Found {len(assets)} valid CODEBASE assets")

            # 2. Fetch all related data in bulk
            print("Fetching all related data...")

            # Versions
            versions = source_session.exec(
                select(Version).where(Version.primary_asset_id.in_(valid_asset_ids))
            ).all()
            version_ids = [v.id for v in versions]

            # Nodes
            nodes = source_session.exec(
                select(Node).where(
                    Node.version_id.in_(version_ids),
                    Node.kind.in_(
                        [NodeKind.CODEBASE_FILE, NodeKind.CODEBASE_DIRECTORY]
                    ),
                )
            ).all()
            node_ids = [n.id for n in nodes]

            # Derived contents
            contents = source_session.exec(
                select(DerivedContent).where(DerivedContent.node_id.in_(node_ids))
            ).all()
            content_ids = [c.id for c in contents]

            # Chunks and embeddings
            chunks = []
            if not skip_embeddings and content_ids:
                chunks = source_session.exec(
                    select(ChunkAndEmbedding).where(
                        ChunkAndEmbedding.content_id.in_(content_ids)
                    )
                ).all()

            # Inspector runs
            runs = source_session.exec(
                select(InspectorRun).where(InspectorRun.version_id.in_(version_ids))
            ).all()

        # Print what we found
        print("\nData to copy:")
        print(f"  Assets: {len(assets)}")
        print(f"  Versions: {len(versions)}")
        print(f"  Nodes: {len(nodes)}")
        print(f"  Derived Contents: {len(contents)}")
        print(f"  Chunks/Embeddings: {len(chunks)}")
        print(f"  Inspector Runs: {len(runs)}")

        if self.dry_run:
            print("\nDRY RUN - not copying data")
            return True

        # 3. Bulk insert all data
        with Session(self.dest_engine) as dest_session:
            try:
                print("\nCopying data...")

                # Assets (with updated org_id)
                asset_mappings = [
                    {
                        "id": a.id,
                        "display_name": a.display_name,
                        "repository_id": a.repository_id,
                        "organization_id": destination_org_id,  # Updated
                        "kind": a.kind,
                        "installation_id": None,  # Clear git installation
                        "codebase_settings_auto_commit_docs": a.codebase_settings_auto_commit_docs,
                        "created_at": a.created_at,
                        "updated_at": a.updated_at,
                        "related_content_last_updated": a.related_content_last_updated,
                    }
                    for a in assets
                ]
                dest_session.bulk_insert_mappings(PrimaryAsset, asset_mappings)
                print(f"  Copied {len(assets)} assets")

                # Versions - first insert without previous_version_id to avoid fk issues
                version_mappings = [
                    {
                        "id": v.id,
                        "primary_asset_id": v.primary_asset_id,
                        "vcs_hash": v.vcs_hash,
                        "status": v.status,
                        "previous_version_id": None,  # Set to None initially
                        "created_at": v.created_at,
                        "updated_at": v.updated_at,
                        "vcs_metadata": v.vcs_metadata,
                    }
                    for v in versions
                ]
                if version_mappings:
                    dest_session.bulk_insert_mappings(Version, version_mappings)
                    print(f"  Copied {len(versions)} versions")

                    # Now update previous_version_id references
                    versions_with_prev = [
                        v for v in versions if v.previous_version_id is not None
                    ]
                    if versions_with_prev:
                        dest_session.flush()  # Make sure versions are inserted
                        from sqlalchemy import text

                        for v in versions_with_prev:
                            dest_session.execute(
                                text(
                                    "UPDATE v2_version SET previous_version_id = :prev_id WHERE id = :id"
                                ),
                                {
                                    "prev_id": str(v.previous_version_id),
                                    "id": str(v.id),
                                },
                            )
                        print(f"  Updated {len(versions_with_prev)} version references")

                # Nodes
                node_mappings = [
                    {
                        "id": n.id,
                        "version_id": n.version_id,
                        "relative_path": n.relative_path,
                        "kind": n.kind,
                        # 'depth': n.depth,
                        # 'total_files': n.total_files,
                        "misc_metadata": n.misc_metadata,
                        "created_at": n.created_at,
                        "updated_at": n.updated_at,
                    }
                    for n in nodes
                ]
                if node_mappings:
                    dest_session.bulk_insert_mappings(Node, node_mappings)
                    print(f"  Copied {len(nodes)} nodes")

                # Derived contents
                content_mappings = [
                    {
                        "id": c.id,
                        "node_id": c.node_id,
                        "content_kind": c.content_kind,
                        "relative_path": c.relative_path,
                        "content": c.content,
                        "content_name": c.content_name,
                        "misc_metadata": c.misc_metadata,
                        "order": c.order,
                        "created_at": c.created_at,
                        "updated_at": c.updated_at,
                    }
                    for c in contents
                ]
                if content_mappings:
                    dest_session.bulk_insert_mappings(DerivedContent, content_mappings)
                    print(f"  Copied {len(contents)} derived contents")

                # Chunks and embeddings (in batches if large)
                if chunks:
                    BATCH_SIZE = 1000
                    for i in range(0, len(chunks), BATCH_SIZE):
                        batch = chunks[i : i + BATCH_SIZE]
                        chunk_mappings = [
                            {
                                "id": ch.id,
                                "content_id": ch.content_id,
                                "chunk_number": ch.chunk_number,
                                "text": ch.text,
                                "text_embedding_3_small": ch.text_embedding_3_small,
                                "created_at": ch.created_at,
                                "updated_at": ch.updated_at,
                            }
                            for ch in batch
                        ]
                        dest_session.bulk_insert_mappings(
                            ChunkAndEmbedding, chunk_mappings
                        )
                        if i > 0:
                            print(
                                f"    Batch {i//BATCH_SIZE + 1}/{(len(chunks) + BATCH_SIZE - 1)//BATCH_SIZE}"
                            )
                    print(f"  Copied {len(chunks)} chunks/embeddings")

                # Inspector runs
                run_mappings = [
                    {
                        "id": r.id,
                        "version_id": r.version_id,
                        "call_id": r.call_id,
                        "created_at": r.created_at,
                        "updated_at": r.updated_at,
                    }
                    for r in runs
                ]
                if run_mappings:
                    dest_session.bulk_insert_mappings(InspectorRun, run_mappings)
                    print(f"  Copied {len(runs)} inspector runs")

                dest_session.commit()
                print("\nSuccess!")
                return True

            except Exception as e:
                print(f"\nERROR: {e!s}")
                dest_session.rollback()
                raise


def main():
    parser = argparse.ArgumentParser(
        description="Copy CODEBASE primary assets to another database"
    )
    parser.add_argument(
        "--asset-ids",
        nargs="+",
        required=True,
        help="One or more UUIDs of CODEBASE assets to copy",
    )
    parser.add_argument(
        "--destination-org-id", required=True, help="Destination organization ID"
    )
    parser.add_argument(
        "--skip-embeddings", action="store_true", help="Skip copying embeddings"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Perform a dry run without committing"
    )

    args = parser.parse_args()

    source_db = os.environ.get("SOURCE_DATABASE_URL")
    dest_db = os.environ.get("DESTINATION_DATABASE_URL")

    if not source_db:
        print("ERROR: SOURCE_DATABASE_URL environment variable is required")
        return 1

    if not dest_db:
        print("ERROR: DESTINATION_DATABASE_URL environment variable is required")
        return 1

    asset_ids = []
    for asset_id_str in args.asset_ids:
        try:
            asset_ids.append(UUID(asset_id_str))
        except ValueError:
            print(f"ERROR: Invalid UUID format: {asset_id_str}")
            return 1

    source_engine = create_engine(source_db)
    dest_engine = create_engine(dest_db)

    copier = BulkAssetCopier(source_engine, dest_engine, dry_run=args.dry_run)

    success = copier.copy_assets(
        asset_ids=asset_ids,
        destination_org_id=args.destination_org_id,
        skip_embeddings=args.skip_embeddings,
    )

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
