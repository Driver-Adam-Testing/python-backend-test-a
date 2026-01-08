"""Unit tests for branch lifecycle detection."""
import pytest
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass


class TestBranchDiffDetection:
    """Tests for branch diff detection between runs."""

    def test_detect_new_branch(self):
        """New branches are detected when in current but not previous."""
        from analytics.pipeline.orchestrator import _detect_branch_changes

        current = {"main", "feature-new"}
        previous = {"main"}

        result = _detect_branch_changes(current, previous)

        assert result.new_branches == {"feature-new"}
        assert result.deleted_branches == set()

    def test_detect_deleted_branch(self):
        """Deleted branches are detected when in previous but not current."""
        from analytics.pipeline.orchestrator import _detect_branch_changes

        current = {"main"}
        previous = {"main", "feature-old"}

        result = _detect_branch_changes(current, previous)

        assert result.deleted_branches == {"feature-old"}
        assert result.new_branches == set()

    def test_detect_multiple_changes(self):
        """Multiple new and deleted branches are detected."""
        from analytics.pipeline.orchestrator import _detect_branch_changes

        current = {"main", "feature-a", "feature-b"}
        previous = {"main", "feature-old-1", "feature-old-2"}

        result = _detect_branch_changes(current, previous)

        assert result.new_branches == {"feature-a", "feature-b"}
        assert result.deleted_branches == {"feature-old-1", "feature-old-2"}

    def test_no_changes(self):
        """No changes when branches match."""
        from analytics.pipeline.orchestrator import _detect_branch_changes

        current = {"main", "develop"}
        previous = {"main", "develop"}

        result = _detect_branch_changes(current, previous)

        assert result.new_branches == set()
        assert result.deleted_branches == set()

    def test_empty_previous(self):
        """All current branches are new when previous is empty."""
        from analytics.pipeline.orchestrator import _detect_branch_changes

        current = {"main", "feature"}
        previous = set()

        result = _detect_branch_changes(current, previous)

        assert result.new_branches == {"main", "feature"}
        assert result.deleted_branches == set()

    def test_empty_current(self):
        """All previous branches are deleted when current is empty."""
        from analytics.pipeline.orchestrator import _detect_branch_changes

        current = set()
        previous = {"main", "feature"}

        result = _detect_branch_changes(current, previous)

        assert result.new_branches == set()
        assert result.deleted_branches == {"main", "feature"}


class TestBranchDiffResult:
    """Tests for BranchDiffResult dataclass."""

    def test_branch_diff_result_creation(self):
        """BranchDiffResult can be created with sets."""
        from analytics.pipeline.orchestrator import BranchDiffResult

        result = BranchDiffResult(
            new_branches={"feature-a"},
            deleted_branches={"feature-old"},
        )

        assert result.new_branches == {"feature-a"}
        assert result.deleted_branches == {"feature-old"}


class TestMergeDetection:
    """Tests for merge detection logic."""

    def test_was_merged_returns_false_for_none_sha(self):
        """Returns False when branch_last_sha is None."""
        from analytics.pipeline.orchestrator import _was_merged

        # Mock repo - not needed since we short-circuit on None SHA
        result = _was_merged(None, None, "main")

        assert result is False

    def test_was_merged_handles_invalid_repo(self):
        """Returns False gracefully when repo is invalid."""
        from analytics.pipeline.orchestrator import _was_merged

        result = _was_merged(None, "abc123", "main")

        assert result is False


class TestDeletedBranchProcessing:
    """Tests for processing deleted branches."""

    def test_build_deleted_branch_entry(self):
        """Deleted branch entry has correct structure."""
        from analytics.pipeline.orchestrator import _build_deleted_branch_entry

        now = datetime.now(timezone.utc)
        entry = _build_deleted_branch_entry(
            branch_name="feature-old",
            previous_branch_data={
                "name": "feature-old",
                "head_commit_sha": "abc123",
                "commits": 10,
                "last_commit_date": now.isoformat(),
            },
            is_merged=True,
        )

        assert entry["name"] == "feature-old"
        assert entry["is_deleted"] is True
        assert entry["is_merged"] is True
        assert entry["deleted_at"] is not None
        assert entry["merged_at"] is not None

    def test_build_deleted_branch_entry_not_merged(self):
        """Non-merged deleted branch has no merged_at."""
        from analytics.pipeline.orchestrator import _build_deleted_branch_entry

        entry = _build_deleted_branch_entry(
            branch_name="stale-feature",
            previous_branch_data={
                "name": "stale-feature",
                "head_commit_sha": "def456",
                "commits": 5,
            },
            is_merged=False,
        )

        assert entry["name"] == "stale-feature"
        assert entry["is_deleted"] is True
        assert entry["is_merged"] is False
        assert entry["deleted_at"] is not None
        assert entry["merged_at"] is None

