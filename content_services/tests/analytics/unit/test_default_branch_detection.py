"""Unit tests for default branch detection.

Tests that _get_default_branch correctly identifies the default branch
using origin/HEAD reference (set by GitHub) before falling back to
common names or HEAD.
"""
import pytest
from unittest.mock import MagicMock, PropertyMock


class TestGetDefaultBranch:
    """Tests for _get_default_branch function."""

    def test_uses_origin_head_when_available(self):
        """Should use refs/remotes/origin/HEAD when it exists."""
        from analytics.pipeline.phases.branches import _get_default_branch
        
        # Mock a repository with origin/HEAD pointing to main
        mock_repo = MagicMock()
        mock_repo.head_is_unborn = False
        mock_repo.head.shorthand = "some-feature-branch"  # HEAD is on wrong branch
        
        # origin/HEAD reference pointing to main
        mock_origin_head = MagicMock()
        mock_origin_head.target = "refs/remotes/origin/main"
        mock_repo.references.get.return_value = mock_origin_head
        
        result = _get_default_branch(mock_repo)
        
        assert result == "main", f"Expected 'main', got '{result}'"
        mock_repo.references.get.assert_called_with("refs/remotes/origin/HEAD")

    def test_uses_origin_head_with_master(self):
        """Should correctly extract 'master' from origin/HEAD."""
        from analytics.pipeline.phases.branches import _get_default_branch
        
        mock_repo = MagicMock()
        mock_repo.head_is_unborn = False
        mock_repo.head.shorthand = "develop"
        
        mock_origin_head = MagicMock()
        mock_origin_head.target = "refs/remotes/origin/master"
        mock_repo.references.get.return_value = mock_origin_head
        
        result = _get_default_branch(mock_repo)
        
        assert result == "master"

    def test_falls_back_to_common_names_when_no_origin_head(self):
        """Should check main/master/develop when origin/HEAD doesn't exist."""
        from analytics.pipeline.phases.branches import _get_default_branch
        
        mock_repo = MagicMock()
        mock_repo.head_is_unborn = False
        mock_repo.head.shorthand = "feature-branch"
        mock_repo.references.get.return_value = None  # No origin/HEAD
        
        # Local branches include 'main'
        mock_repo.branches.local = ["feature-branch", "main", "develop"]
        
        result = _get_default_branch(mock_repo)
        
        assert result == "main"

    def test_prefers_main_over_master(self):
        """Should prefer 'main' over 'master' in fallback order."""
        from analytics.pipeline.phases.branches import _get_default_branch
        
        mock_repo = MagicMock()
        mock_repo.head_is_unborn = False
        mock_repo.head.shorthand = "feature"
        mock_repo.references.get.return_value = None
        
        # Both main and master exist
        mock_repo.branches.local = ["feature", "master", "main"]
        
        result = _get_default_branch(mock_repo)
        
        assert result == "main", "Should prefer 'main' over 'master'"

    def test_falls_back_to_head_when_no_common_names(self):
        """Should use HEAD when no common branch names exist."""
        from analytics.pipeline.phases.branches import _get_default_branch
        
        mock_repo = MagicMock()
        mock_repo.head_is_unborn = False
        mock_repo.head.shorthand = "trunk"  # Non-standard name
        mock_repo.references.get.return_value = None
        
        # No common names
        mock_repo.branches.local = ["trunk", "feature-1"]
        
        result = _get_default_branch(mock_repo)
        
        assert result == "trunk"

    def test_handles_origin_head_exception(self):
        """Should gracefully handle exceptions when reading origin/HEAD."""
        from analytics.pipeline.phases.branches import _get_default_branch
        
        mock_repo = MagicMock()
        mock_repo.head_is_unborn = False
        mock_repo.head.shorthand = "develop"
        mock_repo.references.get.side_effect = Exception("Failed to read ref")
        
        mock_repo.branches.local = ["develop", "main"]
        
        result = _get_default_branch(mock_repo)
        
        # Should fall back to common names
        assert result == "main"

    def test_ignores_origin_head_with_wrong_format(self):
        """Should ignore origin/HEAD if target format is unexpected."""
        from analytics.pipeline.phases.branches import _get_default_branch
        
        mock_repo = MagicMock()
        mock_repo.head_is_unborn = False
        mock_repo.head.shorthand = "feature"
        
        # origin/HEAD exists but has unexpected target format
        mock_origin_head = MagicMock()
        mock_origin_head.target = "not-a-valid-ref-format"  # No refs/remotes/origin/ prefix
        mock_repo.references.get.return_value = mock_origin_head
        
        mock_repo.branches.local = ["feature", "main"]
        
        result = _get_default_branch(mock_repo)
        
        # Should fall back to common names
        assert result == "main"

    def test_handles_non_string_target(self):
        """Should handle origin/HEAD with non-string target (OID)."""
        from analytics.pipeline.phases.branches import _get_default_branch
        
        mock_repo = MagicMock()
        mock_repo.head_is_unborn = False
        mock_repo.head.shorthand = "feature"
        
        # origin/HEAD with OID target (not symbolic ref)
        mock_origin_head = MagicMock()
        mock_origin_head.target = MagicMock()  # Not a string
        mock_repo.references.get.return_value = mock_origin_head
        
        mock_repo.branches.local = ["feature", "main"]
        
        result = _get_default_branch(mock_repo)
        
        # Should fall back to common names
        assert result == "main"


class TestDefaultBranchPriority:
    """Tests to ensure correct priority order."""

    def test_origin_head_takes_priority_over_head(self):
        """origin/HEAD should override what HEAD points to."""
        from analytics.pipeline.phases.branches import _get_default_branch
        
        mock_repo = MagicMock()
        mock_repo.head_is_unborn = False
        # HEAD is checked out to a dependabot branch (the original bug)
        mock_repo.head.shorthand = "dependabot/github_actions/actions/checkout-6.0.0"
        
        # But origin/HEAD correctly points to main
        mock_origin_head = MagicMock()
        mock_origin_head.target = "refs/remotes/origin/main"
        mock_repo.references.get.return_value = mock_origin_head
        
        result = _get_default_branch(mock_repo)
        
        # Should use origin/HEAD (main), NOT HEAD (dependabot branch)
        assert result == "main", \
            f"Expected 'main' from origin/HEAD, got '{result}' (possibly from HEAD)"

    def test_common_names_take_priority_over_head(self):
        """Common branch names should override HEAD when no origin/HEAD."""
        from analytics.pipeline.phases.branches import _get_default_branch
        
        mock_repo = MagicMock()
        mock_repo.head_is_unborn = False
        mock_repo.head.shorthand = "dependabot/something"
        mock_repo.references.get.return_value = None
        
        # main exists in local branches
        mock_repo.branches.local = ["dependabot/something", "main"]
        
        result = _get_default_branch(mock_repo)
        
        assert result == "main", \
            f"Expected 'main' from common names, got '{result}'"

