import asyncio
import hashlib
import logging
import os
import tempfile
import zipfile
from pathlib import Path
from typing import Any
from uuid import UUID

import boto3
import modal
from sqlmodel import Session, select

# Configuration flag: Set to True to use S3 content, False to use DerivedContent long description
USE_S3 = True

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Modal app setup
app = modal.App("version-node-migration")

# Modal image with dependencies
migration_image = (
    modal.Image.debian_slim(python_version="3.12")
    .add_local_dir(local_path="../driver_db", remote_path="/driver_db", copy=True)
    .pip_install(
        [
            "boto3",
            "sqlmodel",
            "/driver_db",
        ]
    )
    .add_local_python_source(
        "database",
        copy=True,
        ignore=lambda p: False,  # recent modal version only copy .py by default, but we have text files, for example, that we want
    )
)


def setup_s3_client() -> boto3.client:
    """Initialize and return S3 client."""
    return boto3.client(
        "s3",
        aws_access_key_id=os.getenv("S3ADMIN_AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("S3ADMIN_AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_REGION"),
        endpoint_url=os.getenv("AWS_S3_ENDPOINT_URL")
        if os.getenv("AWS_S3_ENDPOINT_URL")
        else None,
    )


def hash_organization_id(organization_id: str) -> str:
    """Hash organization ID to get S3 bucket name."""
    return hashlib.sha256(organization_id.encode()).hexdigest()[:63]


def fetch_s3_content(
    s3_client: boto3.client,
    organization_id: str,
    primary_asset_id: UUID,
    version_id: UUID,
    relative_path: str,
) -> str | None:
    """Fetch file content from S3."""
    bucket = hash_organization_id(organization_id)
    key = f"{primary_asset_id}/{version_id}/{relative_path.lstrip('/')}"

    try:
        obj = s3_client.get_object(Bucket=bucket, Key=key)
        file_content = obj["Body"].read()
        return file_content.decode("utf-8", errors="replace")
    except s3_client.exceptions.NoSuchKey:
        logger.warning(f"S3 content not found: {bucket}/{key}")
        return None
    except Exception as e:
        logger.error(f"Error fetching S3 content for {key}: {e}")
        return None


def fetch_long_description(session: Session, node_id: UUID) -> str | None:
    """Fetch long description content from DerivedContent for a node."""
    from database.models import DerivedContent
    from database.models_enums import ContentKind

    derived_content = session.exec(
        select(DerivedContent)
        .where(DerivedContent.node_id == node_id)
        .where(DerivedContent.content_kind == ContentKind.LONG_DESCRIPTION)
        .limit(1)
    ).first()

    if derived_content and derived_content.content:
        return derived_content.content

    logger.warning(f"No long description found for node {node_id}")
    return None


def hash_file_content(content: str) -> str:
    """Hash source file content using SHA256."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def hash_directory_node(children_hashes: list[str]) -> str:
    """
    Hash directory node based on children content hashes.
    This enables proper content-based deduplication.
    """
    # Sort children hashes for consistent hashing
    sorted_hashes = sorted(children_hashes)

    # Hash based on children content hashes only
    hash_input = "|".join(sorted_hashes)
    return hashlib.sha256(hash_input.encode("utf-8")).hexdigest()


def update_document_sources(
    session: Session, old_node_id: UUID, new_version_node_id: UUID
) -> None:
    """
    Update DocumentSource records to point to new VersionNode.

    When migrating a node, any DocumentSource records that reference the old node
    should be updated to point to the newly created VersionNode.
    """
    from database.models import DocumentSource

    # Update source_version_node_id for DocumentSources that reference this node as source
    source_docs = session.exec(
        select(DocumentSource).where(DocumentSource.source_node_id == old_node_id)
    ).all()

    for doc_source in source_docs:
        doc_source.source_version_node_id = new_version_node_id
        logger.info(
            f"Updated DocumentSource {doc_source.id} source_version_node_id -> {new_version_node_id}"
        )

    # Update page_version_node_id for DocumentSources that reference this node as page
    page_docs = session.exec(
        select(DocumentSource).where(DocumentSource.page_node_id == old_node_id)
    ).all()

    for doc_source in page_docs:
        doc_source.page_version_node_id = new_version_node_id
        logger.info(
            f"Updated DocumentSource {doc_source.id} page_version_node_id -> {new_version_node_id}"
        )


def update_autodoc_status_history(
    session: Session, old_node_id: UUID, new_version_node_id: UUID
) -> None:
    """
    Update AutoDocStatusHistory records to point to new VersionNode during deduplication.

    When migrating a node, any AutoDocStatusHistory records that reference the old node
    should be updated to point to the newly created VersionNode.
    """
    from database.models import AutoDocStatusHistory

    autodoc_records = session.exec(
        select(AutoDocStatusHistory).where(
            AutoDocStatusHistory.page_node_id == old_node_id
        )
    ).all()

    logger.info(f"Found {len(autodoc_records)} AutoDocStatusHistory records to update")

    for record in autodoc_records:
        record.source_version_node_id = new_version_node_id
        logger.info(
            f"Updated AutoDocStatusHistory {record.id} source_version_node_id -> {new_version_node_id}"
        )


def get_directory_children_hashes(
    session: Session, version_id: UUID, relative_path: str
) -> list[str]:
    """Get list of content hashes for direct children of a directory node."""
    from database.models import Node, VersionNode

    # Add trailing slash to directory path if not present
    dir_path = relative_path if relative_path.endswith("/") else f"{relative_path}/"

    # Find all nodes that are direct children (one level deeper)
    target_depth = dir_path.count("/") - 1  # depth starts from 0

    # Join VersionNode with Node to get content hashes
    children_hashes = session.exec(
        select(Node.source_hash)
        .join(VersionNode, VersionNode.node_id == Node.id)
        .where(VersionNode.version_id == version_id)
        .where(VersionNode.relative_path.startswith(dir_path))
        .where(VersionNode.depth == target_depth + 1)
    ).all()
    print(f"found {len(children_hashes)} children for directory {relative_path}")

    return list(children_hashes)


def find_node_by_hash(
    session: Session, primary_asset_id: UUID, source_hash: str
) -> Any | None:
    """Find existing Node with matching hash for the same PrimaryAsset."""
    from database.models import Node

    return session.exec(
        select(Node)
        .where(Node.primary_asset_id == primary_asset_id)
        .where(Node.source_hash == source_hash)
        .limit(1)
    ).first()


def migrate_file_node(
    session: Session,
    s3_client: str | None,
    version: Any,
    node: Any,
) -> None:
    """Migrate a single file node with deduplication."""
    from database.models import DerivedContent, Node, VersionNode

    print(f"Migrating file node: {node.relative_path} (version: {version.id})")

    # Fetch content based on USE_S3 flag
    if USE_S3:
        if s3_client is None:
            logger.error("S3 client is None but USE_S3 is True")
            return
        content = fetch_s3_content(
            s3_client,
            version.primary_asset.organization_id,
            version.primary_asset_id,
            version.id,
            node.relative_path,
        )
        if content is None:
            logger.warning(f"Skipping node {node.id} - no S3 content found")
            return
    else:
        content = fetch_long_description(session, node.id)
        if content is None:
            logger.warning(f"Skipping node {node.id} - no long description found")
            return

    # Hash the content
    source_hash = hash_file_content(content)

    # Check for existing node with same hash
    existing_node = find_node_by_hash(session, version.primary_asset_id, source_hash)

    if existing_node:
        print(
            f"Found existing node with hash {source_hash}, reusing node {existing_node.id}"
        )
        # Create VersionNode link to existing node
        version_node = VersionNode(
            version_id=version.id,
            relative_path=node.relative_path,
            node_id=existing_node.id,
            misc_metadata=node.misc_metadata,
        )
        session.add(version_node)
        session.flush()  # Get the new version_node ID

        # Update DocumentSource records to point to new VersionNode
        update_document_sources(session, node.id, version_node.id)

        # Delete old node (cascade deletes DerivedContent)
        session.delete(node)
        session.commit()
    else:
        print(f"Creating new node with hash {source_hash}")
        # Create new Node with hash
        new_node = Node(
            source_hash=source_hash,
            kind=node.kind,
            primary_asset_id=version.primary_asset_id,
            version_id=version.id,
            relative_path=node.relative_path,
            misc_metadata=node.misc_metadata,
        )
        session.add(new_node)
        session.flush()  # Get the new node ID

        # Move DerivedContent to new node
        derived_contents = session.exec(
            select(DerivedContent).where(DerivedContent.node_id == node.id)
        ).all()

        for dc in derived_contents:
            dc.node_id = new_node.id

        # Create VersionNode link
        version_node = VersionNode(
            version_id=version.id,
            relative_path=node.relative_path,
            node_id=new_node.id,
            misc_metadata=node.misc_metadata,
        )
        session.add(version_node)
        session.flush()  # Get the new version_node ID

        # Update DocumentSource records to point to new VersionNode
        update_document_sources(session, node.id, version_node.id)

        # Delete old node (DerivedContent already moved, so no cascade delete)
        session.delete(node)
        session.commit()


def migrate_directory_node(
    session: Session,
    version: Any,
    node: Any,
) -> None:
    """Migrate a single directory node with content-based hashing."""
    from database.models import DerivedContent, Node, VersionNode

    print(f"Migrating directory node: {node.relative_path} (version: {version.id})")

    # Get children content hashes for hashing
    children_hashes = get_directory_children_hashes(
        session, version.id, node.relative_path
    )

    # Hash directory based on children content hashes
    source_hash = hash_directory_node(children_hashes)

    # Check for existing node with same hash
    existing_node = find_node_by_hash(session, version.primary_asset_id, source_hash)

    if existing_node:
        print(
            f"Found existing directory node with hash {source_hash}, reusing node {existing_node.id}"
        )
        # Create VersionNode link to existing node
        version_node = VersionNode(
            version_id=version.id,
            relative_path=node.relative_path,
            node_id=existing_node.id,
            misc_metadata=node.misc_metadata,
        )
        session.add(version_node)
        session.flush()  # Get the new version_node ID

        # Update DocumentSource records to point to new VersionNode
        update_document_sources(session, node.id, version_node.id)

        # Update AutoDocStatusHistory records to point to new VersionNode
        update_autodoc_status_history(session, node.id, version_node.id)

        # Delete old node (cascade deletes DerivedContent)
        session.delete(node)
        session.commit()
    else:
        print(f"Creating new directory node with hash {source_hash}")
        # Create new Node with hash
        new_node = Node(
            source_hash=source_hash,
            kind=node.kind,
            primary_asset_id=version.primary_asset_id,
            version_id=version.id,
            relative_path=node.relative_path,
            misc_metadata=node.misc_metadata,
        )
        session.add(new_node)
        session.flush()  # Get the new node ID

        # Move DerivedContent to new node
        derived_contents = session.exec(
            select(DerivedContent).where(DerivedContent.node_id == node.id)
        ).all()

        for dc in derived_contents:
            dc.node_id = new_node.id

        # Create VersionNode link
        version_node = VersionNode(
            version_id=version.id,
            relative_path=node.relative_path,
            node_id=new_node.id,
            misc_metadata=node.misc_metadata,
        )
        session.add(version_node)
        session.flush()  # Get the new version_node ID

        # Update DocumentSource records to point to new VersionNode
        update_document_sources(session, node.id, version_node.id)

        # Update AutoDocStatusHistory records to point to new VersionNode
        update_autodoc_status_history(session, node.id, version_node.id)

        # Delete old node (DerivedContent already moved, so no cascade delete)
        session.delete(node)
        session.commit()


def migrate_other_node(
    session: Session,
    version: Any,
    node: Any,
) -> None:
    """
    Migrate nodes of other kinds by reusing existing node.

    Since we're not doing content-based hashing for these nodes,
    we simply create a VersionNode link to the existing node.
    """
    from database.models import VersionNode

    print(f"Migrating other node: {node.relative_path} (version: {version.id})")

    # Create VersionNode link to existing node (no need to create new Node)
    version_node = VersionNode(
        version_id=version.id,
        relative_path=node.relative_path,
        node_id=node.id,
        misc_metadata=node.misc_metadata,
    )
    # Update Node with primary_asset_id
    node.primary_asset_id = version.primary_asset_id
    session.add(node)
    session.add(version_node)
    session.flush()  # Get the new version_node ID

    # Update DocumentSource records to point to new VersionNode
    update_document_sources(session, node.id, version_node.id)

    # Update AutoDocStatusHistory records to point to new VersionNode
    update_autodoc_status_history(session, node.id, version_node.id)

    session.commit()


def download_and_extract_zip(
    s3_client: boto3.client,
    organization_id: str,
    primary_asset_id: UUID,
    version_id: UUID,
    temp_dir: str,
) -> Path:
    """Download and extract the source zip file for a connected version."""
    bucket = hash_organization_id(organization_id)
    key = f"{primary_asset_id}/{version_id}/{version_id}_source.zip"

    zip_path = Path(temp_dir) / f"{version_id}_source.zip"

    try:
        logger.info(f"Downloading zip from s3://{bucket}/{key}")
        s3_client.download_file(bucket, key, str(zip_path))

        extract_dir = Path(temp_dir) / "extracted"
        extract_dir.mkdir(exist_ok=True)

        logger.info(f"Extracting zip to {extract_dir}")
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(extract_dir)

        return extract_dir
    except s3_client.exceptions.NoSuchKey:
        logger.error(f"Zip file not found: {bucket}/{key}")
        raise
    except Exception as e:
        logger.error(f"Error downloading/extracting zip for {key}: {e}")
        raise


def migrate_connected_file_node(
    session: Session,
    version: Any,
    node: Any,
    extracted_dir: Path,
) -> None:
    """Migrate a file node from extracted zip with deduplication."""
    from database.models import DerivedContent, Node, VersionNode

    print(
        f"Migrating connected file node: {node.relative_path} (version: {version.id})"
    )

    # Read content from extracted directory
    file_path = extracted_dir / node.relative_path.lstrip("/")

    if not file_path.exists():
        logger.warning(
            f"File not found in extracted zip: {file_path}, skipping node {node.id}"
        )
        return

    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return

    # Hash the content
    source_hash = hash_file_content(content)

    # Check for existing node with same hash
    existing_node = find_node_by_hash(session, version.primary_asset_id, source_hash)

    if existing_node:
        print(
            f"Found existing node with hash {source_hash}, reusing node {existing_node.id}"
        )
        # Create VersionNode link to existing node
        version_node = VersionNode(
            version_id=version.id,
            relative_path=node.relative_path,
            node_id=existing_node.id,
            misc_metadata=node.misc_metadata,
        )
        session.add(version_node)
        session.flush()

        # Update DocumentSource records to point to new VersionNode
        update_document_sources(session, node.id, version_node.id)

        # Delete old node (cascade deletes DerivedContent)
        session.delete(node)
        session.commit()
    else:
        print(f"Creating new node with hash {source_hash}")
        # Create new Node with hash
        new_node = Node(
            source_hash=source_hash,
            kind=node.kind,
            primary_asset_id=version.primary_asset_id,
            version_id=version.id,
            relative_path=node.relative_path,
            misc_metadata=node.misc_metadata,
        )
        session.add(new_node)
        session.flush()

        # Move DerivedContent to new node
        derived_contents = session.exec(
            select(DerivedContent).where(DerivedContent.node_id == node.id)
        ).all()

        for dc in derived_contents:
            dc.node_id = new_node.id

        # Create VersionNode link
        version_node = VersionNode(
            version_id=version.id,
            relative_path=node.relative_path,
            node_id=new_node.id,
            misc_metadata=node.misc_metadata,
        )
        session.add(version_node)
        session.flush()

        # Update DocumentSource records to point to new VersionNode
        update_document_sources(session, node.id, version_node.id)

        # Delete old node (DerivedContent already moved, so no cascade delete)
        session.delete(node)
        session.commit()


def migrate_connected_version(session: Session, version: Any) -> None:
    """Migrate a connected version by downloading and extracting the zip file."""
    from database.models import Node
    from database.models_enums import NodeKind

    print(f"Migrating connected version {version.id}")

    s3_client = setup_s3_client()

    # Create temporary directory for zip extraction
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # Download and extract the zip file
            extracted_dir = download_and_extract_zip(
                s3_client,
                version.primary_asset.organization_id,
                version.primary_asset_id,
                version.id,
                temp_dir,
            )

            # Get all nodes for this version
            nodes = session.exec(
                select(Node)
                .where(Node.version_id == version.id)
                .order_by(Node.depth.desc())  # Process deepest nodes first
            ).all()

            print(f"Found {len(nodes)} nodes to migrate for connected version")

            for node in nodes:
                try:
                    if node.kind == NodeKind.CODEBASE_FILE:
                        migrate_connected_file_node(
                            session, version, node, extracted_dir
                        )
                    elif node.kind == NodeKind.CODEBASE_DIRECTORY:
                        migrate_directory_node(session, version, node)
                    else:
                        # NodeKind.OTHER
                        migrate_other_node(session, version, node)
                except Exception as e:
                    logger.error(f"Error migrating connected node {node.id}: {e}")
                    session.rollback()
                    # Continue with next node

        except Exception as e:
            logger.error(f"Error processing connected version {version.id}: {e}")
            session.rollback()
            raise


def migrate_version(
    session: Session,
    s3_client: str | None,
    version: Any,
) -> None:
    """Migrate all nodes for a specific version."""
    from database.models import Node, VersionNode
    from database.models_enums import NodeKind, VersionStatus

    print(
        f"Processing version {version.id} for primary asset {version.primary_asset_id}"
    )

    # Check for existing VersionNodes - if they exist, this has already been migrated
    existing_version_nodes = session.exec(
        select(VersionNode).where(VersionNode.version_id == version.id)
    ).all()

    if existing_version_nodes:
        print(f"Version {version.id} already migrated. Skipping.")
        return

    if version.status == VersionStatus.CONNECTED:
        migrate_connected_version(session, version)
        return

    # Get all nodes for this version
    nodes = session.exec(
        select(Node)
        .where(Node.version_id == version.id)
        .order_by(Node.depth.desc())  # Process deepest nodes first
    ).all()

    print(f"Found {len(nodes)} nodes to migrate")

    for node in nodes:
        try:
            if node.kind == NodeKind.CODEBASE_FILE:
                migrate_file_node(session, s3_client, version, node)
            elif node.kind == NodeKind.CODEBASE_DIRECTORY:
                migrate_directory_node(session, version, node)
            else:
                # NodeKind.OTHER
                migrate_other_node(session, version, node)
        except Exception as e:
            logger.error(f"Error migrating node {node.id}: {e}")
            session.rollback()
            # Continue with next node


def cleanup_old_connected_versions(session: Session, primary_asset_id: UUID) -> int:
    """
    Delete all CONNECTED versions except the latest one for a primary asset.
    Returns the number of versions deleted.
    """
    from database.models import Version
    from database.models_enums import VersionStatus

    # Get all CONNECTED versions ordered by updated_at descending
    connected_versions = session.exec(
        select(Version)
        .where(Version.primary_asset_id == primary_asset_id)
        .where(Version.status == VersionStatus.CONNECTED)
        .order_by(Version.updated_at.desc())
    ).all()

    if len(connected_versions) <= 1:
        # Nothing to clean up
        return 0

    # Keep the first (latest), delete the rest
    versions_to_delete = connected_versions[1:]
    deleted_count = 0

    for version in versions_to_delete:
        logger.info(
            f"Deleting old CONNECTED version {version.id} (updated_at: {version.updated_at})"
        )
        session.delete(version)
        deleted_count += 1

    session.commit()
    return deleted_count


@app.function(
    image=migration_image,
    secrets=[
        modal.Secret.from_name("db"),
        modal.Secret.from_name("aws-inspector-s3"),
    ],
)
def migrate_primary_asset(primary_asset_id: UUID) -> dict[str, Any]:
    """
    Process all versions for a single primary asset.
    Returns summary statistics and any errors encountered.
    """
    from database.db import engine
    from database.models import PrimaryAsset, Version

    s3_client = setup_s3_client() if USE_S3 else None
    errors = []
    versions_processed = 0
    connected_versions_deleted = 0

    with Session(engine) as session:
        # Fetch the primary asset
        primary_asset = session.get(PrimaryAsset, primary_asset_id)
        if not primary_asset:
            error_msg = f"Primary asset {primary_asset_id} not found"
            logger.error(error_msg)
            return {
                "primary_asset_id": str(primary_asset_id),
                "success": False,
                "error": error_msg,
            }

        logger.info(
            f"Processing primary asset: {primary_asset.display_name} ({primary_asset.id}). Kind: {primary_asset.kind}"
        )

        # Clean up old CONNECTED versions
        try:
            connected_versions_deleted = cleanup_old_connected_versions(
                session, primary_asset_id
            )
            if connected_versions_deleted > 0:
                logger.info(
                    f"Deleted {connected_versions_deleted} old CONNECTED versions for {primary_asset.display_name}"
                )
        except Exception as e:
            error_msg = f"Error cleaning up CONNECTED versions: {e}"
            logger.error(error_msg)
            errors.append(error_msg)
            session.rollback()

        # Get all versions for this primary asset in reverse chronological order
        versions = session.exec(
            select(Version)
            .where(Version.primary_asset_id == primary_asset.id)
            .order_by(Version.updated_at.desc())
        ).all()

        logger.info(f"Found {len(versions)} versions for {primary_asset.display_name}")

        for version in versions:
            try:
                migrate_version(session, s3_client, version)
                versions_processed += 1
            except Exception as e:
                error_msg = f"Error migrating version {version.id}: {e}"
                logger.error(error_msg)
                errors.append(error_msg)
                session.rollback()
                # Continue with next version

    return {
        "primary_asset_id": str(primary_asset_id),
        "primary_asset_name": primary_asset.display_name,
        "success": True,
        "versions_processed": versions_processed,
        "connected_versions_deleted": connected_versions_deleted,
        "errors": errors,
    }


@app.function(
    image=migration_image,
    secrets=[
        modal.Secret.from_name("db"),
        modal.Secret.from_name("aws-inspector-s3"),
    ],
)
async def migrate_all_versions(max_concurrent: int = 5) -> None:
    """
    Main migration function - processes all primary assets in parallel with throttling.
    Uses semaphore to limit concurrent database connections.
    """
    from database.db import engine
    from database.models import PrimaryAsset

    logger.info("Starting VersionNode migration")
    logger.info(
        f"Using {'S3 content' if USE_S3 else 'DerivedContent long description'} for hashing"
    )
    logger.info(f"Max concurrent workers: {max_concurrent}")

    # Get all primary asset IDs
    with Session(engine) as session:
        primary_assets = session.exec(select(PrimaryAsset)).all()
        primary_asset_ids = [pa.id for pa in primary_assets]

    logger.info(f"Found {len(primary_asset_ids)} primary assets to process")

    # Semaphore to limit concurrent workers
    semaphore = asyncio.Semaphore(max_concurrent)

    async def throttled_migrate(pa_id: UUID) -> dict[str, Any]:
        async with semaphore:
            return await migrate_primary_asset.remote.aio(pa_id)

    # Execute with throttling
    results = await asyncio.gather(
        *[throttled_migrate(pa_id) for pa_id in primary_asset_ids],
        return_exceptions=True,
    )

    # Log summary
    successful = sum(1 for r in results if isinstance(r, dict) and r.get("success"))
    failed = len(results) - successful
    logger.info(f"Migration complete: {successful} successful, {failed} failed")

    # Log any errors
    for result in results:
        if isinstance(result, dict) and result.get("errors"):
            logger.warning(
                f"Primary asset {result['primary_asset_name']} had {len(result['errors'])} version errors"
            )
        elif isinstance(result, Exception):
            logger.error(f"Primary asset migration failed with exception: {result}")


@app.local_entrypoint()
def main(max_concurrent: int = 5) -> None:
    """Local entrypoint for running the migration via Modal."""
    migrate_all_versions.remote(max_concurrent)
