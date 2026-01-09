"""Checkpoint data class and storage for analytics resume capability.

This module provides:
- ExtractionCheckpoint: Pydantic model for checkpoint state
- S3 upload/download functions
- Local file cache functions
- Validation logic
"""

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

import boto3
from botocore.exceptions import ClientError
from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    import pygit2

logger = logging.getLogger(__name__)

# Increment this when checkpoint schema changes
CHECKPOINT_VERSION = "1.0"


class ExtractionCheckpoint(BaseModel):
    """In-flight checkpoint for fault-tolerant extraction.

    This model captures the state needed to resume extraction
    after a failure or timeout.
    """

    # Schema version for compatibility
    version: str = CHECKPOINT_VERSION

    # Identity
    codebase_id: str

    # Timing
    started_at: datetime
    last_updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    # Progress tracking
    commits_total: int
    commits_processed: int
    last_processed_index: int
    last_processed_sha: str

    # Tree size cache from Rust (SHA -> (bytes, lines))
    tree_size_cache: dict[str, tuple[int, int]]

    model_config = ConfigDict(
        # Pydantic V2 handles datetime serialization automatically with ISO format
    )


def validate_checkpoint_version(checkpoint_data: dict) -> bool:
    """Check if checkpoint version matches current version.

    Args:
        checkpoint_data: Raw checkpoint data dict

    Returns:
        True if version matches, False otherwise
    """
    version = checkpoint_data.get("version", "unknown")
    if version != CHECKPOINT_VERSION:
        logger.warning(
            f"Checkpoint version mismatch: {version} != {CHECKPOINT_VERSION}"
        )
        return False
    return True


def validate_checkpoint(
    repo: "pygit2.Repository", checkpoint: ExtractionCheckpoint
) -> bool:
    """Validate checkpoint is still valid for the repository.

    Checks that the last processed commit still exists (handles force push).

    Args:
        repo: pygit2.Repository instance
        checkpoint: Checkpoint to validate

    Returns:
        True if valid, False if checkpoint should be discarded
    """
    try:
        obj = repo.get(checkpoint.last_processed_sha)
        if obj is None:
            logger.warning(
                f"Checkpoint references missing commit {checkpoint.last_processed_sha}"
            )
            return False
        return True
    except (KeyError, ValueError) as e:
        logger.warning(
            f"Checkpoint references missing commit {checkpoint.last_processed_sha}: {e}"
        )
        return False


# S3 Storage Functions


def _get_checkpoint_key(codebase_id: str) -> str:
    """Get the S3 key for a checkpoint."""
    return f"analytics/{codebase_id}/checkpoint.json"


def upload_checkpoint(
    checkpoint: ExtractionCheckpoint,
    bucket: str,
    s3_client: Any = None,
) -> None:
    """Upload checkpoint to S3.

    Args:
        checkpoint: Checkpoint to upload
        bucket: S3 bucket name
        s3_client: Optional boto3 S3 client (for testing)
    """
    if s3_client is None:
        s3_client = boto3.client("s3")

    key = _get_checkpoint_key(checkpoint.codebase_id)
    body = checkpoint.model_dump_json().encode("utf-8")

    logger.info(f"Uploading checkpoint to s3://{bucket}/{key} ({len(body)} bytes)")
    s3_client.put_object(
        Bucket=bucket,
        Key=key,
        Body=body,
        ContentType="application/json",
    )


def download_checkpoint(
    bucket: str,
    codebase_id: str,
    s3_client: Any = None,
) -> ExtractionCheckpoint | None:
    """Download checkpoint from S3.

    Args:
        bucket: S3 bucket name
        codebase_id: Codebase ID to download checkpoint for
        s3_client: Optional boto3 S3 client (for testing)

    Returns:
        ExtractionCheckpoint if found and valid, None otherwise
    """
    if s3_client is None:
        s3_client = boto3.client("s3")

    key = _get_checkpoint_key(codebase_id)

    try:
        response = s3_client.get_object(Bucket=bucket, Key=key)
        body = response["Body"].read()

        # Parse and validate version first
        data = json.loads(body)
        if not validate_checkpoint_version(data):
            logger.warning("Discarding checkpoint due to version mismatch")
            return None

        checkpoint = ExtractionCheckpoint.model_validate_json(body)
        logger.info(
            f"Downloaded checkpoint: {checkpoint.commits_processed}/{checkpoint.commits_total} commits"
        )
        return checkpoint

    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchKey":
            logger.debug(f"No checkpoint found at s3://{bucket}/{key}")
            return None
        logger.warning(f"Error downloading checkpoint: {e}")
        return None
    except (json.JSONDecodeError, ValueError) as e:
        logger.warning(f"Checkpoint corrupted or invalid: {e}")
        return None


def delete_checkpoint(
    bucket: str,
    codebase_id: str,
    s3_client: Any = None,
) -> None:
    """Delete checkpoint from S3.

    Args:
        bucket: S3 bucket name
        codebase_id: Codebase ID to delete checkpoint for
        s3_client: Optional boto3 S3 client (for testing)
    """
    if s3_client is None:
        s3_client = boto3.client("s3")

    key = _get_checkpoint_key(codebase_id)
    logger.info(f"Deleting checkpoint at s3://{bucket}/{key}")
    s3_client.delete_object(Bucket=bucket, Key=key)


# Local File Cache Functions


def write_local_checkpoint(
    checkpoint: ExtractionCheckpoint,
    path: Path,
) -> None:
    """Write checkpoint to local file.

    Args:
        checkpoint: Checkpoint to write
        path: Local file path
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(checkpoint.model_dump_json())
    logger.debug(f"Wrote local checkpoint to {path}")


def read_local_checkpoint(path: Path) -> ExtractionCheckpoint | None:
    """Read checkpoint from local file.

    Args:
        path: Local file path

    Returns:
        ExtractionCheckpoint if found and valid, None otherwise
    """
    if not path.exists():
        return None

    try:
        data = json.loads(path.read_text())
        if not validate_checkpoint_version(data):
            return None
        return ExtractionCheckpoint.model_validate(data)
    except (json.JSONDecodeError, ValueError) as e:
        logger.warning(f"Local checkpoint corrupted: {e}")
        return None
