"""Unit tests for incremental commit extraction with since_sha filtering.

TDD: These tests are written BEFORE implementation.
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock

# Add src to path for imports
_src_path = Path(__file__).parent.parent.parent.parent / "src"
if str(_src_path) not in sys.path:
    sys.path.insert(0, str(_src_path))

# Mock Hatchet before any imports
sys.modules['hatchet_client'] = MagicMock()

import pygit2


@pytest.fixture
def test_repo_with_commits(tmp_path):
    """Create a test repo with 5 commits and return repo + commit SHAs."""
    repo_path = tmp_path / "test_repo"
    repo_path.mkdir()
    repo = pygit2.init_repository(str(repo_path))

    # Configure user
    config = repo.config
    config["user.name"] = "Test User"
    config["user.email"] = "test@example.com"

    commit_shas = []

    for i in range(5):
        # Create/modify a file
        file_path = repo_path / "file.txt"
        file_path.write_text(f"Content {i}\n" + "x" * (i * 100))

        # Stage and commit
        repo.index.add("file.txt")
        repo.index.write()

        tree = repo.index.write_tree()

        sig = pygit2.Signature("Test User", "test@example.com")

        parents = [repo.head.target] if not repo.head_is_unborn else []

        commit_oid = repo.create_commit(
            "HEAD",
            sig, sig,
            f"Commit {i + 1}",
            tree,
            parents
        )
        commit_shas.append(str(commit_oid))

    return repo, commit_shas


class TestExtractCommitsSinceSha:
    """Tests for extract_commits with since_sha filtering."""

    def test_extract_all_when_no_since_sha(self, test_repo_with_commits):
        """Extract all commits when since_sha is None."""
        from analytics.pipeline.phases.extract import extract_commits

        repo, commit_shas = test_repo_with_commits  # 5 commits

        result = extract_commits(
            repo=repo,
            codebase_id="test-uuid",
            since_sha=None,
        )

        assert result.success
        assert result.total_commits == 5

    def test_extract_only_new_commits_since_sha(self, test_repo_with_commits):
        """Extract only commits after since_sha."""
        from analytics.pipeline.phases.extract import extract_commits

        repo, commit_shas = test_repo_with_commits  # 5 commits
        # commit_shas[2] is the 3rd commit (index 2)
        # Should return commits after commit 3: commits 4 and 5 (indices 3, 4) = 2 commits

        result = extract_commits(
            repo=repo,
            codebase_id="test-uuid",
            since_sha=commit_shas[2],  # 3rd commit
        )

        assert result.success
        assert result.total_commits == 2  # Only commits 4 and 5

    def test_extract_zero_when_since_sha_is_latest(self, test_repo_with_commits):
        """Extract zero commits when since_sha is the latest."""
        from analytics.pipeline.phases.extract import extract_commits

        repo, commit_shas = test_repo_with_commits

        result = extract_commits(
            repo=repo,
            codebase_id="test-uuid",
            since_sha=commit_shas[-1],  # Latest commit
        )

        assert result.success
        assert result.total_commits == 0

    def test_extract_all_when_since_sha_not_found(self, test_repo_with_commits):
        """Extract all commits when since_sha doesn't exist (force full rebuild)."""
        from analytics.pipeline.phases.extract import extract_commits

        repo, commit_shas = test_repo_with_commits

        result = extract_commits(
            repo=repo,
            codebase_id="test-uuid",
            since_sha="0" * 40,  # Non-existent SHA
        )

        assert result.success
        assert result.total_commits == 5  # All commits (fallback)

    def test_extract_one_commit_since_second_to_last(self, test_repo_with_commits):
        """Extract only the latest commit when since_sha is second-to-last."""
        from analytics.pipeline.phases.extract import extract_commits

        repo, commit_shas = test_repo_with_commits

        result = extract_commits(
            repo=repo,
            codebase_id="test-uuid",
            since_sha=commit_shas[-2],  # Second-to-last commit
        )

        assert result.success
        assert result.total_commits == 1  # Only the latest commit

    def test_extract_preserves_commit_data(self, test_repo_with_commits):
        """Extracted commits have full data regardless of since_sha."""
        from analytics.pipeline.phases.extract import extract_commits

        repo, commit_shas = test_repo_with_commits

        result = extract_commits(
            repo=repo,
            codebase_id="test-uuid",
            since_sha=commit_shas[2],  # Get 2 new commits
        )

        assert result.success
        assert len(result.commits) >= 2

        # Check commit data is complete
        for commit in result.commits:
            assert 'commit_sha' in commit
            assert 'author_email' in commit
            assert 'additions_lines' in commit
            assert 'addition_bytes' in commit


class TestExtractCommitsWithBranches:
    """Tests for incremental extraction with multiple branches."""

    def test_extract_since_sha_across_branches(self, tmp_path):
        """Extract new commits from all branches since checkpoint."""
        import pygit2
        from analytics.pipeline.phases.extract import extract_commits

        # Create repo with main branch
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()
        repo = pygit2.init_repository(str(repo_path))

        config = repo.config
        config["user.name"] = "Test User"
        config["user.email"] = "test@example.com"

        # Create 3 commits on main
        commit_shas = []
        for i in range(3):
            file_path = repo_path / "file.txt"
            file_path.write_text(f"Content {i}\n")
            repo.index.add("file.txt")
            repo.index.write()
            tree = repo.index.write_tree()
            sig = pygit2.Signature("Test User", "test@example.com")
            parents = [repo.head.target] if not repo.head_is_unborn else []
            commit_oid = repo.create_commit("HEAD", sig, sig, f"Commit {i}", tree, parents)
            commit_shas.append(str(commit_oid))

        checkpoint_sha = commit_shas[-1]  # Last commit is checkpoint

        # Create feature branch from main
        main_commit = repo.head.peel(pygit2.Commit)
        feature_branch = repo.branches.create("feature", main_commit)
        repo.checkout(feature_branch)

        # Add 2 commits on feature branch
        for i in range(2):
            file_path = repo_path / "feature.txt"
            file_path.write_text(f"Feature {i}\n")
            repo.index.add("feature.txt")
            repo.index.write()
            tree = repo.index.write_tree()
            sig = pygit2.Signature("Test User", "test@example.com")
            parents = [repo.head.target]
            commit_oid = repo.create_commit("HEAD", sig, sig, f"Feature {i}", tree, parents)
            commit_shas.append(str(commit_oid))

        # Extract since checkpoint - should only get feature branch commits
        result = extract_commits(
            repo=repo,
            codebase_id="test-uuid",
            since_sha=checkpoint_sha,
        )

        assert result.success
        assert result.total_commits == 2  # Only the 2 feature commits

