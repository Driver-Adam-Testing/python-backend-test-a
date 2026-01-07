"""Analytics response schemas for GitStats integration.

These schemas match the JSON files exported by GitStats DriverJSONExporter.
See: gitstats/src/gitstats/export/schemas.py
"""

from datetime import datetime

from pydantic import BaseModel


# === Organization-Level Schemas ===


class OrgAnalyticsSummary(BaseModel):
    """Summary metrics across all codebases (org_summary.json)."""

    organization_id: str
    total_codebases: int
    codebases_with_analytics: int
    generated_at: datetime


class CodebaseListItem(BaseModel):
    """Codebase entry in the list view (from codebases_list.json)."""

    codebase_id: str
    display_name: str
    provider: str | None = None  # github, gitlab, bitbucket, azure-devops - for icon display
    total_commits: int
    current_sloc: int
    last_commit_date: datetime | None
    analytics_status: str  # "complete" | "failed" | "none"
    # Additional fields for frontend Analytics table
    total_contributors: int = 0
    total_branches: int = 0
    primary_language: str | None = None
    churn_lines: int = 0


class CodebasesListResponse(BaseModel):
    """List of codebases with analytics status (codebases_list.json)."""

    organization_id: str
    codebases: list[CodebaseListItem]
    generated_at: datetime


# === Codebase-Level Schemas ===


class AnalyticsOverview(BaseModel):
    """Overview metrics for a single codebase (overview.json).

    Contains 25+ fields covering commits, SLOC, line metrics, and timestamps.
    """

    codebase_id: str
    display_name: str
    provider: str | None = None  # github, gitlab, bitbucket, azure-devops - for icon display
    repository_name: str
    full_name: str
    owner: str
    total_commits: int
    total_contributors: int
    total_branches: int
    # Current codebase state (from tree walk at HEAD)
    current_sloc: int  # SLOC in codebase now
    current_lines: int = 0  # Line count in codebase now

    # Cumulative line-based activity
    additions_lines: int = 0  # Total lines added over time
    deletions_lines: int = 0  # Total lines deleted over time
    churn_lines: int = 0  # additions_lines + deletions_lines
    net_lines: int = 0  # additions_lines - deletions_lines

    # Cumulative SLOC-based activity
    additions_sloc: int = 0  # SLOC added (bytes / 50)
    deletions_sloc: int = 0  # SLOC deleted (bytes / 50)
    churn_sloc: int = 0  # additions_sloc + deletions_sloc
    net_sloc: int = 0  # additions_sloc - deletions_sloc

    # Other metrics
    avg_bytes_per_line: float | None  # Average bytes per line ratio
    total_files: int
    default_branch: str
    primary_language: str | None
    first_commit_date: datetime | None
    last_commit_date: datetime | None
    collected_at: datetime  # When repository was ingested
    last_updated_at: datetime  # When JSON was generated


class BranchMetrics(BaseModel):
    """Metrics for a single branch (branches.json entry).

    Contains 23 fields covering branch metadata, line metrics, SLOC, and state.
    """

    name: str
    is_default: bool
    commits: int
    last_commit_date: datetime | None
    last_analyzed_at: datetime
    status: str  # "active", "stale", "merged"
    # Branch metadata
    head_commit_sha: str = ""
    divergence_point_sha: str | None = None
    parent_branch: str | None = None
    created_at: datetime | None = None
    # Line-based metrics
    current_lines: int = 0
    unique_lines: int = 0
    additions_lines: int = 0
    deletions_lines: int = 0
    # SLOC-based metrics
    current_sloc: int = 0
    churn_sloc: int = 0
    unique_sloc: int = 0
    additions_sloc: int = 0
    deletions_sloc: int = 0
    # Branch stats
    unique_commits: int = 0
    unique_contributors: int = 0
    total_files: int = 0
    # Branch state flags
    is_active: bool = True
    is_merged: bool = False
    is_deleted: bool = False
    merged_at: datetime | None = None
    deleted_at: datetime | None = None


class BranchesResponse(BaseModel):
    """Branch data for a codebase (branches.json)."""

    codebase_id: str
    branches: list[BranchMetrics]


class ContributorEntry(BaseModel):
    """Contributor's ownership in a directory (ownership.json nested)."""

    contributor_email: str
    contributor_name: str
    total_commits: int
    churn_sloc: int = 0  # Total SLOC touched (additions + deletions)
    additions_sloc: int = 0  # SLOC added
    deletions_sloc: int = 0  # SLOC deleted
    ownership_percentage: float
    first_commit_at: datetime | None
    last_commit_at: datetime | None
    active_days: int


class DirectoryOwnership(BaseModel):
    """Ownership data for a directory (ownership.json entry)."""

    directory_path: str
    total_commits: int
    churn_sloc: int = 0  # Total SLOC touched
    unique_contributors: int
    primary_owner_email: str | None
    primary_owner_name: str | None
    primary_owner_percentage: float
    contributors: list[ContributorEntry]


class OwnershipResponse(BaseModel):
    """Code ownership data for a codebase (ownership.json).

    Note: top_contributors is computed by frontend from directories data.
    """

    codebase_id: str
    directories: list[DirectoryOwnership]


class ActivityEntry(BaseModel):
    """Daily activity metrics (activity.json entry).

    Contains both line-based and byte-based metrics for charts.
    """

    date: str
    commits: int
    # Line-based metrics
    additions: int  # additions_lines
    deletions: int  # deletions_lines
    active_contributors: int = 0
    files_changed: int = 0
    cumulative_lines: int = 0
    # Byte-based metrics for SLOC calculation
    addition_bytes: int = 0
    deletion_bytes: int = 0
    net_bytes: int = 0
    patch_bytes: int = 0
    cumulative_sloc: int = 0
    # Tree-based actual codebase size (not cumulative churn)
    codebase_sloc: int = 0
    codebase_lines: int = 0


class ActivityResponse(BaseModel):
    """Daily activity data for a codebase (activity.json)."""

    codebase_id: str
    daily_activity: list[ActivityEntry]


class AnalyticsStatus(BaseModel):
    """Analytics generation status for a codebase (metadata.json)."""

    codebase_id: str
    generated_at: datetime | None = None
    status: str  # "complete" | "failed" | "none"
    generation_seconds: float | None = None

