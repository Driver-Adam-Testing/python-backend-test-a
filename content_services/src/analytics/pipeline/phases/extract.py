"""
Extract phase: Extract commit data from repository using pygit2.

This phase collects commit metadata and calculates SLOC metrics.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pygit2

from analytics.sloc.calculator import DualSLOCCalculator, SLOCMetrics

logger = logging.getLogger(__name__)


@dataclass
class ExtractResult:
    """Result of commit extraction."""
    success: bool
    commits: list[dict]
    total_commits: int
    error: str | None = None
    file_changes: list[dict] | None = None
    
    def __post_init__(self):
        if self.file_changes is None:
            self.file_changes = []


def extract_commits(
    repo: pygit2.Repository,
    codebase_id: str,
    branch_names: list[str] | None = None,
    include_patches: bool = True,
    since_sha: str | None = None,
    include_file_changes: bool = False,
) -> ExtractResult:
    """
    Extract commits from repository.

    Args:
        repo: pygit2.Repository instance
        codebase_id: Codebase UUID
        branch_names: List of branches to extract from (None = all)
        include_patches: Whether to include patch data for SLOC
        since_sha: Only extract commits after this SHA (for incremental updates)
        include_file_changes: Whether to extract file-level changes (for cold storage)

    Returns:
        ExtractResult with commit data and optionally file changes
    """
    logger.info(f"Extracting commits for codebase {codebase_id}")

    try:
        # Get branches to process
        if branch_names is None:
            branch_names = _get_all_branch_names(repo)

        logger.info(f"Processing {len(branch_names)} branches: {branch_names[:5]}...")

        # Collect commits from all branches
        all_commits = []
        commit_shas_by_branch: dict[str, set[str]] = {}

        for branch_name in branch_names:
            branch_shas = _get_commits_in_branch(repo, branch_name)
            commit_shas_by_branch[branch_name] = branch_shas
            logger.debug(f"Branch {branch_name}: {len(branch_shas)} commits")

        # Get unique commit SHAs across all branches
        all_sha_set = set()
        for shas in commit_shas_by_branch.values():
            all_sha_set.update(shas)

        total_before_filter = len(all_sha_set)
        logger.info(f"Found {total_before_filter} unique commits")

        # Filter by since_sha for incremental updates
        if since_sha:
            all_sha_set = _filter_commits_since(repo, all_sha_set, since_sha)
            # Also filter branch-specific sets
            for branch_name in commit_shas_by_branch:
                commit_shas_by_branch[branch_name] &= all_sha_set
            logger.info(f"Incremental: {len(all_sha_set)} new commits (filtered {total_before_filter - len(all_sha_set)} old)")

        # Process each commit
        collected_at = datetime.now(timezone.utc)
        all_file_changes = []

        for i, commit_sha in enumerate(all_sha_set):
            if (i + 1) % 100 == 0:
                logger.debug(f"Processing commit {i + 1}/{len(all_sha_set)}")

            try:
                # Get branches this commit belongs to
                commit_branches = [
                    branch for branch, shas in commit_shas_by_branch.items()
                    if commit_sha in shas
                ]

                # Extract commit data (also returns diff for file changes)
                commit_data, diff = _extract_commit_data_with_diff(
                    repo, commit_sha, codebase_id, commit_branches,
                    collected_at, include_patches
                )

                if commit_data:
                    all_commits.extend(commit_data)
                    
                    # Extract file-level changes if requested
                    if include_file_changes and diff:
                        commit_time = datetime.fromtimestamp(
                            repo.get(commit_sha).commit_time, tz=timezone.utc
                        )
                        file_changes = _extract_file_changes(
                            diff, commit_sha, codebase_id, commit_time.date()
                        )
                        all_file_changes.extend(file_changes)

            except Exception as e:
                logger.warning(f"Error processing commit {commit_sha[:8]}: {e}")
                continue

        logger.info(f"Successfully extracted {len(all_commits)} commit records")
        if include_file_changes:
            logger.info(f"Extracted {len(all_file_changes)} file change records")

        return ExtractResult(
            success=True,
            commits=all_commits,
            total_commits=len(all_sha_set),
            file_changes=all_file_changes if include_file_changes else [],
        )

    except Exception as e:
        error_msg = f"Failed to extract commits: {e}"
        logger.error(error_msg)
        return ExtractResult(
            success=False,
            commits=[],
            total_commits=0,
            error=error_msg
        )


def _get_all_branch_names(repo: pygit2.Repository) -> list[str]:
    """Get all branch names (local + remote, deduplicated)."""
    branch_names = set()

    # Add local branches
    for branch_name in repo.branches.local:
        branch_names.add(branch_name)

    # Add remote branches (strip "origin/" prefix)
    for remote_branch in repo.branches.remote:
        if "/" in remote_branch:
            branch_name = remote_branch.split("/", 1)[1]
            if branch_name.upper() != "HEAD":
                branch_names.add(branch_name)

    return sorted(list(branch_names))


def _get_commits_in_branch(repo: pygit2.Repository, branch_name: str) -> set[str]:
    """Get all commit SHAs in a branch."""
    # Try to get branch reference (local first, then remote)
    branch_ref = None
    if branch_name in repo.branches.local:
        branch_ref = repo.branches[branch_name]
    elif f"origin/{branch_name}" in repo.branches.remote:
        branch_ref = repo.branches[f"origin/{branch_name}"]
    else:
        logger.warning(f"Branch not found: {branch_name}")
        return set()

    # Walk commits in branch
    commit_shas = set()
    try:
        for commit in repo.walk(
            branch_ref.target,
            pygit2.GIT_SORT_TOPOLOGICAL | pygit2.GIT_SORT_TIME
        ):
            commit_shas.add(str(commit.id))
    except Exception as e:
        logger.warning(f"Error walking branch {branch_name}: {e}")

    return commit_shas


def _filter_commits_since(
    repo: pygit2.Repository,
    all_shas: set[str],
    since_sha: str
) -> set[str]:
    """Filter commits to only those after since_sha.

    Uses git ancestry to determine which commits are new.
    If since_sha is not found, returns all commits (fallback to full rebuild).
    
    Args:
        repo: pygit2.Repository instance
        all_shas: Set of all commit SHAs to filter
        since_sha: Only include commits after this SHA
        
    Returns:
        Set of commit SHAs that are newer than since_sha
    """
    try:
        # Try to find the since_sha commit
        since_commit = repo.get(since_sha)
        if not since_commit:
            logger.warning(f"since_sha {since_sha[:8]} not found, extracting all commits")
            return all_shas

        # Get all commits reachable from since_sha (these are the "old" commits)
        old_shas = set()
        try:
            for commit in repo.walk(since_commit.id, pygit2.GIT_SORT_TOPOLOGICAL):
                old_shas.add(str(commit.id))
        except Exception as e:
            logger.warning(f"Error walking from since_sha: {e}")
            return all_shas

        # New commits = all commits - old commits (including since_sha itself)
        new_shas = all_shas - old_shas
        
        logger.debug(f"Filtered: {len(new_shas)} new commits, {len(old_shas)} old commits")
        return new_shas

    except Exception as e:
        logger.warning(f"Error filtering commits since {since_sha[:8]}: {e}")
        return all_shas  # Fallback to all


# Map pygit2 status chars to our change types
STATUS_CHAR_TO_CHANGE_TYPE = {
    'A': 'added',
    'D': 'deleted',
    'M': 'modified',
    'R': 'renamed',
    'C': 'copied',
    'T': 'typechange',
}


def _extract_file_changes(
    diff: pygit2.Diff,
    commit_sha: str,
    codebase_id: str,
    commit_date,
) -> list[dict]:
    """Extract file-level changes from a diff.
    
    Args:
        diff: pygit2.Diff object
        commit_sha: SHA of the commit
        codebase_id: Codebase UUID
        commit_date: Date of the commit (date object)
        
    Returns:
        List of file change dictionaries matching FILE_CHANGES_SCHEMA
    """
    file_changes = []
    
    if not diff:
        return file_changes
    
    try:
        for patch in diff:
            delta = patch.delta
            
            # Determine file path (new path for adds/modifies, old for deletes)
            new_path = delta.new_file.path if delta.new_file.path else ""
            old_path = delta.old_file.path if delta.old_file.path else ""
            file_path = new_path or old_path
            
            if not file_path:
                continue
            
            # Get change type from status char
            try:
                status_char = delta.status_char()
                change_type = STATUS_CHAR_TO_CHANGE_TYPE.get(status_char, 'modified')
            except Exception:
                change_type = 'modified'
            
            # Get line stats
            try:
                _, additions, deletions = patch.line_stats
            except Exception:
                additions = 0
                deletions = 0
            
            # Calculate bytes from patch text
            addition_bytes = 0
            deletion_bytes = 0
            has_patch_data = False
            
            try:
                patch_text = patch.text
                if patch_text:
                    has_patch_data = True
                    for line in patch_text.split('\n'):
                        if line.startswith('+') and not line.startswith('+++'):
                            addition_bytes += len(line[1:].encode('utf-8', errors='replace'))
                        elif line.startswith('-') and not line.startswith('---'):
                            deletion_bytes += len(line[1:].encode('utf-8', errors='replace'))
            except Exception as e:
                logger.debug(f"Could not parse patch text for {file_path}: {e}")
            
            # Extract file extension
            file_extension = None
            if '.' in file_path:
                file_extension = '.' + file_path.rsplit('.', 1)[-1]
            
            # Calculate SLOC for this file (bytes / 50)
            file_sloc = (addition_bytes + deletion_bytes) // 50
            
            # Detect language from file path (A11)
            from analytics.aggregation.language import _get_language_from_path
            file_language = _get_language_from_path(file_path)
            
            file_change = {
                'codebase_id': codebase_id,
                'commit_sha': commit_sha,
                'file_path': file_path,
                'commit_date': commit_date,
                'change_type': change_type,
                'previous_path': old_path if change_type == 'renamed' else None,
                'additions_lines': additions,
                'deletions_lines': deletions,
                'changes_lines': additions + deletions,
                'addition_bytes': addition_bytes,
                'deletion_bytes': deletion_bytes,
                'file_sloc': file_sloc,
                'file_extension': file_extension,
                'file_language': file_language,
                'has_patch_data': has_patch_data,
                'patch_blob_key': None,  # Reserved for future patch storage
            }
            
            file_changes.append(file_change)
            
    except Exception as e:
        logger.warning(f"Error extracting file changes for {commit_sha[:8]}: {e}")
    
    return file_changes


def _extract_commit_data_with_diff(
    repo: pygit2.Repository,
    commit_sha: str,
    codebase_id: str,
    branches: list[str],
    collected_at: datetime,
    include_patches: bool
) -> tuple[list[dict], pygit2.Diff | None]:
    """
    Extract data for a single commit and return the diff.

    Returns:
        Tuple of (commit records, diff object)
        - One commit record per branch the commit belongs to
        - The diff object for file-level extraction
    """
    try:
        commit = repo.get(commit_sha)
        if not commit:
            return [], None

        # Get diff from parent
        diff = _get_commit_diff(repo, commit)

        # Calculate line/byte metrics from diff
        files_changed = 0
        total_additions = 0
        total_deletions = 0
        total_addition_bytes = 0
        total_deletion_bytes = 0

        if diff:
            # Use diff.stats for line counts (most reliable)
            stats = diff.stats
            files_changed = stats.files_changed
            total_additions = stats.insertions
            total_deletions = stats.deletions
            
            # Calculate bytes from patch content
            # CRITICAL: Always use patch data for accurate SLOC. No fallback to estimates.
            # The include_patches parameter is deprecated but kept for API compatibility.
            try:
                patch_text = diff.patch
                if patch_text:
                    for line in patch_text.split('\n'):
                        if line.startswith('+') and not line.startswith('+++'):
                            total_addition_bytes += len(line[1:].encode('utf-8', errors='replace'))
                        elif line.startswith('-') and not line.startswith('---'):
                            total_deletion_bytes += len(line[1:].encode('utf-8', errors='replace'))
                else:
                    # No patch data available - log warning, set bytes to 0
                    logger.warning(f"Commit {commit_sha[:8]}: No patch data available, bytes set to 0")
            except Exception as e:
                # Patch analysis failed - log warning, set bytes to 0
                logger.warning(f"Commit {commit_sha[:8]}: Patch analysis failed: {e}, bytes set to 0")
                total_addition_bytes = 0
                total_deletion_bytes = 0

        # Calculate derived metrics
        net_lines = total_additions - total_deletions
        churn_lines = total_additions + total_deletions
        patch_bytes = total_addition_bytes + total_deletion_bytes
        net_bytes = total_addition_bytes - total_deletion_bytes
        sloc = patch_bytes // 50
        bytes_per_line = patch_bytes / churn_lines if churn_lines > 0 else 0.0

        # Categorize commit size
        if churn_lines < 10:
            size_category = "tiny"
        elif churn_lines < 50:
            size_category = "small"
        elif churn_lines < 200:
            size_category = "medium"
        else:
            size_category = "large"

        # Get commit timestamp
        commit_time = datetime.fromtimestamp(commit.commit_time, tz=timezone.utc)

        # Calculate actual codebase size at this commit (tree walk)
        # This is the REAL codebase size, not cumulative churn
        tree_bytes, tree_lines = _get_tree_size_at_commit(repo, commit)
        tree_sloc = tree_bytes // 50  # Same conversion factor as Driver

        # Create base commit record
        base_record = {
            'commit_sha': commit_sha,
            'codebase_id': codebase_id,
            'committed_at': commit_time,
            'collected_at': collected_at,
            'commit_date': commit_time.date(),
            'commit_year': commit_time.year,
            'commit_month': commit_time.month,
            'commit_day': commit_time.day,
            'author_email': commit.author.email,
            'author_name': commit.author.name,
            'committer_email': commit.committer.email,
            'committer_name': commit.committer.name,
            'message': commit.message[:1000] if commit.message else "",
            'message_length': len(commit.message) if commit.message else 0,
            'parent_count': len(commit.parents),
            'is_merge_commit': len(commit.parents) > 1,
            'files_changed': files_changed,
            'additions_lines': total_additions,
            'deletions_lines': total_deletions,
            'net_lines': net_lines,
            'churn_lines': churn_lines,
            'addition_bytes': total_addition_bytes,
            'deletion_bytes': total_deletion_bytes,
            'patch_bytes': patch_bytes,
            'net_bytes': net_bytes,
            'sloc': sloc,
            'bytes_per_line': bytes_per_line,
            'commit_size_category': size_category,
            'is_refactor': total_additions > 0 and total_deletions > 0 and abs(net_lines) < churn_lines * 0.1,
            # Tree-based metrics (actual codebase size at this commit)
            'tree_bytes': tree_bytes,
            'tree_lines': tree_lines,
            'tree_sloc': tree_sloc,
            'collection_version': '2.0'
        }

        # Create one record per branch
        records = []
        for branch in branches:
            record = base_record.copy()
            record['branch_name'] = branch
            records.append(record)

        return records, diff

    except Exception as e:
        logger.warning(f"Error extracting commit {commit_sha[:8]}: {e}")
        return [], None


def _get_commit_diff(repo: pygit2.Repository, commit: pygit2.Commit) -> pygit2.Diff | None:
    """Get diff for a commit compared to its parent."""
    try:
        if commit.parents:
            # Normal commit: diff against first parent
            parent = commit.parents[0]
            return repo.diff(parent.tree, commit.tree)
        else:
            # First commit: diff against empty tree
            tree_builder = repo.TreeBuilder()
            empty_tree_oid = tree_builder.write()
            empty_tree = repo.get(empty_tree_oid)
            return repo.diff(empty_tree, commit.tree)
    except Exception as e:
        logger.debug(f"Error getting diff for commit {commit.id}: {e}")
        return None


def _get_tree_size_at_commit(repo: pygit2.Repository, commit: pygit2.Commit) -> tuple[int, int]:
    """
    Calculate the total size of the codebase at a given commit by walking its tree.
    
    This gives the ACTUAL codebase size (all files) at this point in history,
    NOT the cumulative churn from patches. This is what users expect when they
    see "current SLOC" - the actual size of the codebase.
    
    Args:
        repo: pygit2.Repository instance
        commit: pygit2.Commit to analyze
        
    Returns:
        Tuple of (total_bytes, total_lines) for all non-binary files in the tree
    """
    total_bytes = 0
    total_lines = 0
    
    try:
        tree = commit.tree
        if not tree:
            return (0, 0)
        
        # Recursively walk the tree
        total_bytes, total_lines = _walk_tree_recursive(repo, tree)
        
    except Exception as e:
        logger.warning(f"Error calculating tree size for commit {commit.id}: {e}")
        return (0, 0)
    
    return (total_bytes, total_lines)


def _walk_tree_recursive(repo: pygit2.Repository, tree: pygit2.Tree) -> tuple[int, int]:
    """
    Recursively walk a tree and sum up file sizes.
    
    Args:
        repo: pygit2.Repository instance
        tree: pygit2.Tree to walk
        
    Returns:
        Tuple of (total_bytes, total_lines)
    """
    total_bytes = 0
    total_lines = 0
    
    for entry in tree:
        try:
            if entry.type_str == 'blob':
                # It's a file - get the blob and check if binary
                blob = repo.get(entry.id)
                if blob and not blob.is_binary:
                    data = blob.data
                    total_bytes += len(data)
                    # Count lines: number of newlines + 1 for last line without newline
                    if data:
                        total_lines += data.count(b'\n')
                        # Add 1 for the last line if it doesn't end with newline
                        if not data.endswith(b'\n'):
                            total_lines += 1
                            
            elif entry.type_str == 'tree':
                # It's a subdirectory - recurse
                subtree = repo.get(entry.id)
                if subtree:
                    sub_bytes, sub_lines = _walk_tree_recursive(repo, subtree)
                    total_bytes += sub_bytes
                    total_lines += sub_lines
                    
        except Exception as e:
            logger.debug(f"Error processing tree entry {entry.name}: {e}")
            continue
    
    return (total_bytes, total_lines)

