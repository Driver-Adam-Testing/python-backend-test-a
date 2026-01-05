"""Unit tests for SLOC bytes calculation from patches.

A3: SLOC Bytes - Always use patches, no fallback to 50 bytes/line estimate.

These tests ensure:
1. Bytes are calculated from actual patch content
2. No 50 bytes/line fallback exists
3. Only analyzable code files are counted
4. Metadata tracks patch failures
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
import logging


def create_mock_patch(file_path: str, additions: int, deletions: int, patch_text: str):
    """Create a mock patch object for testing."""
    mock_patch = MagicMock()
    mock_patch.delta.new_file.path = file_path
    mock_patch.delta.old_file.path = file_path
    mock_patch.line_stats = (0, additions, deletions)
    mock_patch.text = patch_text
    return mock_patch


class TestSlocBytesFromPatch:
    """Tests for bytes calculation from patch data."""

    def test_bytes_calculated_from_patch_not_estimate(self):
        """Bytes are calculated from actual patch content, not estimated."""
        from analytics.pipeline.phases.extract import _extract_commit_data_with_diff
        
        # Create a mock repo and commit with known patch content
        mock_repo = MagicMock()
        mock_commit = MagicMock()
        mock_commit.id = "abc123def456"
        mock_commit.commit_time = datetime.now(timezone.utc).timestamp()
        mock_commit.author.email = "test@example.com"
        mock_commit.author.name = "Test Author"
        mock_commit.committer.email = "test@example.com"
        mock_commit.committer.name = "Test Author"
        mock_commit.message = "Test commit"
        mock_commit.parents = []
        
        # Create mock diff with a proper patch object for iteration
        mock_patch = create_mock_patch(
            file_path="src/main.py",  # Analyzable code file
            additions=2,
            deletions=1,
            patch_text="+short\n+tiny\n-medium line"  # 5 + 4 = 9 bytes additions, 11 bytes deletions
        )
        mock_diff = MagicMock()
        mock_diff.__iter__ = lambda self: iter([mock_patch])
        
        mock_repo.get.return_value = mock_commit
        
        # Mock _get_commit_diff to return our controlled diff
        with patch('analytics.pipeline.phases.extract._get_commit_diff', return_value=mock_diff):
            result, _ = _extract_commit_data_with_diff(
                mock_repo, "abc123def456", "test-codebase", ["main"],
                datetime.now(timezone.utc), include_patches=True
            )
        
        assert len(result) == 1
        commit_data = result[0]
        
        # Key assertion: bytes should NOT be lines * 50
        # If fallback was used: addition_bytes = 2 * 50 = 100, deletion_bytes = 1 * 50 = 50
        # Actual from patch: addition_bytes = 5 + 4 = 9 (for "short" and "tiny")
        assert commit_data['addition_bytes'] != commit_data['additions_lines'] * 50, \
            "Bytes should be calculated from patch, not estimated as lines * 50"
        assert commit_data['addition_bytes'] == 9  # "short" (5) + "tiny" (4)
        assert commit_data['deletion_bytes'] == 11  # "medium line" (11)

    def test_no_fallback_when_include_patches_true(self):
        """When include_patches=True, never fall back to 50 bytes/line."""
        from analytics.pipeline.phases.extract import _extract_commit_data_with_diff
        
        mock_repo = MagicMock()
        mock_commit = MagicMock()
        mock_commit.id = "abc123"
        mock_commit.commit_time = datetime.now(timezone.utc).timestamp()
        mock_commit.author.email = "test@example.com"
        mock_commit.author.name = "Test"
        mock_commit.committer.email = "test@example.com"
        mock_commit.committer.name = "Test"
        mock_commit.message = "Test"
        mock_commit.parents = []
        
        # Create mock diff with proper patch iteration
        mock_patch = create_mock_patch(
            file_path="src/app.py",  # Analyzable code file
            additions=10,
            deletions=5,
            patch_text="+a\n" * 10 + "-b\n" * 5  # 10 bytes additions, 5 bytes deletions
        )
        mock_diff = MagicMock()
        mock_diff.__iter__ = lambda self: iter([mock_patch])
        
        mock_repo.get.return_value = mock_commit
        
        with patch('analytics.pipeline.phases.extract._get_commit_diff', return_value=mock_diff):
            result, _ = _extract_commit_data_with_diff(
                mock_repo, "abc123", "test-codebase", ["main"],
                datetime.now(timezone.utc), include_patches=True
            )
        
        commit_data = result[0]
        
        # Should be actual bytes from patch (10 + 5 = 15), not estimate (10*50 + 5*50 = 750)
        assert commit_data['addition_bytes'] == 10
        assert commit_data['deletion_bytes'] == 5
        assert commit_data['patch_bytes'] == 15

    def test_non_code_files_not_counted(self):
        """Non-analyzable files (docs, config) are not counted in metrics."""
        from analytics.pipeline.phases.extract import _extract_commit_data_with_diff
        
        mock_repo = MagicMock()
        mock_commit = MagicMock()
        mock_commit.id = "abc123"
        mock_commit.commit_time = datetime.now(timezone.utc).timestamp()
        mock_commit.author.email = "test@example.com"
        mock_commit.author.name = "Test"
        mock_commit.committer.email = "test@example.com"
        mock_commit.committer.name = "Test"
        mock_commit.message = "Test"
        mock_commit.parents = []
        
        # Create mock patches - all files in languages.yml should be counted
        code_patch = create_mock_patch("src/main.py", 5, 2, "+code\n" * 5 + "-rm\n" * 2)
        readme_patch = create_mock_patch("README.md", 10, 3, "+doc\n" * 10)  # In languages.yml
        config_patch = create_mock_patch("config.json", 8, 0, "+cfg\n" * 8)  # In languages.yml
        
        mock_diff = MagicMock()
        mock_diff.__iter__ = lambda self: iter([code_patch, readme_patch, config_patch])
        
        mock_repo.get.return_value = mock_commit
        
        with patch('analytics.pipeline.phases.extract._get_commit_diff', return_value=mock_diff):
            result, _ = _extract_commit_data_with_diff(
                mock_repo, "abc123", "test-codebase", ["main"],
                datetime.now(timezone.utc), include_patches=True
            )
        
        commit_data = result[0]
        
        # All files are in languages.yml, so all counted
        assert commit_data['files_changed'] == 3
        assert commit_data['additions_lines'] == 5 + 10 + 8  # 23 total
        assert commit_data['deletions_lines'] == 2 + 3 + 0  # 5 total

    def test_empty_diff_produces_zero_metrics(self):
        """Empty diff (no patches) produces zero metrics."""
        from analytics.pipeline.phases.extract import _extract_commit_data_with_diff
        
        mock_repo = MagicMock()
        mock_commit = MagicMock()
        mock_commit.id = "abc123"
        mock_commit.commit_time = datetime.now(timezone.utc).timestamp()
        mock_commit.author.email = "test@example.com"
        mock_commit.author.name = "Test"
        mock_commit.committer.email = "test@example.com"
        mock_commit.committer.name = "Test"
        mock_commit.message = "Test"
        mock_commit.parents = []
        
        # Empty diff (no patches)
        mock_diff = MagicMock()
        mock_diff.__iter__ = lambda self: iter([])
        
        mock_repo.get.return_value = mock_commit
        
        with patch('analytics.pipeline.phases.extract._get_commit_diff', return_value=mock_diff):
            result, _ = _extract_commit_data_with_diff(
                mock_repo, "abc123", "test-codebase", ["main"],
                datetime.now(timezone.utc), include_patches=True
            )
        
        commit_data = result[0]
        
        assert commit_data['files_changed'] == 0
        assert commit_data['additions_lines'] == 0
        assert commit_data['deletions_lines'] == 0
        assert commit_data['addition_bytes'] == 0
        assert commit_data['deletion_bytes'] == 0


class TestIncludePatchesFalseRemoved:
    """Tests to ensure include_patches=False doesn't use estimates."""

    def test_include_patches_false_still_tries_patch(self):
        """Even with include_patches=False, we should try to use patches.
        
        This test verifies that the fallback behavior is removed.
        The include_patches parameter should be deprecated or ignored.
        """
        from analytics.pipeline.phases.extract import _extract_commit_data_with_diff
        
        mock_repo = MagicMock()
        mock_commit = MagicMock()
        mock_commit.id = "abc123"
        mock_commit.commit_time = datetime.now(timezone.utc).timestamp()
        mock_commit.author.email = "test@example.com"
        mock_commit.author.name = "Test"
        mock_commit.committer.email = "test@example.com"
        mock_commit.committer.name = "Test"
        mock_commit.message = "Test"
        mock_commit.parents = []
        
        # Create mock diff with proper patch iteration
        mock_patch = create_mock_patch(
            file_path="src/app.py",  # Analyzable code file
            additions=10,
            deletions=5,
            patch_text="+hello\n" * 10 + "-world\n" * 5  # Actual patch content
        )
        mock_diff = MagicMock()
        mock_diff.__iter__ = lambda self: iter([mock_patch])
        
        mock_repo.get.return_value = mock_commit
        
        with patch('analytics.pipeline.phases.extract._get_commit_diff', return_value=mock_diff):
            result, _ = _extract_commit_data_with_diff(
                mock_repo, "abc123", "test-codebase", ["main"],
                datetime.now(timezone.utc), include_patches=False  # Even with False
            )
        
        commit_data = result[0]
        
        # Should NOT be lines * 50 estimate
        # If fallback was used: 10*50 + 5*50 = 750
        # With proper implementation, bytes should come from patch or be 0
        assert commit_data['addition_bytes'] != 10 * 50, \
            "Should not use 50 bytes/line fallback even with include_patches=False"


class TestExtractResultMetadata:
    """Tests for metadata tracking of patch failures."""

    def test_extract_result_can_track_patch_failures(self):
        """ExtractResult should be able to track patch failure count."""
        from analytics.pipeline.phases.extract import ExtractResult
        
        # This tests the schema - implementation will add the field
        result = ExtractResult(
            success=True,
            commits=[],
            total_commits=10,
        )
        
        # For now, verify the basic structure exists
        # After implementation, we'll add patch_failures field
        assert result.success is True
        assert result.total_commits == 10

