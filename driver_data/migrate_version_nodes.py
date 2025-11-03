import hashlib
import logging
from uuid import UUID

# import boto3
from database.db import engine
from database.models import DerivedContent, Node, PrimaryAsset, Version, VersionNode
from database.models_enums import ContentKind, NodeKind, PrimaryAssetKind, VersionStatus
from sqlmodel import Session, select

# Configuration flag: Set to True to use S3 content, False to use DerivedContent long description
USE_S3 = False

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# def setup_s3_client() -> boto3.client:
#     """Initialize and return S3 client."""
#     return boto3.client(
#         "s3",
#         aws_access_key_id=settings.S3ADMIN_AWS_ACCESS_KEY_ID,
#         aws_secret_access_key=settings.S3ADMIN_AWS_SECRET_ACCESS_KEY,
#         region_name=settings.AWS_REGION,
#         endpoint_url=settings.AWS_S3_ENDPOINT_URL if settings.AWS_S3_ENDPOINT_URL else None,
#     )
#
#
# def hash_organization_id(organization_id: str) -> str:
#     """Hash organization ID to get S3 bucket name."""
#     return hashlib.sha256(organization_id.encode()).hexdigest()[:63]
#
#
# def fetch_s3_content(
#     s3_client: boto3.client,
#     organization_id: str,
#     primary_asset_id: UUID,
#     version_id: UUID,
#     relative_path: str,
# ) -> str | None:
#     """Fetch file content from S3."""
#     bucket = hash_organization_id(organization_id)
#     key = f"{primary_asset_id}/{version_id}/{relative_path.lstrip('/')}"
#
#     try:
#         obj = s3_client.get_object(Bucket=bucket, Key=key)
#         file_content = obj["Body"].read()
#         return file_content.decode("utf-8", errors="replace")
#     except s3_client.exceptions.NoSuchKey:
#         logger.warning(f"S3 content not found: {bucket}/{key}")
#         return None
#     except Exception as e:
#         logger.error(f"Error fetching S3 content for {key}: {e}")
#         return None


def fetch_long_description(session: Session, node_id: UUID) -> str | None:
    """Fetch long description content from DerivedContent for a node."""
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


def get_directory_children_hashes(
    session: Session, version_id: UUID, relative_path: str
) -> list[str]:
    """Get list of content hashes for direct children of a directory node."""
    # Add trailing slash to directory path if not present
    dir_path = relative_path if relative_path.endswith("/") else f"{relative_path}/"

    # Find all nodes that are direct children (one level deeper)
    target_depth = dir_path.count("/") - 1  # depth starts from 0

    # Join VersionNode with Node to get content hashes
    children_hashes = session.exec(
        select(Node.content_hash)
        .join(VersionNode, VersionNode.node_content_id == Node.id)
        .where(VersionNode.version_id == version_id)
        .where(VersionNode.relative_path.startswith(dir_path))
        .where(VersionNode.depth == target_depth + 1)
    ).all()
    print(f"found {len(children_hashes)} children for directory {relative_path}")

    return list(children_hashes)


def find_node_by_hash(
    session: Session, primary_asset_id: UUID, content_hash: str
) -> Node | None:
    """Find existing Node with matching hash for the same PrimaryAsset."""
    return session.exec(
        select(Node)
        .where(Node.primary_asset_id == primary_asset_id)
        .where(Node.content_hash == content_hash)
        .limit(1)
    ).first()


def migrate_file_node(
    session: Session,
    s3_client: str | None,
    version: Version,
    node: Node,
) -> None:
    """Migrate a single file node with deduplication."""
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
    content_hash = hash_file_content(content)

    # Check for existing node with same hash
    existing_node = find_node_by_hash(session, version.primary_asset_id, content_hash)

    if existing_node:
        print(
            f"Found existing node with hash {content_hash}, reusing node {existing_node.id}"
        )
        # Create VersionNode link to existing node
        version_node = VersionNode(
            version_id=version.id,
            relative_path=node.relative_path,
            primary_asset_id=version.primary_asset_id,
            node_content_id=existing_node.id,
        )
        session.add(version_node)

        # Delete old node (cascade deletes DerivedContent)
        session.delete(node)
        session.commit()
    else:
        print(f"Creating new node with hash {content_hash}")
        # Create new Node with hash
        new_node = Node(
            content_hash=content_hash,
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
            primary_asset_id=version.primary_asset_id,
            node_content_id=new_node.id,
        )
        session.add(version_node)

        # Delete old node (DerivedContent already moved, so no cascade delete)
        session.delete(node)
        session.commit()


def migrate_directory_node(
    session: Session,
    version: Version,
    node: Node,
) -> None:
    """Migrate a single directory node with content-based hashing."""
    print(f"Migrating directory node: {node.relative_path} (version: {version.id})")

    # Get children content hashes for hashing
    children_hashes = get_directory_children_hashes(
        session, version.id, node.relative_path
    )

    # Hash directory based on children content hashes
    content_hash = hash_directory_node(children_hashes)

    # Check for existing node with same hash
    existing_node = find_node_by_hash(session, version.primary_asset_id, content_hash)

    if existing_node:
        print(
            f"Found existing directory node with hash {content_hash}, reusing node {existing_node.id}"
        )
        # Create VersionNode link to existing node
        version_node = VersionNode(
            version_id=version.id,
            relative_path=node.relative_path,
            primary_asset_id=version.primary_asset_id,
            node_content_id=existing_node.id,
        )
        session.add(version_node)

        # Delete old node (cascade deletes DerivedContent)
        session.delete(node)
        session.commit()
    else:
        print(f"Creating new directory node with hash {content_hash}")
        # Create new Node with hash
        new_node = Node(
            content_hash=content_hash,
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
            primary_asset_id=version.primary_asset_id,
            node_content_id=new_node.id,
        )
        session.add(version_node)

        # Delete old node (DerivedContent already moved, so no cascade delete)
        session.delete(node)
        session.commit()


def migrate_version(
    session: Session,
    s3_client: str | None,
    version: Version,
) -> None:
    """Migrate all nodes for a specific version."""
    print(
        f"Processing version {version.id} for primary asset {version.primary_asset_id}"
    )

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
                logger.warning(
                    f"Unknown node kind: {node.kind}, skipping node {node.id}"
                )
        except Exception as e:
            logger.error(f"Error migrating node {node.id}: {e}")
            session.rollback()
            # Continue with next node


def migrate_all_versions() -> None:
    """Main migration function - processes all versions in reverse chronological order."""
    print("Starting VersionNode migration")
    print(
        f"Using {'S3 content' if USE_S3 else 'DerivedContent long description'} for hashing"
    )
    # TODO::
    # * handling versions in states besides GENERATION_COMPLETE?
    # * handling assets other than codebases?

    s3_client = None  # setup_s3_client() if USE_S3 else None

    with Session(engine) as session:
        # Get all codebase PrimaryAssets
        primary_assets = session.exec(
            select(PrimaryAsset).where(PrimaryAsset.kind == PrimaryAssetKind.CODEBASE)
        ).all()

        print(f"Found {len(primary_assets)} codebase primary assets")

        for primary_asset in primary_assets:
            if str(primary_asset.id) not in [
                "64647130-650d-4c00-9104-799dc97be024",
                "4a977ae1-ac8c-48c1-bd7e-81272467c691",
            ]:
                print(
                    f"Processing primary asset: {primary_asset.display_name} ({primary_asset.id})"
                )

                # Get all versions for this primary asset in reverse chronological order
                versions = session.exec(
                    select(Version)
                    .where(Version.primary_asset_id == primary_asset.id)
                    .where(Version.status == VersionStatus.GENERATION_COMPLETE)
                    .order_by(Version.updated_at.desc())
                ).all()

                print(
                    f"Found {len(versions)} versions for {primary_asset.display_name}"
                )

                for version in versions:
                    try:
                        migrate_version(session, s3_client, version)
                    except Exception as e:
                        print("=========\n=========\n=========")
                        logger.error(f"Error migrating version {version.id}: {e}")
                        print("=========\n=========\n=========")
                        session.rollback()
                        # Continue with next version

    print("Migration complete")


if __name__ == "__main__":
    migrate_all_versions()
