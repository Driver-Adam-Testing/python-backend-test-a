"""
Git Commit Fetcher using pygit2 for better performance
"""

import logging
import os
import shutil
import tempfile
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import pygit2

logger = logging.getLogger(__name__)


def get_commit_from_walker_item(
    repo: pygit2.Repository, item: pygit2.Commit | pygit2.Oid
) -> pygit2.Commit:
    """
    Helper to handle different pygit2 versions.
    Some versions return Oid, others return Commit directly.
    """
    if isinstance(item, pygit2.Commit):
        return item
    elif isinstance(item, pygit2.Oid):
        return repo.get(item)
    else:
        # Try to get it as an Oid
        try:
            return repo.get(item)
        except Exception as e:
            logger.error(f"Failed to get commit from walker item: {e}")
            # Last resort - assume it's already a commit
            return item


@dataclass
class CommitData:
    """Structured commit data"""

    sha: str
    author_name: str
    author_email: str
    authored_date: datetime
    committer_name: str
    committer_email: str
    committed_date: datetime
    message: str
    parents: list[str]
    files_changed: list[str]
    stats: dict[str, Any]  # Files with additions/deletions
    diff: str
    file_specific_diffs: dict[str, str] | None = (
        None  # Diff for a specific file if requested
    )
    branch: str | None = None
    tags: list[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "sha": self.sha,
            "author_name": self.author_name,
            "author_email": self.author_email,
            "authored_date": self.authored_date.isoformat(),
            "committer_name": self.committer_name,
            "committer_email": self.committer_email,
            "committed_date": self.committed_date.isoformat(),
            "message": self.message,
            "parents": self.parents,
            "files_changed": self.files_changed,
            "stats": self.stats,
            "diff": self.diff,
            "file_specific_diffs": self.file_specific_diffs,
            "branch": self.branch,
            "tags": self.tags or [],
        }


class GitFetcher:
    """High-performance git fetcher using pygit2"""

    def __init__(self, repo_path: str | None = None) -> None:
        """
        Initialize GitFetcher

        Args:
            repo_path: Path to local repository (optional)
        """
        self.repo_path = repo_path
        self.repo: pygit2.Repository | None = None
        self._temp_dir: str | None = None

        if repo_path:
            self.open_repository(repo_path)

    def open_repository(self, repo_path: str) -> pygit2.Repository:
        """Open a local repository"""
        try:
            self.repo = pygit2.Repository(repo_path)
            self.repo_path = repo_path
            logger.info(f"Opened repository at {repo_path}")
            return self.repo
        except Exception as e:
            raise ValueError(f"Invalid Git repository: {repo_path} - {e}")

    def clone_repository(
        self, repo_url: str, branch: str | None = None
    ) -> pygit2.Repository:
        """
        Clone a remote repository to a temporary directory

        Args:
            repo_url: URL of the repository to clone
            branch: Specific branch to clone (optional)

        Returns:
            Repository object
        """
        # Create temporary directory
        self._temp_dir = tempfile.mkdtemp(prefix="driver_historian_")
        logger.info(f"Cloning {repo_url} to {self._temp_dir}")

        try:
            # Clone repository
            callbacks = pygit2.RemoteCallbacks()

            if branch:
                self.repo = pygit2.clone_repository(
                    repo_url,
                    self._temp_dir,
                    checkout_branch=branch,
                    callbacks=callbacks,
                )
            else:
                self.repo = pygit2.clone_repository(
                    repo_url, self._temp_dir, callbacks=callbacks
                )

            self.repo_path = self._temp_dir
            logger.info("Successfully cloned repository")
            return self.repo

        except Exception as e:
            # Clean up on failure
            if self._temp_dir and os.path.exists(self._temp_dir):
                shutil.rmtree(self._temp_dir)
            raise RuntimeError(f"Failed to clone repository: {e}")

    def fetch_commits(
        self,
        branch: str | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
        author: str | None = None,
        limit: int | None = None,
        skip_merge_commits: bool = True,
        include_stats: bool = True,
        include_diff: bool = True,
        stop_commit: str | None = None,
        unravel_merges: bool = False,  # Will still unravel merges, but not explicitly return the merge commit itself
    ) -> Iterator[CommitData]:
        """
        Fetch commits from the repository

        Args:
            branch: Branch name (defaults to HEAD)
            since: Fetch commits after this date
            until: Fetch commits before this date
            author: Filter by author email or name
            limit: Maximum number of commits to fetch
            skip_merge_commits: Skip merge commits
            include_stats: Include file statistics
            include_diff: Include full diff

        Yields:
            CommitData objects
        """
        if not self.repo:
            raise RuntimeError("No repository opened or cloned")

        # Get starting point
        if branch:
            try:
                ref = self.repo.lookup_reference(f"refs/heads/{branch}")
                start_oid = ref.target
            except KeyError:
                logger.warning(f"Branch {branch} not found, using HEAD")
                start_oid = self.repo.head.target
        else:
            start_oid = self.repo.head.target

        # Walk commits
        commit_count = 0
        yielded_commits = (
            set()
        )  # Track commits we've already yielded to avoid duplicates
        walker = self.repo.walk(start_oid, pygit2.enums.SortMode.TIME)
        for walker_item in walker:
            # Use helper to handle different pygit2 versions
            commit = get_commit_from_walker_item(self.repo, walker_item)
            commit_sha = str(commit.id)

            if stop_commit and commit_sha == stop_commit:
                logger.info(f"Reached stop commit {stop_commit}, stopping fetch")
                break

            # Skip if we've already yielded this commit (can happen with unravel_merges)
            if commit_sha in yielded_commits:
                continue

            # Apply filters
            commit_time = datetime.fromtimestamp(commit.commit_time, tz=UTC)

            if since and commit_time < since:
                break  # Stop walking (commits are in time order)

            if until and commit_time > until:
                continue

            if (
                author
                and author not in commit.author.email
                and author not in commit.author.name
            ):
                continue

            # Handle merge commits
            is_merge = len(commit.parents) > 1

            # Unravel merge commits by yielding child commits
            if unravel_merges and is_merge:
                for parent in commit.parents[1:]:  # Skip first parent (mainline)
                    child_commits = self._get_merge_child_commits(
                        parent.id, commit.parents[0].id
                    )
                    for child_commit in child_commits:
                        child_sha = str(child_commit.id)

                        # Skip if already yielded or is a merge commit
                        if child_sha in yielded_commits:
                            continue
                        if len(child_commit.parents) > 1:
                            logger.debug(f"Skipping child merge commit {child_sha}")
                            continue

                        commit_data = self._process_commit(
                            child_commit,
                            branch=branch,
                            include_stats=include_stats,
                            include_diff=include_diff,
                        )
                        yield commit_data
                        yielded_commits.add(child_sha)

                        commit_count += 1
                        if limit and commit_count >= limit:
                            return
                continue
            elif skip_merge_commits and is_merge:
                continue

            # Convert to CommitData
            commit_data = self._process_commit(
                commit,
                branch=branch,
                include_stats=include_stats,
                include_diff=include_diff,
            )

            yield commit_data
            yielded_commits.add(commit_sha)

            commit_count += 1
            if limit and commit_count >= limit:
                break

    def fetch_commit_by_sha(
        self, sha: str, include_stats: bool = True, include_diff: bool = True
    ) -> CommitData:
        """Fetch a specific commit by SHA"""
        if not self.repo:
            raise RuntimeError("No repository opened or cloned")

        try:
            # Try different methods for different pygit2 versions
            try:
                commit = self.repo.revparse_single(sha)
            except Exception as e:
                logger.warning(f"Failed to revparse {sha}: {e}")
                oid = pygit2.Oid(hex=sha)
                commit = self.repo.get(oid)

            if not isinstance(commit, pygit2.Commit):
                raise ValueError(f"Object {sha} is not a commit")

            return self._process_commit(
                commit, include_stats=include_stats, include_diff=include_diff
            )
        except (KeyError, ValueError) as e:
            raise ValueError(f"Commit {sha} not found: {e}")

    def fetch_file_history(
        self,
        file_path: str,
        branch: str | None = None,
        limit: int | None = None,
        include_diff: bool = True,
    ) -> list[CommitData]:
        """
        Fetch commit history for a specific file

        Args:
            file_path: Path to the file
            branch: Branch name (defaults to HEAD)
            limit: Maximum number of commits
            include_diff: Include diffs

        Returns:
            List of CommitData objects
        """
        if not self.repo:
            raise RuntimeError("No repository opened or cloned")

        commits = []

        # Get starting point
        if branch:
            try:
                ref = self.repo.lookup_reference(f"refs/heads/{branch}")
                start_oid = ref.target
            except KeyError:
                start_oid = self.repo.head.target
        else:
            start_oid = self.repo.head.target

        # Walk commits and check if they touch the file
        walker = self.repo.walk(start_oid, pygit2.GIT_SORT_TIME)
        for walker_item in walker:
            # Use helper to handle different pygit2 versions
            commit = get_commit_from_walker_item(self.repo, walker_item)

            if len(commit.parents) > 1:
                # Skip merge commits
                continue
            # Check if this commit touches the file
            if self._commit_touches_file(commit, file_path):
                commit_data = self._process_commit(
                    commit,
                    branch=branch,
                    include_stats=True,
                    include_diff=include_diff,
                    file_path=file_path,
                )
                commits.append(commit_data)

                if limit and len(commits) >= limit:
                    break

        return commits

    def _get_merge_child_commits(
        self, merge_parent: pygit2.Oid, mainline_parent: pygit2.Oid
    ) -> list[pygit2.Commit]:
        child_commits = []
        visited = set()

        # Walk from merge_parent back to where it diverged from mainline
        walker = self.repo.walk(merge_parent, pygit2.enums.SortMode.TIME)

        print(f"Unraveling merge from {merge_parent} to {mainline_parent}")
        for walker_item in walker:
            commit = get_commit_from_walker_item(self.repo, walker_item)
            commit_id = str(commit.id)

            if commit_id in visited:
                continue

            visited.add(commit_id)

            # Stop if we've reached the mainline
            if commit.id == mainline_parent:
                break

            # Check if this commit is reachable from mainline_parent
            try:
                is_ancestor = self.repo.descendant_of(mainline_parent, commit.id)
                if is_ancestor:
                    break
            except Exception:
                # If we can't determine ancestry, continue collecting commits
                pass

            child_commits.append(commit)

        print(f"Found {len(child_commits)} child commits in merge")
        return child_commits

    def _commit_touches_file(self, commit: pygit2.Commit, file_path: str) -> bool:
        """Check if a commit modifies a specific file"""
        if not commit.parents:
            # First commit - check if file exists
            try:
                tree = commit.tree
                tree[file_path]
                return True
            except KeyError:
                return False

        # Compare with parent
        parent = commit.parents[0]
        diff = self.repo.diff(parent, commit)

        for patch in diff:
            if (
                patch.delta.old_file.path == file_path
                or patch.delta.new_file.path == file_path
            ):
                return True

        return False

    def _process_commit(
        self,
        commit: pygit2.Commit,
        branch: str | None = None,
        include_stats: bool = True,
        include_diff: bool = True,
        file_path: str | None = None,
    ) -> CommitData:
        """Process a pygit2 Commit object into CommitData"""

        # Get basic info
        sha = str(commit.id)
        message = commit.message
        parents = [str(parent_id) for parent_id in commit.parents]

        # Author info
        author_name = commit.author.name
        author_email = commit.author.email
        authored_date = datetime.fromtimestamp(commit.author.time, tz=UTC)

        # Committer info
        committer_name = commit.committer.name
        committer_email = commit.committer.email
        committed_date = datetime.fromtimestamp(commit.commit_time, tz=UTC)

        # Get files changed and stats
        files_changed = []
        stats = {}
        diff_text = ""
        file_specific_diffs = {}

        if (include_stats or include_diff) and commit.parents:
            # Compare with first parent
            # print('parent',commit.parents.items())
            parent = commit.parents[0]
            diff = self.repo.diff(parent, commit)

            # Configure diff options
            diff.find_similar()

            if include_stats:
                # Get file stats
                for patch in diff:
                    old_path = patch.delta.old_file.path
                    new_path = patch.delta.new_file.path

                    # Handle renames
                    if old_path != new_path:
                        files_changed.extend([old_path, new_path])
                    else:
                        files_changed.append(new_path)

                    # Get line stats
                    additions = patch.line_stats[1]  # additions
                    deletions = patch.line_stats[2]  # deletions

                    if new_path not in stats:
                        stats[new_path] = {
                            "additions": 0,
                            "deletions": 0,
                            "old_path": old_path if old_path != new_path else None,
                        }
                    stats[new_path]["additions"] += additions
                    stats[new_path]["deletions"] += deletions
                    # stats[new_path] = {
                    #     'additions': additions,
                    #     'deletions': deletions,
                    #     'old_path': old_path if old_path != new_path else None
                    # }

            if include_diff:
                file_specific_diffs = {}
                # Generate unified diff
                diff_text = diff.patch or ""
                for patch in diff:
                    if patch.delta.new_file.path not in file_specific_diffs:
                        file_specific_diffs[patch.delta.new_file.path] = ""
                    file_specific_diffs[patch.delta.new_file.path] += patch.text + "\n"
                # if file_path is not None:
                #     file_diff = ""
                #     for patch in diff:
                #         if patch.delta.new_file.path == file_path or patch.delta.old_file.path == file_path:
                #             file_diff += patch.text + "\n"

        elif not commit.parents:
            # First commit - all files are new
            try:
                for entry in commit.tree:
                    if entry.type == "blob":
                        files_changed.append(entry.name)
                        if include_stats:
                            # Count lines in new files
                            blob = self.repo[entry.id]
                            lines = blob.data.decode("utf-8", errors="ignore").count(
                                "\n"
                            )
                            stats[entry.name] = {"additions": lines, "deletions": 0}
            except Exception as e:
                logger.warning(f"Error processing first commit: {e}")

        # Get tags pointing to this commit
        tags = []
        for ref in self.repo.listall_references():
            if ref.startswith("refs/tags/"):
                tag_ref = self.repo.lookup_reference(ref)
                if tag_ref.target == commit.id:
                    tags.append(ref.replace("refs/tags/", ""))

        return CommitData(
            sha=sha,
            author_name=author_name,
            author_email=author_email,
            authored_date=authored_date,
            committer_name=committer_name,
            committer_email=committer_email,
            committed_date=committed_date,
            message=message,
            parents=parents,
            files_changed=files_changed,
            stats=stats,
            diff=diff_text,
            file_specific_diffs=file_specific_diffs,
            branch=branch,
            tags=tags,
        )

    def get_branches(self) -> list[str]:
        """Get list of all branches"""
        if not self.repo:
            raise RuntimeError("No repository opened or cloned")

        branches = []
        for ref in self.repo.listall_references():
            if ref.startswith("refs/heads/"):
                branches.append(ref.replace("refs/heads/", ""))

        return branches

    def get_tags(self) -> list[tuple[str, str]]:
        """Get list of all tags with their commit SHAs"""
        if not self.repo:
            raise RuntimeError("No repository opened or cloned")

        tags = []
        for ref in self.repo.listall_references():
            if ref.startswith("refs/tags/"):
                tag_name = ref.replace("refs/tags/", "")
                tag_ref = self.repo.lookup_reference(ref)

                # Dereference annotated tags
                target = tag_ref.target
                obj = self.repo[target]
                if obj.type == pygit2.GIT_OBJ_TAG:
                    target = obj.target

                tags.append((tag_name, str(target)))

        return tags

    def get_commit_count(self, branch: str | None = None) -> int:
        """Get total number of commits in branch"""
        if not self.repo:
            raise RuntimeError("No repository opened or cloned")

        # Get starting point
        if branch:
            try:
                ref = self.repo.lookup_reference(f"refs/heads/{branch}")
                start_oid = ref.target
            except KeyError:
                start_oid = self.repo.head.target
        else:
            start_oid = self.repo.head.target

        # Count commits
        count = 0
        walker = self.repo.walk(start_oid)
        for _ in walker:
            count += 1

        return count

    def cleanup(self) -> None:
        """Clean up temporary directory if using cloned repo"""
        if self._temp_dir and os.path.exists(self._temp_dir):
            logger.info(f"Cleaning up temporary directory: {self._temp_dir}")
            shutil.rmtree(self._temp_dir)
            self._temp_dir = None

        self.repo = None
        self.repo_path = None

    def __enter__(self) -> "GitFetcher":
        """Context manager support"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # noqa: ANN001
        """Clean up on exit"""
        self.cleanup()


class BatchCommitProcessor:
    """Process commits in batches for efficiency with pygit2"""

    def __init__(self, fetcher: GitFetcher, batch_size: int = 100) -> None:
        self.fetcher = fetcher
        self.batch_size = batch_size

    def process_commits_parallel(
        self,
        processor_func: Callable,
        branch: str | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
        num_workers: int = 4,
        progress_callback: Callable | None = None,
    ) -> int:
        """
        Process commits in parallel batches (pygit2 is thread-safe)

        Args:
            processor_func: Function to process batch of commits
            branch: Branch to process
            since: Start date
            until: End date
            num_workers: Number of parallel workers
            progress_callback: Optional callback for progress updates

        Returns:
            Total number of commits processed
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed

        # Collect commit OIDs first (lightweight)
        oids = []
        for commit in self.fetcher.fetch_commits(
            branch=branch,
            since=since,
            until=until,
            include_stats=False,
            include_diff=False,
        ):
            oids.append(commit.sha)

        total_commits = len(oids)
        if total_commits == 0:
            return 0

        # Process in parallel batches
        total_processed = 0

        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            # Split OIDs into batches
            batches = [
                oids[i : i + self.batch_size]
                for i in range(0, len(oids), self.batch_size)
            ]

            # Submit batch processing tasks
            futures = []
            for batch_oids in batches:
                future = executor.submit(
                    self._process_batch, batch_oids, processor_func
                )
                futures.append(future)

            # Process results as they complete
            for future in as_completed(futures):
                try:
                    batch_size = future.result()
                    total_processed += batch_size

                    if progress_callback:
                        progress_callback(total_processed, total_commits)

                except Exception as e:
                    logger.error(f"Error processing batch: {e}")

        return total_processed

    def _process_batch(self, oid_batch: list[str], processor_func: Callable) -> int:
        """Process a batch of commits by OID"""
        commits = []

        for oid in oid_batch:
            try:
                commit_data = self.fetcher.fetch_commit_by_sha(oid)
                commits.append(commit_data)
            except Exception as e:
                logger.error(f"Error fetching commit {oid}: {e}")

        if commits:
            processor_func(commits)

        return len(commits)


def test_basic_functionality() -> None:
    """Test basic pygit2 functionality"""
    import sys

    print(f"Python version: {sys.version}")
    print(f"pygit2 version: {pygit2.__version__}")
    print(f"libgit2 version: {pygit2.LIBGIT2_VERSION}\n")

    # Test with a small repository
    repo_path = "."  # Current directory

    try:
        print(f"Opening repository at {repo_path}")
        fetcher = GitFetcher(repo_path)

        print("Repository opened successfully!")
        print(f"Branches: {fetcher.get_branches()[:5]}")  # First 5 branches

        print("\nFetching last 5 commits...")
        commits = list(fetcher.fetch_commits(limit=5, include_diff=True))
        print(commits)
        for commit in commits:
            print(f"\n{commit.sha[:8]} - {commit.author_name}")
            print(f"  {commit.message.strip()[:60]}...")
            print(f"  Files: {len(commit.files_changed)}")

        print("\nTest completed successfully!")

    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()


def benchmark_comparison() -> None:
    """Compare pygit2 vs GitPython performance"""
    import time

    repo_path = "."  # Use current directory for testing

    print("=== Performance Comparison ===\n")

    # Test pygit2
    print("Testing pygit2...")
    start = time.time()

    try:
        fetcher = GitFetcher(repo_path)
        commits = list(fetcher.fetch_commits(limit=1000, include_diff=True))

        pygit2_time = time.time() - start
        print(f"pygit2: {len(commits)} commits in {pygit2_time:.2f} seconds")
        print(f"Rate: {len(commits) / pygit2_time:.0f} commits/second\n")
    except Exception as e:
        print(f"Error with pygit2: {e}")
        import traceback

        traceback.print_exc()
        return

    # For comparison with GitPython (if installed)
    try:
        from git import Repo

        print("Testing GitPython...")
        start = time.time()

        repo = Repo(repo_path)
        git_commits = list(repo.iter_commits(max_count=1000))

        gitpython_time = time.time() - start
        print(f"GitPython: {len(git_commits)} commits in {gitpython_time:.2f} seconds")
        print(f"Rate: {len(git_commits) / gitpython_time:.0f} commits/second\n")

        print(f"pygit2 is {gitpython_time / pygit2_time:.1f}x faster")

    except ImportError:
        print("GitPython not installed for comparison")


if __name__ == "__main__":
    print("pygit2-based Git Fetcher")
    print("=" * 50)

    # First run basic test
    test_basic_functionality()

    print("\n" + "=" * 50 + "\n")

    # Then run benchmark if basic test passes
    user_input = input("Run benchmark comparison? (y/n): ")
    if user_input.lower() == "y":
        benchmark_comparison()
