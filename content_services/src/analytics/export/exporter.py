"""Driver-specific JSON export for analytics integration."""

import logging
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pydantic import BaseModel

from analytics.storage.hot_storage import HotStorage
from analytics.storage.parquet_storage import ParquetStorage

from .schemas import (
    ActivityEntry,
    ActivityJSON,
    BranchEntry,
    BranchesJSON,
    ContributorEntry,
    DirectoryOwnership,
    MetadataJSON,
    OverviewJSON,
    OwnershipJSON,
)

logger = logging.getLogger(__name__)


# Constants for branch status computation
STALE_THRESHOLD_DAYS = 30


def _compute_branch_status(branch: dict) -> str:
    """Compute branch display status based on activity and state.

    Status priority:
    1. "merged" - Branch was merged and deleted
    2. "deleted" - Branch was deleted (but not merged)
    3. "default" - The default branch (always shown as default)
    4. "stale" - No commits in 30+ days
    5. "active" - Has commits within the last 30 days

    Args:
        branch: Branch data dict with keys:
            - is_default_branch: bool
            - is_deleted: bool (optional)
            - is_merged: bool (optional)
            - last_commit_at: datetime or ISO string (optional)

    Returns:
        Status string: "default", "active", "stale", "deleted", or "merged"
    """
    # Check merged status first (merged + deleted)
    if branch.get("is_merged"):
        return "merged"

    # Check deleted status
    if branch.get("is_deleted"):
        return "deleted"

    # Default branch always has 'default' status
    if branch.get("is_default_branch"):
        return "default"

    # Get last commit date
    last_commit = branch.get("last_commit_at")

    if last_commit is None:
        # No commit date = assume it's new/active
        return "active"

    # Handle string dates (ISO format)
    if isinstance(last_commit, str):
        try:
            last_commit = datetime.fromisoformat(last_commit.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return "active"  # Can't parse, assume active

    # Ensure timezone-aware comparison
    now = datetime.now(UTC)
    if last_commit.tzinfo is None:
        last_commit = last_commit.replace(tzinfo=UTC)

    # Check 30-day stale threshold
    age = now - last_commit
    if age > timedelta(days=STALE_THRESHOLD_DAYS):
        return "stale"

    return "active"


class DriverJSONExporter:
    """Export analytics as JSON files for Driver integration.

    Creates separate JSON files matching Driver's API structure:
    - overview.json
    - branches.json
    - activity.json
    - ownership.json  (code ownership by directory, includes contributor data)
    - metadata.json

    Note: No separate contributors.json - contributor data is embedded in ownership.json
    """

    def __init__(
        self,
        codebase_id: str,
        hot_storage: HotStorage,
        warm_storage: ParquetStorage | None = None,
        cold_storage: ParquetStorage | None = None,
        output_dir: Path | None = None,
        deleted_branches: list[dict] | None = None,
    ) -> None:
        self.codebase_id = codebase_id
        self.hot = hot_storage
        self.warm_storage = warm_storage
        self.cold_storage = cold_storage
        self.output_dir = output_dir or Path(".")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.deleted_branches = deleted_branches or []

    def export_all(
        self,
        last_commit_sha: str | None = None,
        last_commit_date: datetime | None = None,
        total_commits: int = 0,
    ) -> list[Path]:
        """Export all JSON files for this codebase.

        Args:
            last_commit_sha: SHA of latest processed commit (for checkpoint)
            last_commit_date: Date of latest processed commit
            total_commits: Total commits processed

        Returns:
            List of exported file paths
        """
        start = time.time()

        files = [
            self._export_overview(),
            self._export_branches(),
            self._export_activity(),
            self._export_ownership(),  # Code ownership + contributor data
        ]

        files.append(
            self._export_metadata(
                duration=time.time() - start,
                last_commit_sha=last_commit_sha,
                last_commit_date=last_commit_date,
                total_commits=total_commits,
            )
        )
        return [f for f in files if f]

    def _export_overview(self) -> Path | None:
        """Export overview.json directly from hot storage.

        Hot storage now uses clean field names matching the export schema.
        """
        metrics = self.hot.get_repository_metrics(self.codebase_id)
        if not metrics:
            return None

        # Extract owner from full_name (format: "owner/repo")
        full_name = metrics.get("full_name", "")
        owner = full_name.split("/")[0] if "/" in full_name else ""

        overview = OverviewJSON(
            codebase_id=self.codebase_id,
            display_name=metrics.get("repository_name", self.codebase_id),
            repository_name=metrics.get("repository_name", self.codebase_id),
            full_name=full_name,
            owner=owner,
            total_commits=metrics.get("total_commits", 0),
            total_contributors=metrics.get("total_contributors", 0),
            total_branches=metrics.get("total_branches", 0),
            # Current codebase state (from tree walk at HEAD)
            current_sloc=metrics.get("current_sloc", 0),
            current_lines=metrics.get("current_lines", 0),
            # Line-based cumulative activity
            additions_lines=metrics.get("additions_lines", 0),
            deletions_lines=metrics.get("deletions_lines", 0),
            churn_lines=metrics.get("churn_lines", 0),
            net_lines=metrics.get("net_lines", 0),
            # SLOC-based cumulative activity
            additions_sloc=metrics.get("additions_sloc", 0),
            deletions_sloc=metrics.get("deletions_sloc", 0),
            churn_sloc=metrics.get("churn_sloc", 0),
            net_sloc=metrics.get("net_sloc", 0),
            # Other metrics
            avg_bytes_per_line=metrics.get("avg_bytes_per_line"),
            total_files=metrics.get("total_files", 0),
            default_branch=metrics.get("default_branch", "main"),
            primary_language=metrics.get("primary_language"),
            first_commit_date=metrics.get("first_commit_at"),
            last_commit_date=metrics.get("last_commit_at"),
            collected_at=metrics.get("collected_at") or datetime.now(UTC),
            last_updated_at=metrics.get("last_updated_at") or datetime.now(UTC),
        )

        return self._write("overview.json", overview)

    def _export_branches(self) -> Path | None:
        """Export branches.json directly from hot storage.

        Hot storage now uses clean field names matching the export schema.
        Includes both active branches from hot storage and deleted branches
        that were detected during branch lifecycle processing.
        """
        branches = self.hot.get_all_branch_metrics(self.codebase_id)
        if not branches and not self.deleted_branches:
            return None

        # Get names of deleted branches to filter them from hot storage results
        # (hot storage derives branches from commits, so deleted branches still appear)
        deleted_names = {d.get("name") for d in self.deleted_branches if d.get("name")}

        logger.info(
            f"Exporting branches: {len(branches or [])} in hot storage, {len(self.deleted_branches)} marked deleted"
        )
        logger.info(f"Deleted branch names to filter: {sorted(deleted_names)}")

        hot_storage_branch_names = [b.get("branch_name") for b in (branches or [])]
        logger.info(f"Hot storage branch names: {sorted(hot_storage_branch_names)}")

        # Build branch entries from hot storage (active branches only)
        branch_entries = []
        for b in branches or []:
            branch_name = b.get("branch_name")
            # Skip branches that have been deleted - they'll be added with proper flags below
            if branch_name in deleted_names:
                logger.info(
                    f"Filtering out deleted branch from hot storage: {branch_name}"
                )
                continue

            branch_entries.append(
                BranchEntry(
                    name=b.get("branch_name"),
                    is_default=b.get("is_default_branch", False),
                    commits=b.get("total_commits", 0),
                    last_commit_date=b.get("last_commit_at"),
                    last_analyzed_at=b.get("last_analyzed_at") or datetime.now(UTC),
                    status=_compute_branch_status(b),
                    # Branch metadata
                    head_commit_sha=b.get("head_commit_sha", ""),
                    divergence_point_sha=b.get("divergence_point_sha"),
                    parent_branch=b.get("parent_branch"),
                    created_at=b.get("created_at"),
                    # Line-based metrics (directly from hot storage)
                    current_lines=b.get("current_lines", 0),
                    unique_lines=b.get("unique_lines", 0),
                    additions_lines=b.get("additions_lines", 0),
                    deletions_lines=b.get("deletions_lines", 0),
                    # SLOC-based metrics (directly from hot storage)
                    current_sloc=b.get("current_sloc", 0),
                    churn_sloc=b.get("churn_sloc", 0),
                    unique_sloc=b.get("unique_sloc", 0),
                    additions_sloc=b.get("additions_sloc", 0),
                    deletions_sloc=b.get("deletions_sloc", 0),
                    # Branch stats
                    unique_commits=b.get("unique_commits", 0),
                    unique_contributors=b.get("unique_contributors", 0),
                    total_files=b.get("total_files", 0),
                    # Branch state flags
                    is_active=b.get("is_active", True),
                    is_merged=b.get("is_merged", False),
                    is_deleted=b.get("is_deleted", False),
                    merged_at=b.get("merged_at"),
                    deleted_at=b.get("deleted_at"),
                )
            )

        # Add deleted branches (from branch lifecycle detection)
        # Preserve all historical metrics so users can see what the branch contributed
        logger.info(f"Adding {len(self.deleted_branches)} deleted branches to export")
        for d in self.deleted_branches:
            logger.info(
                f"Adding deleted branch: {d.get('name')} (status={d.get('status')})"
            )
            branch_entries.append(
                BranchEntry(
                    name=d.get("name", ""),
                    is_default=False,
                    commits=d.get("commits", 0),
                    last_commit_date=d.get("last_commit_date"),
                    last_analyzed_at=datetime.now(UTC),
                    status=d.get("status", "deleted"),
                    # Branch metadata
                    head_commit_sha=d.get("head_commit_sha", ""),
                    divergence_point_sha=d.get("divergence_point_sha"),
                    parent_branch=d.get("parent_branch"),
                    created_at=d.get("created_at"),
                    # Historical line-based metrics (directly from stored data)
                    current_lines=d.get("current_lines", 0),
                    unique_lines=d.get("unique_lines", 0),
                    additions_lines=d.get("additions_lines", 0),
                    deletions_lines=d.get("deletions_lines", 0),
                    # Historical SLOC-based metrics (directly from stored data)
                    current_sloc=d.get("current_sloc", 0),
                    churn_sloc=d.get("churn_sloc", 0),
                    unique_sloc=d.get("unique_sloc", 0),
                    additions_sloc=d.get("additions_sloc", 0),
                    deletions_sloc=d.get("deletions_sloc", 0),
                    # Historical branch stats
                    unique_commits=d.get("unique_commits", 0),
                    unique_contributors=d.get("unique_contributors", 0),
                    total_files=d.get("total_files", 0),
                    # Branch state flags
                    is_active=False,
                    is_merged=d.get("is_merged", False),
                    is_deleted=True,
                    merged_at=d.get("merged_at"),
                    deleted_at=d.get("deleted_at"),
                )
            )

        data = BranchesJSON(
            codebase_id=self.codebase_id,
            branches=branch_entries,
        )

        return self._write("branches.json", data)

    def _export_activity(self) -> Path | None:
        """Export activity.json using existing HotStorage patterns."""
        # Last 365 days of daily metrics
        metrics = self.hot.get_daily_metrics(self.codebase_id)
        if not metrics:
            return None

        data = ActivityJSON(
            codebase_id=self.codebase_id,
            daily_activity=[
                ActivityEntry(
                    date=str(m.get("date")),
                    commits=m.get("commits_count", 0),
                    # Line-based metrics
                    additions=m.get("additions_lines", 0),
                    deletions=m.get("deletions_lines", 0),
                    active_contributors=m.get("active_contributors", 0),
                    files_changed=m.get("files_changed", 0),
                    cumulative_lines=m.get("cumulative_lines", 0),
                    # Byte-based metrics for SLOC calculation
                    addition_bytes=m.get("addition_bytes", 0),
                    deletion_bytes=m.get("deletion_bytes", 0),
                    net_bytes=m.get("net_bytes", 0),
                    patch_bytes=m.get("patch_bytes", 0),
                    cumulative_sloc=m.get("cumulative_sloc", 0),
                    # Tree-based actual codebase size
                    codebase_sloc=m.get("codebase_sloc", 0),
                    codebase_lines=m.get("codebase_lines", 0),
                )
                for m in metrics[-365:]  # Last year
            ],
        )

        return self._write("activity.json", data)

    def _export_ownership(self) -> Path | None:
        """Export ownership.json with code ownership by directory.

        This includes contributor data - the same data used by both the
        CodeOwnershipMap and ContributorStatsTable components.
        """
        if not self.warm_storage or not self.cold_storage:
            return None

        import pandas as pd

        # Get file changes from cold storage
        file_changes_df = self.cold_storage.read_file_changes(self.codebase_id)
        if file_changes_df is None or len(file_changes_df) == 0:
            return None

        # Get commits from warm storage
        commits_df = self.warm_storage.read_commits(self.codebase_id)
        if commits_df is None or len(commits_df) == 0:
            return None

        commits_df = commits_df.drop_duplicates(subset=["commit_sha"], keep="first")

        # Join and compute ownership
        joined = file_changes_df.merge(commits_df, on="commit_sha", how="inner")
        if joined.empty:
            return None

        # Extract directory (first two path components)
        def extract_directory(path: str) -> str:
            if not path or pd.isna(path):
                return "root"
            parts = path.split("/")
            if len(parts) <= 1:
                return "root"
            elif len(parts) == 2:
                return parts[0]
            else:
                return "/".join(parts[:2])

        joined["directory"] = joined["file_path"].apply(extract_directory)

        # Calculate SLOC estimate from bytes (separate additions and deletions)
        add_col = (
            "addition_bytes_x"
            if "addition_bytes_x" in joined.columns
            else "addition_bytes"
        )
        del_col = (
            "deletion_bytes_x"
            if "deletion_bytes_x" in joined.columns
            else "deletion_bytes"
        )

        joined["additions_sloc"] = (joined[add_col].fillna(0) / 50).astype(int)
        joined["deletions_sloc"] = (joined[del_col].fillna(0) / 50).astype(int)
        joined["churn_sloc"] = joined["additions_sloc"] + joined["deletions_sloc"]

        # Aggregate by directory and contributor
        ownership = (
            joined.groupby(["directory", "author_email", "author_name"])
            .agg(
                {
                    "churn_sloc": "sum",
                    "additions_sloc": "sum",
                    "deletions_sloc": "sum",
                    "commit_sha": "nunique",
                    "committed_at": ["min", "max", "nunique"],
                }
            )
            .reset_index()
        )
        ownership.columns = [
            "directory",
            "author_email",
            "author_name",
            "churn_sloc",
            "additions_sloc",
            "deletions_sloc",
            "commits",
            "first_commit_at",
            "last_commit_at",
            "active_days",
        ]

        # Calculate totals and ownership percentages
        dir_totals = ownership.groupby("directory")["churn_sloc"].sum()
        ownership["ownership_pct"] = (
            ownership["churn_sloc"] / ownership["directory"].map(dir_totals) * 100
        ).fillna(0.0)

        contributor_counts = ownership.groupby("directory")["author_email"].nunique()
        ownership = ownership.sort_values(
            ["directory", "churn_sloc"], ascending=[True, False]
        )

        # Build result
        directories = []
        for directory in ownership["directory"].unique():
            dir_data = ownership[ownership["directory"] == directory]
            churn_sloc = int(dir_totals[directory])
            total_contributors = int(contributor_counts[directory])

            top_contributors = dir_data.head(10)  # Max 10 per directory
            if len(top_contributors) == 0:
                continue

            primary = top_contributors.iloc[0]

            contributors = [
                ContributorEntry(
                    contributor_email=str(c["author_email"]),
                    contributor_name=str(c["author_name"]),
                    total_commits=int(c["commits"]),
                    churn_sloc=int(c["churn_sloc"]),
                    additions_sloc=int(c["additions_sloc"]),
                    deletions_sloc=int(c["deletions_sloc"]),
                    ownership_percentage=float(c["ownership_pct"]),
                    first_commit_at=c["first_commit_at"],
                    last_commit_at=c["last_commit_at"],
                    active_days=int(c["active_days"]),
                )
                for _, c in top_contributors.iterrows()
            ]

            directories.append(
                DirectoryOwnership(
                    directory_path=str(directory),
                    total_commits=int(dir_data["commits"].sum()),
                    churn_sloc=churn_sloc,
                    unique_contributors=total_contributors,
                    primary_owner_email=str(primary["author_email"]),
                    primary_owner_name=str(primary["author_name"]),
                    primary_owner_percentage=float(primary["ownership_pct"]),
                    contributors=contributors,
                )
            )

        # Sort by churn SLOC descending
        directories.sort(key=lambda x: x.churn_sloc, reverse=True)

        data = OwnershipJSON(
            codebase_id=self.codebase_id,
            directories=directories,
        )

        return self._write("ownership.json", data)

    def _export_metadata(
        self,
        duration: float,
        last_commit_sha: str | None = None,
        last_commit_date: datetime | None = None,
        total_commits: int = 0,
    ) -> Path:
        """Export metadata.json with generation info and checkpoint data.

        Args:
            duration: Processing duration in seconds
            last_commit_sha: SHA of the latest processed commit (for checkpoint)
            last_commit_date: Date of the latest processed commit
            total_commits: Total commits processed

        Returns:
            Path to written metadata.json
        """
        data = MetadataJSON(
            codebase_id=self.codebase_id,
            generated_at=datetime.now(UTC),
            status="complete",
            generation_seconds=duration,
            pipeline_version="2.0",
            last_processed_commit_sha=last_commit_sha,
            last_processed_commit_date=last_commit_date,
            total_commits_processed=total_commits,
        )

        return self._write("metadata.json", data)

    def _write(self, filename: str, data: "BaseModel") -> Path:
        """Write Pydantic model to JSON file."""
        path = self.output_dir / filename
        path.write_text(data.model_dump_json(indent=2))
        return path
