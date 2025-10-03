"""Unit tests for git_fetcher_pygit2.py using temporary repositories"""

import tempfile
from pathlib import Path

import pygit2
import pytest

from .git_fetcher_pygit2 import CommitData, GitFetcher


@pytest.fixture
def temp_repo() -> pygit2.Repository:
    """Create a temporary git repository with some test commits"""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)
        repo = pygit2.init_repository(repo_path, bare=False)

        # Base time for commits (need increasing timestamps for proper ordering)
        base_time = 1609459200  # 2021-01-01 00:00:00 UTC
        offset = 0

        # Create initial commit (no HEAD exists yet, use refs/heads/master)
        sig1 = pygit2.Signature(
            "Test User", "test@example.com", time=base_time, offset=offset
        )
        tree_id = _create_tree_with_files(repo, {"file1.txt": "Initial content"})
        commit1_oid = repo.create_commit(
            "refs/heads/master",
            sig1,
            sig1,
            "Initial commit",
            tree_id,
            [],
        )

        # Set HEAD to point to master
        repo.set_head("refs/heads/master")

        # Create second commit (1 hour later)
        sig2 = pygit2.Signature(
            "Test User", "test@example.com", time=base_time + 3600, offset=offset
        )
        tree_id = _create_tree_with_files(
            repo, {"file1.txt": "Modified content", "file2.txt": "New file"}
        )
        commit2_oid = repo.create_commit(
            "refs/heads/master",
            sig2,
            sig2,
            "Add file2 and modify file1",
            tree_id,
            [commit1_oid],
        )

        # Create third commit (2 hours later)
        sig3 = pygit2.Signature(
            "Test User", "test@example.com", time=base_time + 7200, offset=offset
        )
        tree_id = _create_tree_with_files(
            repo,
            {
                "file1.txt": "Modified again",
                "file2.txt": "New file",
                "file3.txt": "Another file",
            },
        )
        repo.create_commit(
            "refs/heads/master",
            sig3,
            sig3,
            "Add file3",
            tree_id,
            [commit2_oid],
        )

        yield repo


def _create_tree_with_files(
    repo: pygit2.Repository, files: dict[str, str]
) -> pygit2.Oid:
    """Helper to create a tree with specified files"""
    builder = repo.TreeBuilder()
    for filename, content in files.items():
        blob_id = repo.create_blob(content.encode("utf-8"))
        builder.insert(filename, blob_id, pygit2.GIT_FILEMODE_BLOB)
    return builder.write()


def test_fetch_commits_basic(temp_repo: pygit2.Repository) -> None:
    """Test fetching commits from a repository"""
    fetcher = GitFetcher(temp_repo.workdir)
    commits = list(fetcher.fetch_commits(skip_merge_commits=False))

    assert len(commits) == 3
    assert all(isinstance(c, CommitData) for c in commits)
    assert commits[0].message == "Add file3"
    assert commits[1].message == "Add file2 and modify file1"
    assert commits[2].message == "Initial commit"


def test_fetch_commits_with_limit(temp_repo: pygit2.Repository) -> None:
    """Test fetching commits with a limit"""
    fetcher = GitFetcher(temp_repo.workdir)
    commits = list(fetcher.fetch_commits(limit=2, skip_merge_commits=False))

    assert len(commits) == 2
    assert commits[0].message == "Add file3"
    assert commits[1].message == "Add file2 and modify file1"


@pytest.fixture
def repo_with_merge() -> pygit2.Repository:
    """Create a temporary git repository with a merge commit"""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)
        repo = pygit2.init_repository(repo_path, bare=False)

        base_time = 1609459200  # 2021-01-01 00:00:00 UTC
        offset = 0

        # Create initial commit on master
        sig1 = pygit2.Signature(
            "Test User", "test@example.com", time=base_time, offset=offset
        )
        tree_id = _create_tree_with_files(repo, {"file1.txt": "Initial content"})
        commit1_oid = repo.create_commit(
            "refs/heads/master",
            sig1,
            sig1,
            "Initial commit",
            tree_id,
            [],
        )
        repo.set_head("refs/heads/master")

        # Create a feature branch from initial commit
        repo.references.create("refs/heads/feature", commit1_oid)

        # Add commit on feature branch (1 hour later)
        sig2 = pygit2.Signature(
            "Feature Dev", "dev@example.com", time=base_time + 3600, offset=offset
        )
        tree_id = _create_tree_with_files(
            repo, {"file1.txt": "Initial content", "feature.txt": "Feature work"}
        )
        feature_commit1_oid = repo.create_commit(
            "refs/heads/feature",
            sig2,
            sig2,
            "Add feature work",
            tree_id,
            [commit1_oid],
        )

        # Add another commit on feature branch (2 hours later)
        sig3 = pygit2.Signature(
            "Feature Dev", "dev@example.com", time=base_time + 7200, offset=offset
        )
        tree_id = _create_tree_with_files(
            repo, {"file1.txt": "Initial content", "feature.txt": "More feature work"}
        )
        feature_commit2_oid = repo.create_commit(
            "refs/heads/feature",
            sig3,
            sig3,
            "Improve feature",
            tree_id,
            [feature_commit1_oid],
        )

        # Add commit on master (2.5 hours later)
        sig4 = pygit2.Signature(
            "Test User", "test@example.com", time=base_time + 9000, offset=offset
        )
        tree_id = _create_tree_with_files(
            repo, {"file1.txt": "Modified on master", "master.txt": "Master work"}
        )
        master_commit_oid = repo.create_commit(
            "refs/heads/master",
            sig4,
            sig4,
            "Master branch work",
            tree_id,
            [commit1_oid],
        )

        # Create merge commit (3 hours later) - merge feature into master
        sig5 = pygit2.Signature(
            "Test User", "test@example.com", time=base_time + 10800, offset=offset
        )

        # For the merge, we need to create a tree that combines both branches
        tree_id = _create_tree_with_files(
            repo,
            {
                "file1.txt": "Modified on master",
                "feature.txt": "More feature work",
                "master.txt": "Master work",
            },
        )
        repo.create_commit(
            "refs/heads/master",
            sig5,
            sig5,
            "Merge feature branch",
            tree_id,
            [master_commit_oid, feature_commit2_oid],  # Two parents = merge commit
        )

        yield repo


def test_merge_commits_skip(repo_with_merge: pygit2.Repository) -> None:
    """Test that merge commits are skipped by default"""
    fetcher = GitFetcher(repo_with_merge.workdir)
    commits = list(fetcher.fetch_commits(skip_merge_commits=True))

    messages = [c.message for c in commits]
    # Should have all commits except the merge, in chronological order (newest first)
    assert messages == [
        "Master branch work",
        "Improve feature",
        "Add feature work",
        "Initial commit",
    ]


def test_merge_commits_included(repo_with_merge: pygit2.Repository) -> None:
    """Test that merge commits are included when skip_merge_commits=False"""
    fetcher = GitFetcher(repo_with_merge.workdir)
    commits = list(fetcher.fetch_commits(skip_merge_commits=False))

    messages = [c.message for c in commits]
    # Should have all commits including the merge, in chronological order
    assert messages == [
        "Merge feature branch",
        "Master branch work",
        "Improve feature",
        "Add feature work",
        "Initial commit",
    ]

    # Verify the merge commit has two parents
    merge_commit = commits[0]
    assert len(merge_commit.parents) == 2


def test_unravel_merges(repo_with_merge: pygit2.Repository) -> None:
    """Test unraveling merge commits to get child commits"""
    fetcher = GitFetcher(repo_with_merge.workdir)
    commits = list(fetcher.fetch_commits(unravel_merges=True, skip_merge_commits=False))

    messages = [c.message for c in commits]
    print(f"Commits with unravel_merges=True: {messages}")

    # When unraveling, merge commit is replaced by its children
    # Order: unraveled children first, then continue walking
    assert messages == [
        "Improve feature",
        "Add feature work",
        "Master branch work",
        "Initial commit",
    ]


def test_stop_commit(temp_repo: pygit2.Repository) -> None:
    """Test stopping at a specific commit SHA"""
    fetcher = GitFetcher(temp_repo.workdir)

    # First, get all commits to find the middle one
    all_commits = list(fetcher.fetch_commits(skip_merge_commits=False))
    assert len(all_commits) == 3

    # Use the middle commit as stop point
    stop_at_sha = all_commits[1].sha  # "Add file2 and modify file1"

    # Fetch with stop_commit - should get only commits AFTER the stop commit
    commits = list(
        fetcher.fetch_commits(stop_commit=stop_at_sha, skip_merge_commits=False)
    )

    # Should only get the first commit (most recent), not the stop commit or anything before it
    assert len(commits) == 1
    assert commits[0].message == "Add file3"
    assert stop_at_sha not in [c.sha for c in commits]


def test_stop_commit_with_unravel_merges(repo_with_merge: pygit2.Repository) -> None:
    """Test that unravel_merges includes feature commits even when they're before stop_commit chronologically

    Scenario: Feature branch commits were created early (1-2 hours after initial),
    but the merge happened later (3 hours). If we stop at "Master branch work" (2.5 hours),
    the feature commits should STILL be included because they're part of a merge
    that happened after the stop commit.
    """
    fetcher = GitFetcher(repo_with_merge.workdir)

    # Get all commits to understand the timeline
    all_commits = list(fetcher.fetch_commits(skip_merge_commits=False))

    # Find "Master branch work" commit to use as stop point
    master_work_commit = next(
        c for c in all_commits if c.message == "Master branch work"
    )
    stop_at_sha = master_work_commit.sha

    # Fetch with stop_commit AND unravel_merges
    commits = list(
        fetcher.fetch_commits(
            stop_commit=stop_at_sha, unravel_merges=True, skip_merge_commits=False
        )
    )

    messages = [c.message for c in commits]
    print(f"Commits with stop_commit={stop_at_sha[:8]} and unravel_merges=True:")
    print(f"  {messages}")

    # Should only get the unraveled feature commits (merge happens after stop_commit)
    assert messages == ["Improve feature", "Add feature work"]


def test_skip_merge_commits_with_unravel_false(
    repo_with_merge: pygit2.Repository,
) -> None:
    """Test skip_merge_commits=True with unravel_merges=False

    Should skip merge commits entirely without unraveling them.
    """
    fetcher = GitFetcher(repo_with_merge.workdir)
    commits = list(fetcher.fetch_commits(skip_merge_commits=True, unravel_merges=False))

    messages = [c.message for c in commits]
    print(f"Commits with skip_merge_commits=True, unravel_merges=False: {messages}")

    # Should skip merge but still traverse to feature commits
    assert messages == [
        "Master branch work",
        "Improve feature",
        "Add feature work",
        "Initial commit",
    ]


def test_skip_and_unravel_both_true(repo_with_merge: pygit2.Repository) -> None:
    """Test skip_merge_commits=True with unravel_merges=True

    Should unravel merge commits (return child commits) but NOT return the merge commit itself.
    This is the key test for the interaction between these two flags.
    """
    fetcher = GitFetcher(repo_with_merge.workdir)
    commits = list(fetcher.fetch_commits(skip_merge_commits=True, unravel_merges=True))

    messages = [c.message for c in commits]
    print(f"Commits with skip_merge_commits=True, unravel_merges=True: {messages}")

    # Should unravel merge and include all non-merge commits, no duplicates
    assert messages == [
        "Improve feature",
        "Add feature work",
        "Master branch work",
        "Initial commit",
    ]


def test_skip_false_unravel_true(repo_with_merge: pygit2.Repository) -> None:
    """Test skip_merge_commits=False with unravel_merges=True

    Should unravel merge commits AND continue processing normally, which means
    the merge commit itself gets skipped (via the 'continue' in unravel logic).
    """
    fetcher = GitFetcher(repo_with_merge.workdir)
    commits = list(fetcher.fetch_commits(skip_merge_commits=False, unravel_merges=True))

    messages = [c.message for c in commits]
    print(f"Commits with skip_merge_commits=False, unravel_merges=True: {messages}")

    # Unravel logic uses 'continue' so merge commit doesn't appear
    # Same result as skip_and_unravel_both_true
    assert messages == [
        "Improve feature",
        "Add feature work",
        "Master branch work",
        "Initial commit",
    ]


def test_start_commit_not_at_head(temp_repo: pygit2.Repository) -> None:
    """Test starting from a commit that's not at the head"""
    fetcher = GitFetcher(temp_repo.workdir)

    # Get all commits first
    all_commits = list(fetcher.fetch_commits(skip_merge_commits=False))
    assert len(all_commits) == 3

    # Start from the middle commit (second in history, "Add file2 and modify file1")
    middle_commit_sha = all_commits[1].sha

    # Fetch starting from middle commit
    commits = list(
        fetcher.fetch_commits(start_commit=middle_commit_sha, skip_merge_commits=False)
    )

    # Should get middle commit and everything before it (not the most recent commit)
    assert len(commits) == 2
    assert commits[0].message == "Add file2 and modify file1"
    assert commits[1].message == "Initial commit"
    assert all_commits[0].sha not in [c.sha for c in commits]


def test_start_commit_with_stop_commit(temp_repo: pygit2.Repository) -> None:
    """Test using both start_commit and stop_commit together"""
    fetcher = GitFetcher(temp_repo.workdir)

    # Get all commits first
    all_commits = list(fetcher.fetch_commits(skip_merge_commits=False))
    assert len(all_commits) == 3

    # Start from middle commit and stop at initial commit
    start_sha = all_commits[1].sha  # "Add file2 and modify file1"
    stop_sha = all_commits[2].sha  # "Initial commit"

    # Fetch between start and stop
    commits = list(
        fetcher.fetch_commits(
            start_commit=start_sha, stop_commit=stop_sha, skip_merge_commits=False
        )
    )

    # Should only get the middle commit (starts at middle, stops before initial)
    assert len(commits) == 1
    assert commits[0].message == "Add file2 and modify file1"
    assert commits[0].sha == start_sha


def test_start_commit_on_merge_branch(repo_with_merge: pygit2.Repository) -> None:
    """Test starting from a commit on a feature branch (not the main branch head)"""
    fetcher = GitFetcher(repo_with_merge.workdir)

    # Get all commits to find feature branch commits
    all_commits = list(fetcher.fetch_commits(skip_merge_commits=False))

    # Find "Improve feature" commit (second feature commit)
    improve_feature = next(c for c in all_commits if c.message == "Improve feature")

    # Start from this commit
    commits = list(
        fetcher.fetch_commits(
            start_commit=improve_feature.sha, skip_merge_commits=False
        )
    )

    messages = [c.message for c in commits]
    print(f"Starting from 'Improve feature': {messages}")

    # Should get: Improve feature -> Add feature work -> Initial commit
    # (follows the parent chain, not the main branch)
    assert messages == [
        "Improve feature",
        "Add feature work",
        "Initial commit",
    ]
