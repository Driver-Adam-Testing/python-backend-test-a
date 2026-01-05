"""Pydantic schemas for Driver JSON export."""
from datetime import datetime
from pydantic import BaseModel, Field


class OverviewJSON(BaseModel):
    """Schema for overview.json - codebase summary metrics.
    
    All metrics measure ANALYZABLE CODE ONLY (matching inspector criteria).
    
    Naming convention:
    - current_* : Current codebase state from tree walk at HEAD
    - *_lines   : Line-based metrics (from git diff stats)
    - *_sloc    : SLOC metrics (bytes / 50, from patch content)
    - net_*     : additions - deletions
    - churn_*   : additions + deletions (total activity)
    """
    codebase_id: str
    display_name: str
    repository_name: str
    full_name: str
    owner: str
    total_commits: int
    total_contributors: int
    total_branches: int
    
    # Current codebase state (from tree walk at HEAD)
    current_sloc: int       # SLOC in codebase now (tree_bytes / 50)
    current_lines: int      # Line count in codebase now (from tree walk)
    
    # Cumulative line-based activity (sum across all commits)
    additions_lines: int    # Total lines added over time
    deletions_lines: int    # Total lines deleted over time
    churn_lines: int        # additions_lines + deletions_lines
    net_lines: int          # additions_lines - deletions_lines
    
    # Cumulative SLOC-based activity (sum across all commits)
    additions_sloc: int     # Total SLOC added (addition_bytes / 50)
    deletions_sloc: int     # Total SLOC deleted (deletion_bytes / 50)
    churn_sloc: int         # additions_sloc + deletions_sloc
    net_sloc: int           # additions_sloc - deletions_sloc
    
    # Other metrics
    avg_bytes_per_line: float | None  # Average bytes per line ratio
    total_files: int        # Total number of files
    default_branch: str
    primary_language: str | None
    first_commit_date: datetime | None
    last_commit_date: datetime | None
    collected_at: datetime  # When repository data was collected/ingested
    last_updated_at: datetime  # When this JSON was generated


class BranchEntry(BaseModel):
    """Branch metrics entry for branches.json.
    
    All metrics measure ANALYZABLE CODE ONLY.
    """
    name: str
    is_default: bool
    commits: int
    last_commit_date: datetime | None
    last_analyzed_at: datetime  # When branch metrics were computed
    status: str  # "active", "stale", "merged"
    # Branch metadata
    head_commit_sha: str = ""
    divergence_point_sha: str | None = None
    parent_branch: str | None = None
    created_at: datetime | None = None
    # Line-based metrics
    current_lines: int = 0
    unique_lines: int = 0
    additions_lines: int = 0    # Total lines added (was total_additions_lines)
    deletions_lines: int = 0    # Total lines deleted (was total_deletions_lines)
    # SLOC-based metrics
    current_sloc: int = 0
    churn_sloc: int = 0
    unique_sloc: int = 0
    additions_sloc: int = 0     # SLOC added (was total_addition_bytes / 50)
    deletions_sloc: int = 0     # SLOC deleted (was total_deletion_bytes / 50)
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


class BranchesJSON(BaseModel):
    """Schema for branches.json"""
    codebase_id: str
    branches: list[BranchEntry]


class ContributorEntry(BaseModel):
    """Single contributor within a directory."""
    contributor_email: str
    contributor_name: str
    total_commits: int
    churn_sloc: int  # Total SLOC touched (additions + deletions)
    additions_sloc: int  # SLOC added
    deletions_sloc: int  # SLOC deleted
    ownership_percentage: float
    first_commit_at: datetime | None
    last_commit_at: datetime | None
    active_days: int


class DirectoryOwnership(BaseModel):
    """Ownership data for a single directory."""
    directory_path: str
    total_commits: int
    churn_sloc: int  # Total SLOC touched in this directory
    unique_contributors: int
    primary_owner_email: str | None
    primary_owner_name: str | None
    primary_owner_percentage: float
    contributors: list[ContributorEntry]


class OwnershipJSON(BaseModel):
    """Schema for ownership.json - code ownership by directory."""
    codebase_id: str
    directories: list[DirectoryOwnership]


class ActivityEntry(BaseModel):
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


class ActivityJSON(BaseModel):
    """Schema for activity.json"""
    codebase_id: str
    daily_activity: list[ActivityEntry]


class MetadataJSON(BaseModel):
    """Schema for metadata.json - generation info + checkpoint for incremental updates."""
    codebase_id: str
    generated_at: datetime
    status: str  # "complete", "partial", "failed"
    generation_seconds: float
    # Checkpoint fields for incremental updates
    pipeline_version: str = "2.0"
    last_processed_commit_sha: str | None = None
    last_processed_commit_date: datetime | None = None
    total_commits_processed: int = 0


class CodebaseListEntry(BaseModel):
    """Codebase entry for codebases_list.json."""
    codebase_id: str
    display_name: str
    total_commits: int
    current_sloc: int
    last_commit_date: datetime | None
    analytics_status: str
    # Additional fields for frontend Analytics table
    total_contributors: int = 0
    total_branches: int = 0
    primary_language: str | None = None
    churn_lines: int = 0  # additions_lines + deletions_lines (was total_churn)


class OrgSummaryJSON(BaseModel):
    """Schema for org_summary.json"""
    organization_id: str
    total_codebases: int
    codebases_with_analytics: int
    generated_at: datetime


class CodebasesListJSON(BaseModel):
    """Schema for codebases_list.json"""
    organization_id: str
    codebases: list[CodebaseListEntry]
    generated_at: datetime

