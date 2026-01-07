"""Service for reading analytics JSON from S3.

Authorization Pattern:
- Uses primary_asset_grant_filter to filter codebases by admin access
- Super Admins (is_super_admin=True) see all codebases
- Source Admins (asset_admin role on codebases) see only their administered codebases
"""

import json
import logging
from typing import Any
from uuid import UUID

from botocore.exceptions import ClientError
from database.models import PrimaryAsset
from database.models_enums import PrimaryAssetProvider
from shared.authorization.helpers import is_super_admin
from shared.authorization.query_filters import (
    PrimaryAssetRole,
    primary_asset_grant_filter,
)
from sqlmodel import Session

from app.api.auth import UserToken
from app.utils.aws_s3 import org_id_to_hash, s3_client

logger = logging.getLogger(__name__)

# Map PrimaryAssetProvider enum to frontend provider strings
PROVIDER_MAP: dict[PrimaryAssetProvider, str] = {
    PrimaryAssetProvider.GITHUB: "github",
    PrimaryAssetProvider.GITLAB_SELF_MANAGED: "gitlab",
    PrimaryAssetProvider.BITBUCKET: "bitbucket",
    PrimaryAssetProvider.AZURE_DEVOPS_CLOUD: "azure-devops",
    # USER provider doesn't have an icon, will return None
}


class AnalyticsService:
    """Service for reading pre-computed analytics JSON from S3.

    Filters results based on user's admin access to codebases.
    """

    def __init__(self, session: Session, user: UserToken) -> None:
        self.session = session
        self.user = user
        self.organization_id = str(user.organization_id)
        self.bucket = org_id_to_hash(self.organization_id)

    def _read_json(self, key: str) -> dict[str, Any] | None:
        """Read a JSON file from S3. Returns None if not found."""
        try:
            response = s3_client.get_object(Bucket=self.bucket, Key=key)
            content = response["Body"].read().decode("utf-8")
            return json.loads(content)
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                logger.info(f"Analytics file not found: {key}")
                return None
            logger.error(f"Error reading analytics file {key}: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {key}: {e}")
            return None

    def _get_codebase_ids_for_user(self) -> set[UUID]:
        """Get IDs of codebases this user can administer.

        Uses primary_asset_grant_filter which returns True for super admins
        (meaning all rows match) or the appropriate filter for source admins.
        """
        filter_clause = primary_asset_grant_filter(
            self.session,
            self.user.user_id,
            self.organization_id,
            role=PrimaryAssetRole.asset_admin,
        )

        query = self.session.query(PrimaryAsset.id).where(
            PrimaryAsset.organization_id == self.organization_id,
            filter_clause,
        )
        return {row[0] for row in query.all()}

    def _get_provider_for_codebase(self, codebase_id: str) -> str | None:
        """Get the provider string for a codebase (github, gitlab, etc.)."""
        try:
            asset = (
                self.session.query(PrimaryAsset)
                .filter(PrimaryAsset.id == UUID(codebase_id))
                .first()
            )
            if asset and asset.provider:
                return PROVIDER_MAP.get(asset.provider)
        except Exception as e:
            logger.debug(f"Could not look up provider for {codebase_id}: {e}")
        return None

    def _get_providers_for_codebases(
        self, codebase_ids: list[str]
    ) -> dict[str, str | None]:
        """Get provider strings for multiple codebases in one query."""
        if not codebase_ids:
            return {}

        try:
            uuid_ids = [UUID(cid) for cid in codebase_ids]
            assets = (
                self.session.query(PrimaryAsset.id, PrimaryAsset.provider)
                .filter(PrimaryAsset.id.in_(uuid_ids))
                .all()
            )
            return {str(asset.id): PROVIDER_MAP.get(asset.provider) for asset in assets}
        except Exception as e:
            logger.debug(f"Could not look up providers: {e}")
        return {}

    # === Organization-Level Methods ===

    def get_org_summary(self) -> dict[str, Any] | None:
        """Get organization-level analytics summary.

        For Source Admins, computes a filtered summary based on their administered codebases.
        Super Admins get the full pre-computed org summary.
        """
        # Super Admin optimization: return pre-computed full org summary
        if is_super_admin(self.session, self.user.user_id, self.organization_id):
            return self._read_json("analytics/org_summary.json")

        # Source Admin - compute filtered summary from codebases list
        administered_ids = self._get_codebase_ids_for_user()
        codebases_data = self._read_json("analytics/codebases_list.json")
        if not codebases_data:
            return None

        # Filter to administered codebases and aggregate metrics
        filtered_codebases = [
            cb
            for cb in codebases_data.get("codebases", [])
            if UUID(cb["codebase_id"]) in administered_ids
        ]

        # Compute aggregated summary from filtered codebases
        return {
            "organization_id": self.organization_id,
            "total_codebases": len(filtered_codebases),
            "codebases_with_analytics": len(
                [
                    cb
                    for cb in filtered_codebases
                    if cb.get("analytics_status") == "complete"
                ]
            ),
            "total_commits": sum(
                cb.get("total_commits", 0) for cb in filtered_codebases
            ),
            "total_contributors": sum(
                cb.get("total_contributors", 0) for cb in filtered_codebases
            ),
            "total_sloc": sum(cb.get("current_sloc", 0) for cb in filtered_codebases),
            "generated_at": codebases_data.get("generated_at"),
        }

    def get_codebases_list(self) -> dict[str, Any] | None:
        """Get list of codebases with analytics status.

        Super Admins see all codebases (via primary_asset_grant_filter returning True).
        Source Admins see only codebases they administer.
        Enriches each codebase with provider information from database.
        """
        data = self._read_json("analytics/codebases_list.json")
        if not data:
            return None

        # Get IDs of codebases user can administer
        # For super admins, this returns all codebase IDs
        administered_ids = self._get_codebase_ids_for_user()

        # Filter to only administered codebases
        codebases = [
            cb
            for cb in data.get("codebases", [])
            if UUID(cb["codebase_id"]) in administered_ids
        ]

        # Enrich with provider information
        codebase_ids = [cb["codebase_id"] for cb in codebases]
        providers = self._get_providers_for_codebases(codebase_ids)
        for cb in codebases:
            cb["provider"] = providers.get(cb["codebase_id"])

        return {
            **data,
            "codebases": codebases,
            "total_codebases": len(codebases),
        }

    # === Codebase-Level Methods ===

    def get_overview(self, codebase_id: str) -> dict[str, Any] | None:
        """Get overview metrics for a codebase.

        Enriches with provider information from database.
        """
        data = self._read_json(f"analytics/{codebase_id}/overview.json")
        if data:
            data["provider"] = self._get_provider_for_codebase(codebase_id)
        return data

    def get_branches(self, codebase_id: str) -> dict[str, Any] | None:
        """Get branch data for a codebase."""
        return self._read_json(f"analytics/{codebase_id}/branches.json")

    def get_activity(self, codebase_id: str) -> dict[str, Any] | None:
        """Get activity data for a codebase."""
        return self._read_json(f"analytics/{codebase_id}/activity.json")

    def get_ownership(self, codebase_id: str) -> dict[str, Any] | None:
        """Get code ownership data for a codebase."""
        return self._read_json(f"analytics/{codebase_id}/ownership.json")

    def get_status(self, codebase_id: str) -> dict[str, Any]:
        """Get analytics status for a codebase."""
        metadata = self._read_json(f"analytics/{codebase_id}/metadata.json")
        if metadata:
            return metadata
        # If no metadata, return a "none" status
        return {
            "codebase_id": codebase_id,
            "status": "none",
            "generated_at": None,
            "generation_seconds": None,
        }
