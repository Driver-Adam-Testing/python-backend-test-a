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
    assert "Merge feature branch" not in messages
    # Should have: Master branch work, Improve feature, Add feature work, Initial commit
    assert len(commits) == 4


def test_merge_commits_included(repo_with_merge: pygit2.Repository) -> None:
    """Test that merge commits are included when skip_merge_commits=False"""
    fetcher = GitFetcher(repo_with_merge.workdir)
    commits = list(fetcher.fetch_commits(skip_merge_commits=False))

    messages = [c.message for c in commits]
    assert "Merge feature branch" in messages

    # Find the merge commit
    merge_commit = next(c for c in commits if c.message == "Merge feature branch")
    assert len(merge_commit.parents) == 2  # Should have two parents


def test_unravel_merges(repo_with_merge: pygit2.Repository) -> None:
    """Test unraveling merge commits to get child commits"""
    fetcher = GitFetcher(repo_with_merge.workdir)
    commits = list(fetcher.fetch_commits(unravel_merges=True, skip_merge_commits=False))

    messages = [c.message for c in commits]
    print(f"Commits with unravel_merges=True: {messages}")

    # With unravel_merges=True, we should get the feature branch commits
    assert "Add feature work" in messages
    assert "Improve feature" in messages

    # The merge commit itself should not appear (it's replaced by its children)
    assert "Merge feature branch" not in messages

    # We should NOT get duplicate commits from the mainline
    assert messages.count("Master branch work") == 1
    assert messages.count("Initial commit") == 1
