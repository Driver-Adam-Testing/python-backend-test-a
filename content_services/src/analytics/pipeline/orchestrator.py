"""
Analytics Pipeline Orchestrator.

Coordinates all phases of the analytics pipeline:
1. Clone repository
2. Extract commits
3. Discover branches
4. Build aggregates
5. Calculate ownership
6. Export to JSON
7. Upload to S3
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
import pygit2
from pydantic import BaseModel

from analytics.storage.hot_storage import HotStorage
from analytics.storage.parquet_storage import ParquetStorage
from analytics.aggregation.engine import AggregationEngine
from analytics.export.exporter import DriverJSONExporter

from shared.file_storage.aws_s3_client import AWSS3Client, org_id_to_hash

from .phases.clone import clone_repository, open_repository, cleanup_repository, CloneResult
from .phases.extract import extract_commits, ExtractResult
from .phases.branches import discover_branches, BranchesResult

logger = logging.getLogger(__name__)


# ============================================================================
# Branch Lifecycle Types and Functions
# ============================================================================

@dataclass
class BranchDiffResult:
    """Result of branch diff detection between runs."""
    new_branches: set[str]
    deleted_branches: set[str]


def _detect_branch_changes(
    current_branches: set[str],
    previous_branches: set[str],
) -> BranchDiffResult:
    """
    Detect branch changes between the current and previous runs.
    
    Args:
        current_branches: Set of branch names currently in the repository
        previous_branches: Set of branch names from previous run (branches.json)
        
    Returns:
        BranchDiffResult with new and deleted branch sets
    """
    return BranchDiffResult(
        new_branches=current_branches - previous_branches,
        deleted_branches=previous_branches - current_branches,
    )


def _was_merged(
    repo: pygit2.Repository | None,
    branch_last_sha: str | None,
    default_branch: str,
) -> bool:
    """
    Check if a deleted branch's commits were merged into the default branch.
    
    A branch is considered merged if its last commit is reachable from
    the default branch (i.e., it's an ancestor of the default branch HEAD).
    
    Args:
        repo: pygit2.Repository instance (or None for testing)
        branch_last_sha: SHA of the branch's last commit before deletion
        default_branch: Name of the default branch
        
    Returns:
        True if the branch was merged, False otherwise
    """
    if not repo or not branch_last_sha:
        return False

    try:
        # Get default branch reference
        default_ref = None
        if default_branch in repo.branches.local:
            default_ref = repo.branches[default_branch]
        elif f"origin/{default_branch}" in repo.branches.remote:
            default_ref = repo.branches[f"origin/{default_branch}"]

        if not default_ref:
            logger.warning(f"Default branch {default_branch} not found")
            return False

        # Get the branch's last commit
        try:
            branch_commit_oid = pygit2.Oid(hex=branch_last_sha)
        except ValueError:
            logger.warning(f"Invalid commit SHA: {branch_last_sha}")
            return False

        # Check if branch commit is an ancestor of default branch HEAD
        # This means the branch was merged (its commits are reachable from default)
        return repo.descendant_of(default_ref.target, branch_commit_oid)

    except Exception as e:
        logger.warning(f"Error checking merge status for {branch_last_sha}: {e}")
        return False


def _build_deleted_branch_entry(
    branch_name: str,
    previous_branch_data: dict,
    is_merged: bool,
) -> dict:
    """
    Build a branch entry for a deleted branch.
    
    Preserves all historical metrics from the branch's last known state,
    which allows users to see what the branch contributed before deletion.
    
    Args:
        branch_name: Name of the deleted branch
        previous_branch_data: Branch data from previous branches.json
        is_merged: Whether the branch was merged into default
        
    Returns:
        Dictionary with branch entry for the deleted branch
    """
    now = datetime.now(timezone.utc)

    return {
        "name": branch_name,
        "is_default": False,
        "is_active": False,
        "is_merged": is_merged,
        "is_deleted": True,
        "deleted_at": now,
        "merged_at": now if is_merged else None,
        "status": "merged" if is_merged else "deleted",
        # Preserve historical commit data
        "commits": previous_branch_data.get("commits", 0),
        "last_commit_date": previous_branch_data.get("last_commit_date"),
        "head_commit_sha": previous_branch_data.get("head_commit_sha", ""),
        "divergence_point_sha": previous_branch_data.get("divergence_point_sha"),
        "parent_branch": previous_branch_data.get("parent_branch"),
        "created_at": previous_branch_data.get("created_at"),
        # Preserve historical line-based metrics
        "current_lines": previous_branch_data.get("current_lines", 0),
        "unique_lines": previous_branch_data.get("unique_lines", 0),
        "total_additions_lines": previous_branch_data.get("total_additions_lines", 0),
        "total_deletions_lines": previous_branch_data.get("total_deletions_lines", 0),
        # Preserve historical byte-based SLOC metrics
        "current_sloc": previous_branch_data.get("current_sloc", 0),
        "churn_sloc": previous_branch_data.get("churn_sloc", 0),
        "unique_sloc": previous_branch_data.get("unique_sloc", 0),
        "total_addition_bytes": previous_branch_data.get("total_addition_bytes", 0),
        "total_deletion_bytes": previous_branch_data.get("total_deletion_bytes", 0),
        # Preserve historical branch stats
        "unique_commits": previous_branch_data.get("unique_commits", 0),
        "unique_contributors": previous_branch_data.get("unique_contributors", 0),
        "total_files": previous_branch_data.get("total_files", 0),
    }


class PipelineConfig(BaseModel):
    """Configuration for analytics pipeline."""
    work_dir: Path = Path("/tmp/analytics")
    cleanup_on_complete: bool = True
    default_branch_only: bool = False
    include_patches: bool = True
    incremental: bool = False  # For incremental updates on push


class PipelineInput(BaseModel):
    """Input for analytics pipeline."""
    codebase_id: str
    organization_id: str
    clone_url: str
    repo_owner: str
    repo_name: str
    auth_token: str | None = None
    incremental: bool = False  # For incremental updates on push


class PipelineOutput(BaseModel):
    """Output from analytics pipeline."""
    success: bool
    codebase_id: str
    total_commits: int = 0
    total_branches: int = 0
    total_contributors: int = 0
    json_files: list[str] = []
    error: str | None = None
    duration_seconds: float = 0.0


@dataclass
class PipelineContext:
    """Internal context for pipeline execution."""
    config: PipelineConfig
    input: PipelineInput

    # Storage
    hot_storage: HotStorage | None = None
    warm_storage: ParquetStorage | None = None
    cold_storage: ParquetStorage | None = None

    # Repository state
    repo_path: Path | None = None
    repo: pygit2.Repository | None = None

    # Results from phases
    clone_result: CloneResult | None = None
    extract_result: ExtractResult | None = None
    branches_result: BranchesResult | None = None

    # Incremental mode
    since_sha: str | None = None  # For incremental updates

    # Branch lifecycle (for incremental mode)
    deleted_branches: list[dict] = field(default_factory=list)
    previous_branches_data: dict | None = None  # Previous branches.json content

    # Timing
    start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class AnalyticsPipeline:
    """
    Main analytics pipeline orchestrator.

    Coordinates all phases and manages resources.

    Example:
        >>> config = PipelineConfig(work_dir=Path("/tmp/analytics"))
        >>> pipeline = AnalyticsPipeline(config)
        >>> result = pipeline.run(PipelineInput(
        ...     codebase_id="uuid",
        ...     organization_id="org-uuid",
        ...     clone_url="https://github.com/owner/repo",
        ...     repo_owner="owner",
        ...     repo_name="repo"
        ... ))
    """

    def __init__(self, config: PipelineConfig):
        self.config = config
        self.config.work_dir.mkdir(parents=True, exist_ok=True)

    def run(self, input: PipelineInput) -> PipelineOutput:
        """
        Execute the full analytics pipeline.

        Args:
            input: Pipeline input with repository details

        Returns:
            PipelineOutput with results
        """
        mode = "incremental" if input.incremental else "full"
        logger.info(f"Starting analytics pipeline for {input.codebase_id} (mode={mode})")

        ctx = PipelineContext(config=self.config, input=input)

        try:
            # Initialize storage
            self._init_storage(ctx)

            # For incremental mode, get checkpoint before extraction
            if input.incremental:
                bucket = org_id_to_hash(input.organization_id)
                ctx.since_sha = self._get_since_sha_from_checkpoint(bucket, input.codebase_id)
                if ctx.since_sha:
                    logger.info(f"Incremental mode: extracting commits since {ctx.since_sha[:8]}")
                else:
                    logger.info("Incremental mode: no checkpoint, will process all commits")

            # Phase 1: Clone
            self._phase_clone(ctx)

            # Phase 2: Extract commits
            self._phase_extract(ctx)

            # Check if we have any commits to process
            extracted_commits = ctx.extract_result.total_commits if ctx.extract_result else 0

            # If incremental mode extracted 0 commits, we're done (already up to date)
            if input.incremental and extracted_commits == 0:
                duration = (datetime.now(timezone.utc) - ctx.start_time).total_seconds()
                logger.info(f"Incremental pipeline: no new commits for {input.codebase_id}")
                return PipelineOutput(
                    success=True,
                    codebase_id=input.codebase_id,
                    total_commits=0,
                    total_branches=0,
                    total_contributors=0,
                    json_files=[],
                    duration_seconds=duration
                )

            # Phase 3: Discover branches
            self._phase_branches(ctx)

            # Phase 3b: Branch lifecycle detection (incremental mode only)
            self._phase_branch_diff(ctx)

            # Phase 4: Store in warm/cold storage
            self._phase_store(ctx)

            # Phase 5: Build aggregates
            self._phase_aggregate(ctx)

            # Phase 6: Export to JSON
            json_files = self._phase_export(ctx)

            # Phase 7: Upload to S3
            self._phase_upload(ctx, json_files)

            # Phase 8: Update org-level files
            self._phase_update_org_files(ctx)

            # Calculate duration
            duration = (datetime.now(timezone.utc) - ctx.start_time).total_seconds()

            logger.info(f"Pipeline completed successfully for {input.codebase_id}")

            return PipelineOutput(
                success=True,
                codebase_id=input.codebase_id,
                total_commits=extracted_commits,
                total_branches=len(ctx.branches_result.branches) if ctx.branches_result else 0,
                total_contributors=self._count_contributors(ctx),
                json_files=[str(f) for f in json_files],
                duration_seconds=duration
            )

        except Exception as e:
            logger.error(f"Pipeline failed for {input.codebase_id}: {e}")
            duration = (datetime.now(timezone.utc) - ctx.start_time).total_seconds()

            return PipelineOutput(
                success=False,
                codebase_id=input.codebase_id,
                error=str(e),
                duration_seconds=duration
            )

        finally:
            # Cleanup
            self._cleanup(ctx)

    def _init_storage(self, ctx: PipelineContext) -> None:
        """Initialize storage backends."""
        logger.info("Initializing storage...")

        storage_path = ctx.config.work_dir / ctx.input.codebase_id

        # Hot storage (DuckDB)
        hot_path = storage_path / "hot" / "analytics.duckdb"
        ctx.hot_storage = HotStorage(hot_path)
        ctx.hot_storage.connect()

        # Warm storage (Parquet)
        warm_path = storage_path / "warm"
        ctx.warm_storage = ParquetStorage(warm_path)

        # Cold storage (Parquet)
        cold_path = storage_path / "cold"
        ctx.cold_storage = ParquetStorage(cold_path)

        logger.info("Storage initialized")

    def _phase_clone(self, ctx: PipelineContext) -> None:
        """Phase 1: Clone repository."""
        logger.info("Phase 1: Cloning repository...")

        repo_path = ctx.config.work_dir / ctx.input.codebase_id / "repo"

        result = clone_repository(
            clone_url=ctx.input.clone_url,
            target_path=repo_path,
            auth_token=ctx.input.auth_token,
            clean_existing=True
        )

        if not result.success:
            raise RuntimeError(f"Clone failed: {result.error}")

        ctx.clone_result = result
        ctx.repo_path = result.repo_path
        ctx.repo = result.repo

        logger.info(f"Clone complete: {ctx.repo_path}")

    def _phase_extract(self, ctx: PipelineContext) -> None:
        """Phase 2: Extract commits."""
        logger.info("Phase 2: Extracting commits...")

        if not ctx.repo:
            raise RuntimeError("No repository available for extraction")

        # Determine branches to extract
        branch_names = None  # All branches
        if ctx.config.default_branch_only:
            # Just extract default branch
            branch_names = [ctx.repo.head.shorthand] if not ctx.repo.head_is_unborn else ["main"]

        result = extract_commits(
            repo=ctx.repo,
            codebase_id=ctx.input.codebase_id,
            branch_names=branch_names,
            include_patches=ctx.config.include_patches,
            since_sha=ctx.since_sha,  # For incremental updates
            include_file_changes=True,  # Always extract file-level changes
        )

        if not result.success:
            raise RuntimeError(f"Extract failed: {result.error}")
        
        # Store file changes in cold storage if available
        if result.file_changes and ctx.cold_storage:
            ctx.cold_storage.write_file_changes(
                codebase_id=ctx.input.codebase_id,
                file_changes=result.file_changes,
                partition_by_date=True,
            )
            logger.info(f"Stored {len(result.file_changes)} file changes in cold storage")

        ctx.extract_result = result

        mode_info = f" (since {ctx.since_sha[:8]})" if ctx.since_sha else ""
        logger.info(f"Extracted {result.total_commits} unique commits ({len(result.commits)} records){mode_info}")

    def _phase_branches(self, ctx: PipelineContext) -> None:
        """Phase 3: Discover branches."""
        logger.info("Phase 3: Discovering branches...")

        if not ctx.repo:
            raise RuntimeError("No repository available for branch discovery")

        result = discover_branches(
            repo=ctx.repo,
            default_branch_only=ctx.config.default_branch_only
        )

        if not result.success:
            raise RuntimeError(f"Branch discovery failed: {result.error}")

        ctx.branches_result = result

        logger.info(f"Discovered {len(result.branches)} branches (default: {result.default_branch})")

    def _phase_store(self, ctx: PipelineContext) -> None:
        """Phase 4: Store data in warm/cold storage."""
        logger.info("Phase 4: Storing data...")

        if not ctx.extract_result or not ctx.warm_storage:
            return

        # Store commits in warm storage
        commits = ctx.extract_result.commits
        if commits:
            if ctx.input.incremental and ctx.since_sha:
                # Incremental mode: append to existing
                ctx.warm_storage.append_commits(ctx.input.codebase_id, commits)
                logger.info(f"Appended {len(commits)} new commit records to warm storage")
            else:
                # Full mode: overwrite
                ctx.warm_storage.write_commits(ctx.input.codebase_id, commits)
                logger.info(f"Stored {len(commits)} commit records in warm storage")

        # TODO: Store file changes in cold storage

        logger.info("Data storage complete")

    def _phase_aggregate(self, ctx: PipelineContext) -> None:
        """Phase 5: Build aggregates."""
        logger.info("Phase 5: Building aggregates...")

        if not ctx.hot_storage or not ctx.warm_storage:
            return

        engine = AggregationEngine(ctx.hot_storage, ctx.warm_storage, ctx.cold_storage)

        # Get default branch from branch discovery
        default_branch = None
        if ctx.branches_result and ctx.branches_result.default_branch:
            default_branch = ctx.branches_result.default_branch
        
        # Build all aggregates with repository metadata
        engine.build_all_aggregates(
            ctx.input.codebase_id,
            force_rebuild=True,
            repo_owner=ctx.input.repo_owner,
            repo_name=ctx.input.repo_name,
            default_branch=default_branch
        )

        # Refresh branch metrics
        engine.refresh_branch_metrics(ctx.input.codebase_id)

        logger.info("Aggregates built")

    def _phase_export(self, ctx: PipelineContext) -> list[Path]:
        """Phase 6: Export to JSON."""
        logger.info("Phase 6: Exporting to JSON...")

        if not ctx.hot_storage:
            return []

        output_dir = ctx.config.work_dir / ctx.input.codebase_id / "json"

        exporter = DriverJSONExporter(
            codebase_id=ctx.input.codebase_id,
            hot_storage=ctx.hot_storage,
            warm_storage=ctx.warm_storage,
            cold_storage=ctx.cold_storage,
            output_dir=output_dir,
            deleted_branches=ctx.deleted_branches,  # Pass deleted branches for lifecycle tracking
        )

        # Get checkpoint data from extraction results
        last_commit_sha, last_commit_date, total_commits = self._get_checkpoint_data(ctx)

        json_files = exporter.export_all(
            last_commit_sha=last_commit_sha,
            last_commit_date=last_commit_date,
            total_commits=total_commits,
        )

        logger.info(f"Exported {len(json_files)} JSON files to {output_dir}")
        return json_files

    def _phase_upload(self, ctx: PipelineContext, json_files: list[Path]) -> None:
        """Phase 7: Upload JSON files to S3."""
        logger.info("Phase 7: Uploading to S3...")

        if not json_files:
            logger.warning("No JSON files to upload")
            return

        # Get the S3 bucket for this organization
        bucket = org_id_to_hash(ctx.input.organization_id)
        s3_client = AWSS3Client()

        uploaded = 0
        for json_file in json_files:
            if not json_file.exists():
                logger.warning(f"JSON file not found: {json_file}")
                continue

            # Upload key: analytics/{codebase_id}/{filename}
            upload_key = f"analytics/{ctx.input.codebase_id}/{json_file.name}"

            try:
                s3_client.upload_file_to_s3(
                    file_path=json_file,
                    bucket=bucket,
                    upload_key=upload_key,
                    metadata={"codebase_id": ctx.input.codebase_id},
                    content_type="application/json"
                )
                uploaded += 1
                logger.info(f"Uploaded {json_file.name} to s3://{bucket}/{upload_key}")
            except Exception as e:
                logger.error(f"Failed to upload {json_file.name}: {e}")
                raise RuntimeError(f"S3 upload failed for {json_file.name}: {e}")

        logger.info(f"Uploaded {uploaded}/{len(json_files)} JSON files to S3")

    def _phase_update_org_files(self, ctx: PipelineContext) -> None:
        """Phase 8: Update organization-level summary files."""
        logger.info("Phase 8: Updating org-level files...")

        import json
        import tempfile

        bucket = org_id_to_hash(ctx.input.organization_id)
        s3_client = AWSS3Client()

        # Get current codebase metrics from hot storage
        metrics = ctx.hot_storage.get_repository_metrics(ctx.input.codebase_id)
        if not metrics:
            logger.warning("No metrics found for codebase, skipping org file update")
            return

        # Build codebase entry for the list
        # Note: Field names match D2 schema cleanup (additions_sloc, deletions_sloc, etc.)
        additions_sloc = metrics.get('additions_sloc', 0)
        deletions_sloc = metrics.get('deletions_sloc', 0)
        net_sloc = additions_sloc - deletions_sloc
        # current_sloc comes from tree walk (actual codebase size), fall back to net_sloc
        current_sloc = metrics.get('current_sloc', net_sloc)

        new_codebase_entry = {
            "codebase_id": ctx.input.codebase_id,
            "display_name": metrics.get('full_name', f"{ctx.input.repo_owner}/{ctx.input.repo_name}"),
            "full_name": metrics.get('full_name', f"{ctx.input.repo_owner}/{ctx.input.repo_name}"),
            "owner": ctx.input.repo_owner,
            "repository_name": ctx.input.repo_name,
            "total_commits": metrics.get('total_commits', 0),
            "total_contributors": metrics.get('total_contributors', 0),
            "total_branches": metrics.get('total_branches', 0),
            "churn_lines": metrics.get('churn_lines', 0),  # Use new field name
            "current_sloc": current_sloc,  # From tree walk (actual codebase size)
            "net_sloc": net_sloc,  # From patches (additions - deletions)
            "primary_language": metrics.get('primary_language'),
            "last_commit_date": metrics.get('last_commit_at').isoformat() if metrics.get('last_commit_at') else None,
            "has_analytics": True,
            "analytics_status": "complete",  # Required by API schema
        }

        organization_id = ctx.input.organization_id

        # Update codebases_list.json
        try:
            self._update_codebases_list(s3_client, bucket, organization_id, new_codebase_entry)
            logger.info("Updated codebases_list.json")
        except Exception as e:
            logger.error(f"Failed to update codebases_list.json: {e}")

        # Update org_summary.json
        try:
            self._update_org_summary(s3_client, bucket, organization_id)
            logger.info("Updated org_summary.json")
        except Exception as e:
            logger.error(f"Failed to update org_summary.json: {e}")

    def _update_codebases_list(
        self, s3_client: AWSS3Client, bucket: str, organization_id: str, new_entry: dict
    ) -> None:
        """Update codebases_list.json with new codebase entry.
        
        Schema must match what AnalyticsService expects:
        {
            "organization_id": "org-id",
            "codebases": [{ ... }],
            "generated_at": "ISO timestamp"
        }
        """
        import json
        import tempfile
        import boto3
        from datetime import datetime, timezone

        key = "analytics/codebases_list.json"
        codebases = []

        # Try to download existing file
        try:
            s3 = boto3.client("s3")
            response = s3.get_object(Bucket=bucket, Key=key)
            existing_data = json.loads(response['Body'].read().decode('utf-8'))
            codebases = existing_data.get('codebases', [])
        except Exception as e:
            logger.info(f"No existing codebases_list.json, creating new: {e}")

        # Update or add entry
        updated = False
        for i, cb in enumerate(codebases):
            if cb.get('codebase_id') == new_entry['codebase_id']:
                codebases[i] = new_entry
                updated = True
                break

        if not updated:
            codebases.append(new_entry)

        # Write updated file with correct schema
        data = {
            "organization_id": organization_id,
            "codebases": codebases,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f, indent=2, default=str)
            temp_path = Path(f.name)

        s3_client.upload_file_to_s3(
            file_path=temp_path,
            bucket=bucket,
            upload_key=key,
            metadata=None,
            content_type="application/json"
        )

        temp_path.unlink()

    def _update_org_summary(self, s3_client: AWSS3Client, bucket: str, organization_id: str) -> None:
        """Update org_summary.json with aggregated totals.
        
        Schema must match what AnalyticsService expects:
        {
            "organization_id": "org-id",
            "total_codebases": N,
            "codebases_with_analytics": N,
            "total_commits": N,
            "total_contributors": N,
            "total_sloc": N,
            "generated_at": "ISO timestamp"
        }
        """
        import json
        import tempfile
        import boto3
        from datetime import datetime, timezone

        key = "analytics/org_summary.json"

        # First get the current codebases list to compute totals
        codebases = []
        try:
            s3 = boto3.client("s3")
            response = s3.get_object(Bucket=bucket, Key="analytics/codebases_list.json")
            existing_data = json.loads(response['Body'].read().decode('utf-8'))
            codebases = existing_data.get('codebases', [])
        except Exception as e:
            logger.info(f"Could not read codebases_list.json for summary: {e}")
            return  # Can't compute summary without codebases list

        # Aggregate totals
        total_codebases = len(codebases)
        total_commits = sum(cb.get('total_commits', 0) for cb in codebases)
        total_contributors = sum(cb.get('total_contributors', 0) for cb in codebases)
        total_sloc = sum(cb.get('current_sloc', 0) for cb in codebases)

        # Build summary with correct schema (matching AnalyticsService expectations)
        summary = {
            "organization_id": organization_id,
            "total_codebases": total_codebases,
            "codebases_with_analytics": total_codebases,
            "total_commits": total_commits,
            "total_contributors": total_contributors,
            "total_sloc": total_sloc,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(summary, f, indent=2)
            temp_path = Path(f.name)

        s3_client.upload_file_to_s3(
            file_path=temp_path,
            bucket=bucket,
            upload_key=key,
            metadata=None,
            content_type="application/json"
        )

        temp_path.unlink()
        logger.info(f"Org summary updated: {total_codebases} codebases, {total_commits} commits")

    def _download_branches_json(self, bucket: str, codebase_id: str) -> dict | None:
        """Download existing branches.json from S3 for branch lifecycle tracking.
        
        Args:
            bucket: S3 bucket name
            codebase_id: Codebase UUID
            
        Returns:
            Branches data dict or None if not found
        """
        import boto3
        from botocore.exceptions import ClientError

        s3 = boto3.client('s3')
        key = f"analytics/{codebase_id}/branches.json"

        try:
            response = s3.get_object(Bucket=bucket, Key=key)
            data = json.loads(response['Body'].read().decode('utf-8'))
            logger.info(f"Downloaded previous branches.json: {len(data.get('branches', []))} branches")
            return data
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code in ('NoSuchKey', '404'):
                logger.info(f"No previous branches.json found for {codebase_id}")
            else:
                logger.warning(f"Error downloading branches.json: {e}")
            return None
        except Exception as e:
            logger.warning(f"Unexpected error downloading branches.json: {e}")
            return None

    def _phase_branch_diff(self, ctx: PipelineContext) -> None:
        """Detect branch changes since last run (incremental mode only).
        
        Compares current branches from the repo with previous branches.json
        to detect new, deleted, and merged branches.
        
        Args:
            ctx: Pipeline context
        """
        if not ctx.input.incremental:
            logger.debug("Branch diff skipped: not in incremental mode")
            return

        if not ctx.branches_result:
            logger.warning("Branch diff skipped: no branches result")
            return

        # Download previous branches.json
        bucket = org_id_to_hash(ctx.input.organization_id)
        previous_data = self._download_branches_json(bucket, ctx.input.codebase_id)

        if not previous_data:
            logger.info("No previous branches data, skipping branch diff")
            return

        ctx.previous_branches_data = previous_data

        # Get current and previous branch names
        current_names = {b.name for b in ctx.branches_result.branches}
        previous_branches = previous_data.get("branches", [])
        
        # Carry forward previously deleted branches (so they stay deleted)
        # Only carry forward if they haven't reappeared in the repo
        for prev_branch in previous_branches:
            branch_name = prev_branch.get("name")
            if prev_branch.get("is_deleted", False) and branch_name not in current_names:
                # Branch was deleted before and hasn't reappeared - keep it deleted
                ctx.deleted_branches.append(prev_branch)
                logger.debug(f"Carrying forward deleted branch: {branch_name}")
        
        # Only consider previously ACTIVE branches when detecting NEW deletions
        # (branches already marked is_deleted=True should not be re-detected)
        previous_active_names = {
            b.get("name") for b in previous_branches 
            if b.get("name") and not b.get("is_deleted", False)
        }

        # Detect changes
        diff = _detect_branch_changes(current_names, previous_active_names)

        logger.info(f"Branch diff: {len(diff.new_branches)} new, {len(diff.deleted_branches)} deleted")

        # Process newly deleted branches
        for branch_name in diff.deleted_branches:
            # Find the previous branch data
            prev_branch = next(
                (b for b in previous_branches if b.get("name") == branch_name),
                None
            )

            if not prev_branch:
                logger.warning(f"Could not find previous data for deleted branch: {branch_name}")
                continue

            # Check if the branch was merged into default
            default_branch = ctx.branches_result.default_branch or "main"
            is_merged = _was_merged(
                ctx.repo,
                prev_branch.get("head_commit_sha"),
                default_branch,
            )

            # Build the deleted branch entry
            deleted_entry = _build_deleted_branch_entry(
                branch_name=branch_name,
                previous_branch_data=prev_branch,
                is_merged=is_merged,
            )

            ctx.deleted_branches.append(deleted_entry)
            status = "merged" if is_merged else "deleted"
            logger.info(f"Branch {branch_name} marked as {status}")

    def _download_checkpoint(self, bucket: str, codebase_id: str) -> dict | None:
        """Download existing metadata.json from S3 for checkpoint.
        
        Args:
            bucket: S3 bucket name
            codebase_id: Codebase UUID
            
        Returns:
            Checkpoint data dict or None if not found
        """
        import boto3
        import json
        from botocore.exceptions import ClientError

        s3 = boto3.client('s3')
        key = f"analytics/{codebase_id}/metadata.json"

        try:
            response = s3.get_object(Bucket=bucket, Key=key)
            data = json.loads(response['Body'].read().decode('utf-8'))
            logger.info(f"Downloaded checkpoint: {data.get('last_processed_commit_sha', 'none')[:8] if data.get('last_processed_commit_sha') else 'none'}")
            return data
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code in ('NoSuchKey', '404'):
                logger.info(f"No checkpoint found for {codebase_id}")
            else:
                logger.warning(f"Error downloading checkpoint: {e}")
            return None
        except Exception as e:
            logger.warning(f"Unexpected error downloading checkpoint: {e}")
            return None

    def _get_since_sha_from_checkpoint(self, bucket: str, codebase_id: str) -> str | None:
        """Get the since_sha from checkpoint for incremental extraction.
        
        Args:
            bucket: S3 bucket name
            codebase_id: Codebase UUID
            
        Returns:
            Last processed commit SHA or None
        """
        checkpoint = self._download_checkpoint(bucket, codebase_id)
        if checkpoint:
            return checkpoint.get('last_processed_commit_sha')
        return None

    def _get_checkpoint_data(self, ctx: PipelineContext) -> tuple[str | None, datetime | None, int]:
        """Get checkpoint data from extraction results.
        
        Args:
            ctx: Pipeline context
            
        Returns:
            Tuple of (latest_sha, latest_date, total_commits)
        """
        if not ctx.extract_result or not ctx.extract_result.commits:
            return None, None, 0

        # Find the latest commit by date
        commits = ctx.extract_result.commits
        latest_commit = max(commits, key=lambda c: c.get('committed_at', datetime.min))
        
        latest_sha = latest_commit.get('commit_sha')
        latest_date = latest_commit.get('committed_at')
        
        # Get total commits from repository metrics (includes previous + new)
        total_commits = 0
        if ctx.hot_storage:
            metrics = ctx.hot_storage.get_repository_metrics(ctx.input.codebase_id)
            if metrics:
                total_commits = metrics.get('total_commits', 0)
        
        # Fallback to extracted count if metrics not available
        if total_commits == 0:
            total_commits = ctx.extract_result.total_commits

        return latest_sha, latest_date, total_commits

    def _count_contributors(self, ctx: PipelineContext) -> int:
        """Count unique contributors from extracted commits."""
        if not ctx.extract_result:
            return 0

        emails = set()
        for commit in ctx.extract_result.commits:
            if commit.get('author_email'):
                emails.add(commit['author_email'])

        return len(emails)

    def _cleanup(self, ctx: PipelineContext) -> None:
        """Cleanup resources."""
        logger.info("Cleaning up...")

        # Close storage connections
        if ctx.hot_storage:
            try:
                ctx.hot_storage.close()
            except Exception as e:
                logger.warning(f"Error closing hot storage: {e}")

        # Remove cloned repository if configured
        if ctx.config.cleanup_on_complete and ctx.repo_path:
            cleanup_repository(ctx.repo_path)

        logger.info("Cleanup complete")


# Convenience function for simple usage
def run_pipeline(
    codebase_id: str,
    clone_url: str,
    repo_owner: str,
    repo_name: str,
    organization_id: str = "default",
    work_dir: Path | None = None,
    auth_token: str | None = None
) -> PipelineOutput:
    """
    Run analytics pipeline with default configuration.

    Args:
        codebase_id: Codebase UUID
        clone_url: Git clone URL
        repo_owner: Repository owner
        repo_name: Repository name
        organization_id: Organization UUID
        work_dir: Working directory (default: /tmp/analytics)
        auth_token: Optional auth token for private repos

    Returns:
        PipelineOutput with results
    """
    config = PipelineConfig(
        work_dir=work_dir or Path("/tmp/analytics")
    )

    pipeline = AnalyticsPipeline(config)

    return pipeline.run(PipelineInput(
        codebase_id=codebase_id,
        organization_id=organization_id,
        clone_url=clone_url,
        repo_owner=repo_owner,
        repo_name=repo_name,
        auth_token=auth_token
    ))

