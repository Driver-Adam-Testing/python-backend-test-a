"""
Aggregation engine for pre-computing analytics in hot storage.

This module provides efficient aggregation of commit data from warm storage (Parquet)
into pre-computed metrics in hot storage (DuckDB) for sub-10ms query performance.
"""

import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
import pandas as pd

from analytics.storage.hot_storage import HotStorage
from analytics.storage.parquet_storage import ParquetStorage
from analytics.aggregation.language import detect_primary_language

logger = logging.getLogger(__name__)


class AggregationEngine:
    """
    Build and maintain pre-computed aggregates in hot storage.

    The aggregation engine reads raw commit data from warm storage (Parquet)
    and builds pre-computed aggregates in hot storage (DuckDB) for fast queries.

    Example:
        >>> hot = HotStorage(Path('/data/hot/analytics.duckdb'))
        >>> warm = ParquetStorage(Path('/data/warm'))
        >>> engine = AggregationEngine(hot, warm)
        >>> engine.build_all_aggregates(codebase_id='uuid-here')
    """

    def __init__(self, hot_storage: HotStorage, warm_storage: ParquetStorage, cold_storage: ParquetStorage = None):
        """Initialize aggregation engine.

        Args:
            hot_storage: HotStorage instance (DuckDB)
            warm_storage: ParquetStorage instance (Parquet warm layer)
            cold_storage: ParquetStorage instance (Parquet cold layer, optional)
        """
        self.hot = hot_storage
        self.warm = warm_storage
        self.cold = cold_storage if cold_storage else warm_storage
        logger.info("Initialized AggregationEngine")

    def build_all_aggregates(
        self,
        codebase_id: str,
        force_rebuild: bool = False,
        repo_owner: str | None = None,
        repo_name: str | None = None
    ) -> dict:
        """
        Build all aggregates for a repository.

        Args:
            codebase_id: Repository identifier
            force_rebuild: Force full rebuild even if aggregates exist
            repo_owner: Repository owner (e.g., 'lodash')
            repo_name: Repository name (e.g., 'lodash')

        Returns:
            Dictionary with aggregation statistics

        Raises:
            ValueError: If no commit data found for repository
        """
        logger.info(f"Building all aggregates for repo {codebase_id} (force_rebuild={force_rebuild})")
        
        # Store repo metadata for use in aggregates
        self._repo_owner = repo_owner
        self._repo_name = repo_name

        # Check if aggregates exist
        if not force_rebuild and self._aggregates_exist(codebase_id):
            logger.warning(f"Aggregates exist for repo {codebase_id}, use force_rebuild=True")
            return {
                'status': 'skipped',
                'reason': 'aggregates_exist',
                'codebase_id': codebase_id
            }

        # Load raw data from warm storage
        commits_df = self._load_commits(codebase_id)

        if commits_df.empty:
            logger.warning(f"No commits found for repo {codebase_id}")
            raise ValueError(f"No commit data found for repository {codebase_id}")

        logger.info(f"Loaded {len(commits_df)} commits for aggregation")

        # Build each aggregate type
        stats = {
            'codebase_id': codebase_id,
            'commits_processed': len(commits_df),
            'aggregates_built': []
        }

        try:
            self._build_repository_aggregate(codebase_id, commits_df)
            stats['aggregates_built'].append('repository')

            self._build_daily_aggregates(codebase_id, commits_df)
            stats['aggregates_built'].append('daily')

            self._build_monthly_aggregates(codebase_id, commits_df)
            stats['aggregates_built'].append('monthly')
            
            # Build contributor aggregates (A8)
            self._build_contributor_aggregates(codebase_id, commits_df)
            stats['aggregates_built'].append('contributors')

            stats['status'] = 'success'
            stats['timestamp'] = datetime.now().isoformat()

            logger.info(f"Successfully built all aggregates for repo {codebase_id}")
            return stats

        except Exception as e:
            logger.error(f"Failed to build aggregates for repo {codebase_id}: {e}")
            stats['status'] = 'error'
            stats['error'] = str(e)
            raise

    def refresh_branch_metrics(self, codebase_id: str, branch_name: str = None) -> dict:
        """
        Refresh branch metrics from warm data.

        Args:
            codebase_id: Repository identifier
            branch_name: Specific branch to refresh (None = all branches)

        Returns:
            Dictionary with refresh statistics
        """
        logger.info(f"Refreshing branch metrics for repo {codebase_id} (branch={branch_name})")

        filters = None
        if branch_name:
            filters = [('branch_name', '=', branch_name)]

        # Load branch commits
        commits_df = self._load_commits(codebase_id, filters=filters)

        if commits_df.empty:
            logger.warning(f"No commits found for branch refresh (repo={codebase_id}, branch={branch_name})")
            return {
                'status': 'skipped',
                'reason': 'no_commits',
                'codebase_id': codebase_id,
                'branch_name': branch_name
            }

        stats = {
            'codebase_id': codebase_id,
            'branch_name': branch_name,
            'commits_processed': len(commits_df),
            'branches_updated': []
        }

        try:
            # Get default branch from repository metrics (if available)
            repo_metrics = self.hot.get_repository_metrics(codebase_id)
            default_branch = repo_metrics.get('default_branch', 'main') if repo_metrics else 'main'
            
            # Load all commits to find divergence points
            all_commits_df = self._load_commits(codebase_id)
            
            # Get default branch commits with their tree metrics for divergence calculation
            default_branch_commits = {}
            if default_branch in all_commits_df['branch_name'].values:
                default_df = all_commits_df[all_commits_df['branch_name'] == default_branch]
                for _, row in default_df.iterrows():
                    default_branch_commits[row['commit_sha']] = {
                        'tree_sloc': row.get('tree_sloc', 0),
                        'tree_lines': row.get('tree_lines', 0),
                        'committed_at': row['committed_at']
                    }
            
            # Group by branch and calculate metrics
            for branch, branch_df in commits_df.groupby('branch_name'):
                branch_metrics = self._calculate_branch_metrics(
                    codebase_id, branch, branch_df, default_branch, default_branch_commits
                )
                self.hot.upsert_branch_metrics(branch_metrics)
                stats['branches_updated'].append(branch)

            stats['status'] = 'success'
            stats['timestamp'] = datetime.now().isoformat()

            logger.info(f"Refreshed {len(stats['branches_updated'])} branches for repo {codebase_id}")
            return stats

        except Exception as e:
            logger.error(f"Failed to refresh branch metrics: {e}")
            stats['status'] = 'error'
            stats['error'] = str(e)
            raise

    def _load_commits(self, codebase_id: str, filters: list[tuple] = None) -> pd.DataFrame:
        """Load commits from warm storage.

        Args:
            codebase_id: Repository ID
            filters: Optional PyArrow filters

        Returns:
            DataFrame of commits
        """
        logger.debug(f"Loading commits from warm storage for repo {codebase_id}")

        # Select columns needed for aggregation
        columns = [
            'commit_sha',
            'committed_at',
            'branch_name',
            'additions_lines',
            'deletions_lines',
            'net_lines',
            'churn_lines',
            'addition_bytes',
            'deletion_bytes',
            'patch_bytes',
            'net_bytes',
            'sloc',
            'bytes_per_line',
            'author_email',
            'files_changed',
            # Tree-based metrics (actual codebase size)
            'tree_bytes',
            'tree_lines',
            'tree_sloc',
        ]

        commits_df = self.warm.read_commits(codebase_id, columns=columns, filters=filters)

        if not commits_df.empty:
            # Ensure datetime type
            commits_df['committed_at'] = pd.to_datetime(commits_df['committed_at'])
            logger.info(f"Loaded {len(commits_df)} commits from warm storage")
        else:
            logger.warning(f"No commits found in warm storage for repo {codebase_id}")

        return commits_df

    def _build_repository_aggregate(self, codebase_id: str, commits_df: pd.DataFrame) -> None:
        """Build repository-level aggregate.
        
        All metrics use clean naming convention:
        - current_* : Current codebase state from tree walk at HEAD
        - *_lines   : Line-based metrics
        - *_sloc    : SLOC metrics (already converted from bytes / 50)
        - net_*     : additions - deletions
        - churn_*   : additions + deletions
        """
        logger.debug(f"Building repository aggregate for repo {codebase_id}")

        # Deduplicate commits by SHA (same commit may appear on multiple branches)
        unique_commits = commits_df.drop_duplicates(subset=['commit_sha'])

        # Calculate metrics
        total_commits = len(unique_commits)

        # Line-based metrics (cumulative)
        additions_lines = unique_commits['additions_lines'].sum()
        deletions_lines = unique_commits['deletions_lines'].sum()
        churn_lines = additions_lines + deletions_lines
        net_lines = unique_commits['net_lines'].sum()

        # Byte metrics (for SLOC conversion)
        addition_bytes = unique_commits['addition_bytes'].sum()
        deletion_bytes = unique_commits['deletion_bytes'].sum()
        
        # SLOC-based metrics (convert bytes to SLOC: bytes / 50)
        additions_sloc = int(addition_bytes) // 50
        deletions_sloc = int(deletion_bytes) // 50
        churn_sloc = additions_sloc + deletions_sloc
        net_sloc = additions_sloc - deletions_sloc

        # Tree-based SLOC (actual codebase size from latest commit's tree walk)
        # This is the REAL current size of the codebase
        latest_commit = unique_commits.loc[unique_commits['committed_at'].idxmax()]
        current_sloc = int(latest_commit.get('tree_sloc', 0)) if 'tree_sloc' in unique_commits.columns else 0
        current_lines = int(latest_commit.get('tree_lines', 0)) if 'tree_lines' in unique_commits.columns else 0

        # Average bytes per line
        avg_bytes_per_line = (
            addition_bytes / additions_lines
            if additions_lines > 0 else 0.0
        )

        # Unique counts
        total_contributors = unique_commits['author_email'].nunique()
        branch_count = commits_df['branch_name'].nunique()

        # Date range
        first_commit_at = unique_commits['committed_at'].min()
        last_commit_at = unique_commits['committed_at'].max()

        # Total files (approximate - count unique file changes)
        total_files = unique_commits['files_changed'].sum()

        # Default branch (most common branch)
        default_branch = commits_df['branch_name'].mode()[0] if not commits_df.empty else 'main'

        # Determine repository name from stored metadata or use fallback
        repo_name = getattr(self, '_repo_name', None) or f'repo_{codebase_id[:8]}'
        repo_owner = getattr(self, '_repo_owner', None) or 'owner'
        full_name = f'{repo_owner}/{repo_name}'

        # Detect primary language from file changes in cold storage
        primary_language = None
        try:
            file_changes_df = self.cold.read_file_changes(codebase_id)
            if file_changes_df is not None and not file_changes_df.empty:
                file_changes = file_changes_df.to_dict('records')
                primary_language = detect_primary_language(file_changes)
                logger.debug(f"Detected primary language: {primary_language}")
        except Exception as e:
            logger.warning(f"Failed to detect primary language: {e}")

        # Store aggregate with clean naming (convert numpy types to Python types)
        metrics = {
            'codebase_id': codebase_id,
            'repository_name': repo_name,
            'full_name': full_name,
            'owner': repo_owner,
            # Current codebase state (from tree walk)
            'current_sloc': int(current_sloc),
            'current_lines': int(current_lines),
            # Line-based cumulative activity
            'additions_lines': int(additions_lines),
            'deletions_lines': int(deletions_lines),
            'churn_lines': int(churn_lines),
            'net_lines': int(net_lines),
            # SLOC-based cumulative activity
            'additions_sloc': int(additions_sloc),
            'deletions_sloc': int(deletions_sloc),
            'churn_sloc': int(churn_sloc),
            'net_sloc': int(net_sloc),
            # Other metrics
            'avg_bytes_per_line': float(avg_bytes_per_line),
            'total_commits': int(total_commits),
            'total_contributors': int(total_contributors),
            'total_branches': int(branch_count),
            'total_files': int(total_files),
            'default_branch': str(default_branch),
            'primary_language': primary_language,
            'first_commit_at': first_commit_at.to_pydatetime() if hasattr(first_commit_at, 'to_pydatetime') else first_commit_at,
            'last_commit_at': last_commit_at.to_pydatetime() if hasattr(last_commit_at, 'to_pydatetime') else last_commit_at,
            'collected_at': datetime.now(),
            'last_updated_at': datetime.now(),
            'collection_version': '3.0'
        }

        self.hot.upsert_repository_metrics(metrics)
        logger.info(f"Built repository aggregate: {total_commits} commits, {total_contributors} contributors")

    def _build_daily_aggregates(self, codebase_id: str, commits_df: pd.DataFrame) -> None:
        """Build daily time-series aggregates."""
        logger.debug(f"Building daily aggregates for repo {codebase_id}")

        # Deduplicate commits by SHA
        unique_commits = commits_df.drop_duplicates(subset=['commit_sha'])

        # Group by date
        unique_commits['date'] = unique_commits['committed_at'].dt.date

        daily_df = unique_commits.groupby('date').agg({
            'commit_sha': 'count',
            'additions_lines': 'sum',
            'deletions_lines': 'sum',
            'net_lines': 'sum',
            'churn_lines': 'sum',
            'addition_bytes': 'sum',
            'deletion_bytes': 'sum',
            'net_bytes': 'sum',
            'patch_bytes': 'sum',
            'sloc': 'sum',
            'author_email': 'nunique',
            'files_changed': 'sum'
        }).reset_index()

        daily_df.columns = [
            'date',
            'commits_count',
            'additions_lines',
            'deletions_lines',
            'net_change_lines',
            'churn_lines',
            'addition_bytes',
            'deletion_bytes',
            'net_bytes',
            'patch_bytes',
            'sloc',
            'active_contributors',
            'files_changed'
        ]

        # Calculate cumulative totals
        daily_df = daily_df.sort_values('date')
        daily_df['cumulative_lines'] = daily_df['net_change_lines'].cumsum()
        daily_df['cumulative_sloc'] = daily_df['sloc'].cumsum()

        # Convert to list of dicts
        daily_metrics = daily_df.to_dict('records')

        # Bulk insert
        self.hot.insert_daily_metrics(codebase_id, daily_metrics)
        logger.info(f"Built {len(daily_metrics)} daily aggregates")

    def _build_monthly_aggregates(self, codebase_id: str, commits_df: pd.DataFrame) -> None:
        """Build monthly rollup aggregates."""
        logger.debug(f"Building monthly aggregates for repo {codebase_id}")

        # Deduplicate commits by SHA
        unique_commits = commits_df.drop_duplicates(subset=['commit_sha'])

        # Group by month
        unique_commits['year_month'] = unique_commits['committed_at'].dt.strftime('%Y-%m')

        monthly_df = unique_commits.groupby('year_month').agg({
            'commit_sha': 'count',
            'additions_lines': ['sum', 'max', 'mean'],
            'deletions_lines': 'sum',
            'net_lines': 'sum',
            'addition_bytes': 'sum',
            'deletion_bytes': 'sum',
            'net_bytes': 'sum',
            'sloc': ['sum', 'max', 'mean'],
            'author_email': 'nunique'
        }).reset_index()

        # Flatten multi-level columns
        monthly_df.columns = [
            'year_month',
            'commits_count',
            'additions_lines',
            'max_commit_size_lines',
            'avg_commit_size_lines',
            'deletions_lines',
            'net_lines',
            'addition_bytes',
            'deletion_bytes',
            'net_sloc',
            'sloc_sum',
            'max_commit_size_sloc',
            'avg_commit_size_sloc',
            'unique_contributors'
        ]

        # Drop the extra sloc_sum column (we use net_sloc)
        monthly_df = monthly_df.drop(columns=['sloc_sum'])

        # Convert to list of dicts
        monthly_metrics = monthly_df.to_dict('records')

        # Bulk insert
        self.hot.insert_monthly_metrics(codebase_id, monthly_metrics)
        logger.info(f"Built {len(monthly_metrics)} monthly aggregates")

    def _calculate_branch_metrics(
        self,
        codebase_id: str,
        branch_name: str,
        branch_df: pd.DataFrame,
        default_branch: str = 'main',
        default_branch_commits: dict = None
    ) -> dict:
        """Calculate metrics for a single branch.

        Args:
            codebase_id: Repository ID
            branch_name: Branch name
            branch_df: DataFrame of commits for this branch
            default_branch: Name of the default branch (for is_default_branch flag)
            default_branch_commits: Dict of {sha: {tree_sloc, tree_lines, committed_at}} for default branch

        Returns:
            Dictionary of branch metrics with clean naming
        """
        logger.debug(f"Calculating metrics for branch {branch_name}")

        # Get head commit
        latest_commit = branch_df.loc[branch_df['committed_at'].idxmax()]
        head_commit_sha = latest_commit['commit_sha']

        # Calculate aggregates for ALL commits on this branch
        total_commits = len(branch_df)
        unique_contributors = branch_df['author_email'].nunique()

        # Line-based metrics (all commits)
        current_lines = int(latest_commit.get('tree_lines', 0))
        additions_lines = branch_df['additions_lines'].sum()
        deletions_lines = branch_df['deletions_lines'].sum()

        # Byte metrics (for SLOC conversion)
        addition_bytes = branch_df['addition_bytes'].sum()
        deletion_bytes = branch_df['deletion_bytes'].sum()
        
        # SLOC-based metrics (convert bytes to SLOC: bytes / 50)
        additions_sloc = int(addition_bytes) // 50
        deletions_sloc = int(deletion_bytes) // 50
        churn_sloc = additions_sloc + deletions_sloc
        
        # Current SLOC = actual codebase size at HEAD (from tree walk of latest commit)
        current_sloc = int(latest_commit.get('tree_sloc', 0))

        # Calculate UNIQUE metrics using tree-based approach
        # unique_sloc = branch_head_tree_sloc - divergence_point_tree_sloc
        # This gives the actual net change in codebase size from this branch
        divergence_point_sha = None
        
        if str(branch_name) == str(default_branch) or default_branch_commits is None:
            # For the default branch, unique = current (all code is "unique" to it)
            unique_commits_count = total_commits
            unique_lines = current_lines
            unique_sloc = current_sloc
        else:
            # Find the divergence point: most recent commit that's on BOTH branches
            # This is the commit where this branch diverged from default
            branch_shas = set(branch_df['commit_sha'])
            shared_commits = branch_shas & set(default_branch_commits.keys())
            
            if shared_commits:
                # Find the most recent shared commit (by date)
                divergence_sha = max(
                    shared_commits,
                    key=lambda sha: default_branch_commits[sha]['committed_at']
                )
                divergence_point_sha = divergence_sha
                divergence_sloc = int(default_branch_commits[divergence_sha].get('tree_sloc', 0))
                divergence_lines = int(default_branch_commits[divergence_sha].get('tree_lines', 0))
                
                # Unique = difference between HEAD and divergence point (tree-based)
                unique_sloc = current_sloc - divergence_sloc
                unique_lines = current_lines - divergence_lines
                
                # Count commits after the divergence point
                divergence_time = default_branch_commits[divergence_sha]['committed_at']
                unique_commits_df = branch_df[
                    (~branch_df['commit_sha'].isin(default_branch_commits.keys())) |
                    (branch_df['committed_at'] > divergence_time)
                ]
                unique_commits_count = len(unique_commits_df)
            else:
                # No shared commits - entire branch is unique
                unique_sloc = current_sloc
                unique_lines = current_lines
                unique_commits_count = total_commits

        # Timestamps
        first_commit = branch_df['committed_at'].min()
        last_commit = branch_df['committed_at'].max()

        # Total files
        total_files = branch_df['files_changed'].sum()

        return {
            'codebase_id': codebase_id,
            'branch_name': str(branch_name),
            'head_commit_sha': str(head_commit_sha),
            'divergence_point_sha': divergence_point_sha,
            'parent_branch': default_branch if divergence_point_sha else None,
            'created_at': first_commit.to_pydatetime() if hasattr(first_commit, 'to_pydatetime') else first_commit,
            'last_commit_at': last_commit.to_pydatetime() if hasattr(last_commit, 'to_pydatetime') else last_commit,
            # Line-based metrics (clean names)
            'current_lines': int(current_lines),
            'unique_lines': int(unique_lines),
            'additions_lines': int(additions_lines),
            'deletions_lines': int(deletions_lines),
            # SLOC-based metrics (clean names, already converted from bytes)
            'current_sloc': int(current_sloc),
            'unique_sloc': int(unique_sloc),
            'additions_sloc': int(additions_sloc),
            'deletions_sloc': int(deletions_sloc),
            'churn_sloc': int(churn_sloc),
            # Branch stats
            'total_commits': int(total_commits),
            'unique_commits': int(unique_commits_count),
            'unique_contributors': int(unique_contributors),
            'total_files': int(total_files),
            # Branch state
            'is_default_branch': str(branch_name) == str(default_branch),
            'is_active': True,
            'is_merged': False,
            'is_deleted': False,
            'merged_at': None,
            'deleted_at': None,
            'last_analyzed_at': datetime.now()
        }

    def _build_contributor_aggregates(self, codebase_id: str, commits_df: pd.DataFrame) -> None:
        """Build contributor aggregates and write to warm storage.
        
        A8: Contributor Tracking
        """
        logger.debug(f"Building contributor aggregates for repo {codebase_id}")
        
        contributors = _build_contributor_data(codebase_id, commits_df)
        
        if contributors:
            self.warm.write_contributors(codebase_id, contributors)
            logger.info(f"Built {len(contributors)} contributor aggregates")
        else:
            logger.debug("No contributors to aggregate")

    def _aggregates_exist(self, codebase_id: str) -> bool:
        """Check if aggregates exist for repository.

        Args:
            codebase_id: Repository ID

        Returns:
            True if repository metrics exist
        """
        metrics = self.hot.get_repository_metrics(codebase_id)
        return metrics is not None


def _build_contributor_data(codebase_id: str, commits_df: pd.DataFrame) -> list[dict]:
    """Build contributor aggregates from commits DataFrame.
    
    A8: Contributor Tracking
    
    Aggregates commits by author to build per-contributor metrics.
    
    Args:
        codebase_id: Repository ID
        commits_df: DataFrame of commits with author and metric columns
        
    Returns:
        List of contributor dicts matching CONTRIBUTORS_SCHEMA
    """
    if commits_df.empty:
        return []
    
    # Ensure datetime type
    if 'committed_at' in commits_df.columns:
        commits_df = commits_df.copy()
        commits_df['committed_at'] = pd.to_datetime(commits_df['committed_at'])
    
    now = datetime.now(timezone.utc)
    thirty_days_ago = now - timedelta(days=30)
    ninety_days_ago = now - timedelta(days=90)
    year_ago = now - timedelta(days=365)
    
    contributors = []
    
    # Group by author email
    for email, group in commits_df.groupby('author_email'):
        # Basic counts
        total_commits = len(group)
        
        # Get name (use most recent)
        name = group.iloc[-1].get('author_name', email) if 'author_name' in group.columns else email
        
        # Time range
        first_commit = group['committed_at'].min()
        last_commit = group['committed_at'].max()
        
        # Branches
        branches = group['branch_name'].unique().tolist()
        primary_branch = group['branch_name'].mode().iloc[0] if not group['branch_name'].mode().empty else branches[0]
        
        # Windowed commits
        commits_30d = len(group[group['committed_at'] >= thirty_days_ago])
        commits_90d = len(group[group['committed_at'] >= ninety_days_ago])
        commits_365d = len(group[group['committed_at'] >= year_ago])
        
        # Line metrics
        total_additions_lines = group['additions_lines'].sum()
        total_deletions_lines = group['deletions_lines'].sum()
        churn_lines = total_additions_lines + total_deletions_lines
        avg_commit_size_lines = float(churn_lines / total_commits) if total_commits > 0 else 0.0
        
        # Byte/SLOC metrics
        total_addition_bytes = group['addition_bytes'].sum()
        total_deletion_bytes = group['deletion_bytes'].sum()
        total_sloc = group['sloc'].sum()
        avg_commit_size_sloc = float(total_sloc / total_commits) if total_commits > 0 else 0.0
        
        contributor = {
            'codebase_id': codebase_id,
            'contributor_email': email,
            'contributor_name': name,
            'total_commits': int(total_commits),
            'first_commit_at': first_commit.to_pydatetime() if hasattr(first_commit, 'to_pydatetime') else first_commit,
            'last_commit_at': last_commit.to_pydatetime() if hasattr(last_commit, 'to_pydatetime') else last_commit,
            'branches_contributed_to': branches,
            'primary_branch': primary_branch,
            'branches_count': len(branches),
            'commits_last_30_days': int(commits_30d),
            'commits_last_90_days': int(commits_90d),
            'commits_last_365_days': int(commits_365d),
            'total_additions_lines': int(total_additions_lines),
            'total_deletions_lines': int(total_deletions_lines),
            'avg_commit_size_lines': float(avg_commit_size_lines),
            'total_sloc_contributed': int(total_sloc),
            'total_addition_bytes': int(total_addition_bytes),
            'total_deletion_bytes': int(total_deletion_bytes),
            'avg_commit_size_sloc': float(avg_commit_size_sloc),
            'collected_at': now,
        }
        
        contributors.append(contributor)
    
    logger.info(f"Built {len(contributors)} contributor aggregates for {codebase_id}")
    return contributors

