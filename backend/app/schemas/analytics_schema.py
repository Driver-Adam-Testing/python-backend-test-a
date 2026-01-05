"""Analytics response schemas for GitStats integration.

These schemas match the JSON files exported by GitStats DriverJSONExporter.
See: gitstats/src/gitstats/export/schemas.py
"""

from datetime import datetime

from pydantic import BaseModel, Field


# === Organization-Level Schemas ===


class OrgAnalyticsSummary(BaseModel):
    """Summary metrics across all codebases (org_summary.json)."""

    organization_id: str
    total_codebases: int
    codebases_with_analytics: int
    generated_at: datetime


class CodebaseListItem(BaseModel):
    """Codebase entry in the list view (from codebases_list.json).
    
    Note: Uses validation_alias to accept both old (total_churn) and new (churn_lines)
    field names during the transition period.
    """

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
    # Accept both old (total_churn) and new (churn_lines) field names
    churn_lines: int = Field(default=0, validation_alias="churn_lines")
    
    def __init__(self, **data):
        # Handle legacy field name
        if "total_churn" in data and "churn_lines" not in data:
            data["churn_lines"] = data.pop("total_churn")
        super().__init__(**data)


class CodebasesListResponse(BaseModel):
    """List of codebases with analytics status (codebases_list.json)."""

    organization_id: str
    codebases: list[CodebaseListItem]
    generated_at: datetime


# === Codebase-Level Schemas ===


class AnalyticsOverview(BaseModel):
    """Overview metrics for a single codebase (overview.json).

    Contains 25+ fields covering commits, SLOC, line metrics, and timestamps.
    
    Note: Handles legacy field names from old S3 data during transition period.
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
    
    def __init__(self, **data):
        # Handle legacy field mappings from old S3 data
        legacy_mappings = {
            "total_additions_lines": "additions_lines",
            "total_deletions_lines": "deletions_lines",
            "total_churn": "churn_lines",
            "total_lines": "net_lines",
            "total_addition_bytes": "_addition_bytes",  # Will convert to sloc
            "total_deletion_bytes": "_deletion_bytes",  # Will convert to sloc
            "total_sloc": "churn_sloc",
        }
        for old_name, new_name in legacy_mappings.items():
            if old_name in data and new_name not in data:
                data[new_name] = data.pop(old_name)
        
        # Convert bytes to SLOC if needed
        if "_addition_bytes" in data and "additions_sloc" not in data:
            data["additions_sloc"] = data.pop("_addition_bytes") // 50
        if "_deletion_bytes" in data and "deletions_sloc" not in data:
            data["deletions_sloc"] = data.pop("_deletion_bytes") // 50
        
        # Calculate churn_lines if not present
        if "churn_lines" not in data and "additions_lines" in data:
            data["churn_lines"] = data.get("additions_lines", 0) + data.get("deletions_lines", 0)
        
        super().__init__(**data)


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
    additions_lines: int = 0  # Was total_additions_lines
    deletions_lines: int = 0  # Was total_deletions_lines
    # SLOC-based metrics
    current_sloc: int = 0
    churn_sloc: int = 0
    unique_sloc: int = 0
    additions_sloc: int = 0  # Was total_addition_bytes / 50
    deletions_sloc: int = 0  # Was total_deletion_bytes / 50
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
    
    def __init__(self, **data):
        # Handle legacy field mappings from old S3 data
        legacy_mappings = {
            "total_additions_lines": "additions_lines",
            "total_deletions_lines": "deletions_lines",
            "total_addition_bytes": "_addition_bytes",
            "total_deletion_bytes": "_deletion_bytes",
        }
        for old_name, new_name in legacy_mappings.items():
            if old_name in data and new_name not in data:
                data[new_name] = data.pop(old_name)
        
        # Convert bytes to SLOC if needed
        if "_addition_bytes" in data and "additions_sloc" not in data:
            data["additions_sloc"] = data.pop("_addition_bytes") // 50
        if "_deletion_bytes" in data and "deletions_sloc" not in data:
            data["deletions_sloc"] = data.pop("_deletion_bytes") // 50
        
        super().__init__(**data)


class BranchesResponse(BaseModel):
    """Branch data for a codebase (branches.json)."""

    codebase_id: str
    branches: list[BranchMetrics]


class ContributorEntry(BaseModel):
    """Contributor's ownership in a directory (ownership.json nested)."""

    contributor_email: str
    contributor_name: str
    total_commits: int
    churn_sloc: int = Field(0, alias="total_sloc")  # Total SLOC touched (additions + deletions)
    additions_sloc: int = 0  # SLOC added
    deletions_sloc: int = 0  # SLOC deleted
    ownership_percentage: float
    first_commit_at: datetime | None
    last_commit_at: datetime | None
    active_days: int

    model_config = {"populate_by_name": True}

    def __init__(self, **data):
        # Handle legacy data that only has total_sloc
        if "total_sloc" in data and "churn_sloc" not in data:
            data["churn_sloc"] = data.pop("total_sloc")
        # If we have churn_sloc but not additions/deletions, approximate
        if "churn_sloc" in data and "additions_sloc" not in data:
            # Can't split without more info, so default to all additions
            data["additions_sloc"] = data.get("churn_sloc", 0)
            data["deletions_sloc"] = 0
        super().__init__(**data)


class DirectoryOwnership(BaseModel):
    """Ownership data for a directory (ownership.json entry)."""

    directory_path: str
    total_commits: int
    churn_sloc: int = Field(0, alias="total_sloc")  # Total SLOC touched
    unique_contributors: int
    primary_owner_email: str | None
    primary_owner_name: str | None
    primary_owner_percentage: float
    contributors: list[ContributorEntry]

    model_config = {"populate_by_name": True}

    def __init__(self, **data):
        # Handle legacy data
        if "total_sloc" in data and "churn_sloc" not in data:
            data["churn_sloc"] = data.pop("total_sloc")
        super().__init__(**data)


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

