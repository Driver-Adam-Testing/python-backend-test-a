"""Unit tests for SLOC bytes calculation from patches.

A3: SLOC Bytes - Always use patches, no fallback to 50 bytes/line estimate.

These tests ensure:
1. Bytes are calculated from actual patch content
2. No 50 bytes/line fallback exists
3. Warnings are logged when patch analysis fails
4. Metadata tracks patch failures
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
import logging


class TestSlocBytesFromPatch:
    """Tests for bytes calculation from patch data."""

    def test_bytes_calculated_from_patch_not_estimate(self):
        """Bytes are calculated from actual patch content, not estimated."""
        from analytics.pipeline.phases.extract import _extract_commit_data
        
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
        
        # Create mock diff with specific patch content
        mock_diff = MagicMock()
        mock_diff.stats.files_changed = 1
        mock_diff.stats.insertions = 2  # 2 lines added
        mock_diff.stats.deletions = 1   # 1 line deleted
        # Patch with specific byte content (not 50 bytes per line)
        mock_diff.patch = "+short\n+tiny\n-medium line"  # 5 + 4 + 11 = different from 2*50 + 1*50
        
        mock_repo.get.return_value = mock_commit
        
        # Mock _get_commit_diff to return our controlled diff
        with patch('analytics.pipeline.phases.extract._get_commit_diff', return_value=mock_diff):
            result = _extract_commit_data(
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
        from analytics.pipeline.phases.extract import _extract_commit_data
        
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
        
        mock_diff = MagicMock()
        mock_diff.stats.files_changed = 1
        mock_diff.stats.insertions = 10
        mock_diff.stats.deletions = 5
        mock_diff.patch = "+a\n" * 10 + "-b\n" * 5  # 10 bytes additions, 5 bytes deletions
        
        mock_repo.get.return_value = mock_commit
        
        with patch('analytics.pipeline.phases.extract._get_commit_diff', return_value=mock_diff):
            result = _extract_commit_data(
                mock_repo, "abc123", "test-codebase", ["main"],
                datetime.now(timezone.utc), include_patches=True
            )
        
        commit_data = result[0]
        
        # Should be actual bytes from patch (10 + 5 = 15), not estimate (10*50 + 5*50 = 750)
        assert commit_data['addition_bytes'] == 10
        assert commit_data['deletion_bytes'] == 5
        assert commit_data['patch_bytes'] == 15

    def test_warning_logged_when_no_patch_data(self, caplog):
        """Warning is logged when patch is None or empty."""
        from analytics.pipeline.phases.extract import _extract_commit_data
        
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
        
        mock_diff = MagicMock()
        mock_diff.stats.files_changed = 1
        mock_diff.stats.insertions = 5
        mock_diff.stats.deletions = 2
        mock_diff.patch = None  # No patch data
        
        mock_repo.get.return_value = mock_commit
        
        with patch('analytics.pipeline.phases.extract._get_commit_diff', return_value=mock_diff):
            with caplog.at_level(logging.WARNING):
                result = _extract_commit_data(
                    mock_repo, "abc123", "test-codebase", ["main"],
                    datetime.now(timezone.utc), include_patches=True
                )
        
        # Should log a warning about missing patch data
        assert any("patch" in record.message.lower() or "no patch" in record.message.lower() 
                   for record in caplog.records), \
            "Should log warning when patch data is unavailable"
        
        # Bytes should be 0, not estimated
        commit_data = result[0]
        assert commit_data['addition_bytes'] == 0
        assert commit_data['deletion_bytes'] == 0

    def test_warning_logged_when_patch_analysis_fails(self, caplog):
        """Warning is logged when patch analysis raises exception."""
        from analytics.pipeline.phases.extract import _extract_commit_data
        
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
        
        mock_diff = MagicMock()
        mock_diff.stats.files_changed = 1
        mock_diff.stats.insertions = 5
        mock_diff.stats.deletions = 2
        # Make patch property raise an exception
        type(mock_diff).patch = property(lambda self: (_ for _ in ()).throw(Exception("Patch error")))
        
        mock_repo.get.return_value = mock_commit
        
        with patch('analytics.pipeline.phases.extract._get_commit_diff', return_value=mock_diff):
            with caplog.at_level(logging.WARNING):
                result = _extract_commit_data(
                    mock_repo, "abc123", "test-codebase", ["main"],
                    datetime.now(timezone.utc), include_patches=True
                )
        
        # Should log a warning about the failure
        assert any("patch" in record.message.lower() or "fail" in record.message.lower()
                   for record in caplog.records), \
            "Should log warning when patch analysis fails"
        
        # Bytes should be 0, not estimated
        commit_data = result[0]
        assert commit_data['addition_bytes'] == 0
        assert commit_data['deletion_bytes'] == 0


class TestIncludePatchesFalseRemoved:
    """Tests to ensure include_patches=False doesn't use estimates."""

    def test_include_patches_false_still_tries_patch(self):
        """Even with include_patches=False, we should try to use patches.
        
        This test verifies that the fallback behavior is removed.
        The include_patches parameter should be deprecated or ignored.
        """
        from analytics.pipeline.phases.extract import _extract_commit_data
        
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
        
        mock_diff = MagicMock()
        mock_diff.stats.files_changed = 1
        mock_diff.stats.insertions = 10
        mock_diff.stats.deletions = 5
        mock_diff.patch = "+hello\n" * 10 + "-world\n" * 5  # Actual patch content
        
        mock_repo.get.return_value = mock_commit
        
        with patch('analytics.pipeline.phases.extract._get_commit_diff', return_value=mock_diff):
            result = _extract_commit_data(
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

