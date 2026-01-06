"""Shared analytics cleanup utilities.

Used by both:
- Backend API (when user deletes codebase via UI)
- Onboarding handlers (when repo is deleted via GitHub/GitLab/etc webhook)
"""

import json
import logging
from datetime import UTC, datetime
from typing import Any

import boto3
from botocore.exceptions import ClientError

from shared.file_storage.aws_s3_client import org_id_to_hash

logger = logging.getLogger(__name__)


def delete_analytics_folder(
    s3_resource: Any,
    bucket_name: str,
    codebase_id: str,
) -> None:
    """Delete all analytics files for a codebase.

    Args:
        s3_resource: boto3 S3 resource (not client)
        bucket_name: Name of the org S3 bucket (hashed org ID)
        codebase_id: UUID string of the codebase to clean up
    """
    prefix = f"analytics/{codebase_id}/"
    try:
        bucket = s3_resource.Bucket(bucket_name)
        objects = list(bucket.objects.filter(Prefix=prefix))
        if objects:
            bucket.objects.filter(Prefix=prefix).delete()
            logger.info(
                f"Deleted {len(objects)} analytics files for codebase {codebase_id}"
            )
        else:
            logger.info(f"No analytics files found for codebase {codebase_id}")
    except Exception as e:
        logger.warning(f"Failed to delete analytics folder for {codebase_id}: {e}")
        # Don't raise - continue with deletion


def update_org_files_after_deletion(
    s3_client: Any,
    bucket_name: str,
    organization_id: str,
    deleted_codebase_id: str,
) -> None:
    """Update org-level analytics files after codebase deletion.

    Removes the deleted codebase from codebases_list.json and
    recomputes org_summary.json with updated totals.

    Args:
        s3_client: boto3 S3 client
        bucket_name: Name of the org S3 bucket (hashed org ID)
        organization_id: Organization UUID string
        deleted_codebase_id: UUID string of the deleted codebase
    """
    try:
        # 1. Update codebases_list.json
        key = "analytics/codebases_list.json"
        try:
            response = s3_client.get_object(Bucket=bucket_name, Key=key)
            data = json.loads(response["Body"].read().decode("utf-8"))
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                logger.info("No codebases_list.json to update")
                return
            raise
        except Exception as e:
            logger.warning(f"Could not read codebases_list.json: {e}")
            return

        # Remove deleted codebase
        original_count = len(data.get("codebases", []))
        data["codebases"] = [
            cb
            for cb in data.get("codebases", [])
            if cb.get("codebase_id") != deleted_codebase_id
        ]
        new_count = len(data["codebases"])

        if original_count == new_count:
            logger.info(
                f"Codebase {deleted_codebase_id} not found in codebases_list.json"
            )
            return

        data["generated_at"] = datetime.now(UTC).isoformat()

        # Upload updated list
        s3_client.put_object(
            Bucket=bucket_name,
            Key=key,
            Body=json.dumps(data, indent=2),
            ContentType="application/json",
        )
        logger.info(f"Updated codebases_list.json: removed {deleted_codebase_id}")

        # 2. Recompute org_summary.json
        codebases = data.get("codebases", [])
        summary = {
            "organization_id": organization_id,
            "total_codebases": len(codebases),
            "codebases_with_analytics": len(codebases),
            "total_commits": sum(cb.get("total_commits", 0) for cb in codebases),
            "total_contributors": sum(
                cb.get("total_contributors", 0) for cb in codebases
            ),
            "total_sloc": sum(cb.get("current_sloc", 0) for cb in codebases),
            "generated_at": datetime.now(UTC).isoformat(),
        }

        s3_client.put_object(
            Bucket=bucket_name,
            Key="analytics/org_summary.json",
            Body=json.dumps(summary, indent=2),
            ContentType="application/json",
        )
        logger.info(
            f"Recomputed org_summary.json: {len(codebases)} codebases remaining"
        )

    except Exception as e:
        logger.warning(f"Failed to update org files after deletion: {e}")
        # Don't raise - continue with deletion


def cleanup_analytics_for_codebase(
    organization_id: str,
    codebase_id: str,
    aws_region: str | None = None,
    aws_access_key_id: str | None = None,
    aws_secret_access_key: str | None = None,
    s3_endpoint_url: str | None = None,
) -> None:
    """Full analytics cleanup for a deleted codebase.

    This is the main entry point for cleaning up analytics when a codebase
    is deleted. It handles both the codebase-specific folder and the
    org-level aggregate files.

    Args:
        organization_id: Organization UUID string
        codebase_id: Codebase UUID string
        aws_region: AWS region (optional, uses default if not provided)
        aws_access_key_id: AWS access key (optional, uses IAM role if not provided)
        aws_secret_access_key: AWS secret key (optional, uses IAM role if not provided)
        s3_endpoint_url: S3 endpoint URL (optional, for localstack/testing)
    """
    bucket_name = org_id_to_hash(organization_id)

    # Build S3 client kwargs
    client_kwargs = {}
    if aws_region:
        client_kwargs["region_name"] = aws_region
    if aws_access_key_id:
        client_kwargs["aws_access_key_id"] = aws_access_key_id
    if aws_secret_access_key:
        client_kwargs["aws_secret_access_key"] = aws_secret_access_key
    if s3_endpoint_url:
        client_kwargs["endpoint_url"] = s3_endpoint_url

    s3_resource = boto3.resource("s3", **client_kwargs)
    s3_client = boto3.client("s3", **client_kwargs)

    # 1. Delete analytics folder for the codebase
    delete_analytics_folder(s3_resource, bucket_name, codebase_id)

    # 2. Update org-level files
    update_org_files_after_deletion(
        s3_client, bucket_name, organization_id, codebase_id
    )

    logger.info(f"Analytics cleanup complete for codebase {codebase_id}")
