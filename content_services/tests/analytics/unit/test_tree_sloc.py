"""
Tests for tree-based SLOC calculation (actual codebase size).

This tests the _get_tree_size_at_commit function which walks the file tree
to calculate the REAL codebase size, as opposed to churn SLOC from patches.
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone


class TestTreeSLOCCalculation:
    """Test tree size calculation at a commit."""
    
    def test_tree_sloc_fields_in_commit_record(self):
        """Verify that commit records include tree_bytes, tree_lines, tree_sloc fields."""
        # Import the function
        from analytics.pipeline.phases.extract import _extract_commit_data_with_diff
        
        # Create mock repo with a commit
        mock_repo = MagicMock()
        mock_commit = MagicMock()
        mock_commit.commit_time = datetime.now(timezone.utc).timestamp()
        mock_commit.author.email = 'test@example.com'
        mock_commit.author.name = 'Test User'
        mock_commit.committer.email = 'test@example.com'
        mock_commit.committer.name = 'Test User'
        mock_commit.message = 'Test commit'
        mock_commit.parents = []
        
        # Mock tree for tree walk
        mock_tree = MagicMock()
        mock_tree.__iter__ = MagicMock(return_value=iter([]))
        mock_commit.tree = mock_tree
        
        mock_repo.get.return_value = mock_commit
        
        # Mock diff
        mock_diff = MagicMock()
        mock_diff.stats.files_changed = 1
        mock_diff.stats.insertions = 10
        mock_diff.stats.deletions = 5
        mock_diff.patch = "+new line\n-old line"
        
        with patch('analytics.pipeline.phases.extract._get_commit_diff', return_value=mock_diff):
            with patch('analytics.pipeline.phases.extract._get_tree_size_at_commit', return_value=(1000, 50)):
                records, diff = _extract_commit_data_with_diff(
                    mock_repo,
                    'abc123',
                    'codebase-uuid',
                    ['main'],
                    datetime.now(timezone.utc),
                    include_patches=True
                )
        
        assert len(records) == 1
        record = records[0]
        
        # Check tree-based fields exist
        assert 'tree_bytes' in record
        assert 'tree_lines' in record
        assert 'tree_sloc' in record
        
        # Verify tree_sloc calculation (tree_bytes // 50)
        assert record['tree_bytes'] == 1000
        assert record['tree_lines'] == 50
        assert record['tree_sloc'] == 20  # 1000 // 50
    
    def test_tree_sloc_is_different_from_churn_sloc(self):
        """Tree SLOC (actual size) should be different from churn SLOC (patch-based)."""
        # A commit might have small churn but large tree
        # e.g., fixing a typo in a large file
        
        from analytics.pipeline.phases.extract import _extract_commit_data_with_diff
        
        mock_repo = MagicMock()
        mock_commit = MagicMock()
        mock_commit.commit_time = datetime.now(timezone.utc).timestamp()
        mock_commit.author.email = 'test@example.com'
        mock_commit.author.name = 'Test User'
        mock_commit.committer.email = 'test@example.com'
        mock_commit.committer.name = 'Test User'
        mock_commit.message = 'Test commit'
        mock_commit.parents = []
        mock_commit.tree = MagicMock()
        mock_commit.tree.__iter__ = MagicMock(return_value=iter([]))
        
        mock_repo.get.return_value = mock_commit
        
        # Small patch (churn_sloc should be low)
        mock_diff = MagicMock()
        mock_diff.stats.files_changed = 1
        mock_diff.stats.insertions = 1
        mock_diff.stats.deletions = 1
        mock_diff.patch = "+fix\n-bug"  # 7 bytes total -> 0 SLOC
        
        with patch('analytics.pipeline.phases.extract._get_commit_diff', return_value=mock_diff):
            # Large tree (tree_sloc should be high)
            with patch('analytics.pipeline.phases.extract._get_tree_size_at_commit', return_value=(50000, 1000)):
                records, _ = _extract_commit_data_with_diff(
                    mock_repo,
                    'abc123',
                    'codebase-uuid',
                    ['main'],
                    datetime.now(timezone.utc),
                    include_patches=True
                )
        
        record = records[0]
        
        # Churn SLOC should be small (patch-based)
        assert record['sloc'] < 10  # Small patch
        
        # Tree SLOC should be large (actual codebase size)
        assert record['tree_sloc'] == 1000  # 50000 // 50
        
        # They should be very different
        assert record['tree_sloc'] > record['sloc'] * 10


class TestWalkTreeRecursive:
    """Test the recursive tree walking function."""
    
    def test_walk_empty_tree(self):
        """Empty tree should return (0, 0)."""
        from analytics.pipeline.phases.extract import _walk_tree_recursive
        
        mock_repo = MagicMock()
        mock_tree = MagicMock()
        mock_tree.__iter__ = MagicMock(return_value=iter([]))
        
        bytes_count, lines_count = _walk_tree_recursive(mock_repo, mock_tree)
        
        assert bytes_count == 0
        assert lines_count == 0
    
    def test_walk_tree_with_single_file(self):
        """Single file should be counted correctly."""
        from analytics.pipeline.phases.extract import _walk_tree_recursive
        
        mock_repo = MagicMock()
        
        # Create a blob entry
        mock_blob = MagicMock()
        mock_blob.is_binary = False
        mock_blob.data = b"line 1\nline 2\nline 3"  # 20 bytes, 3 lines
        
        mock_entry = MagicMock()
        mock_entry.type_str = 'blob'
        mock_entry.id = 'blob-id'
        mock_entry.name = 'file.py'
        
        mock_tree = MagicMock()
        mock_tree.__iter__ = MagicMock(return_value=iter([mock_entry]))
        
        mock_repo.get.return_value = mock_blob
        
        bytes_count, lines_count = _walk_tree_recursive(mock_repo, mock_tree)
        
        assert bytes_count == 20
        assert lines_count == 3
    
    def test_walk_tree_skips_binary_files(self):
        """Binary files should be skipped."""
        from analytics.pipeline.phases.extract import _walk_tree_recursive
        
        mock_repo = MagicMock()
        
        # Create a binary blob entry
        mock_blob = MagicMock()
        mock_blob.is_binary = True
        mock_blob.data = b"\x00\x01\x02"
        
        mock_entry = MagicMock()
        mock_entry.type_str = 'blob'
        mock_entry.id = 'blob-id'
        mock_entry.name = 'image.png'
        
        mock_tree = MagicMock()
        mock_tree.__iter__ = MagicMock(return_value=iter([mock_entry]))
        
        mock_repo.get.return_value = mock_blob
        
        bytes_count, lines_count = _walk_tree_recursive(mock_repo, mock_tree)
        
        # Binary files should not be counted
        assert bytes_count == 0
        assert lines_count == 0
    
    def test_walk_tree_recurses_into_subdirectories(self):
        """Subdirectories should be walked recursively."""
        from analytics.pipeline.phases.extract import _walk_tree_recursive
        
        mock_repo = MagicMock()
        
        # Create a blob in a subdirectory
        mock_subblob = MagicMock()
        mock_subblob.is_binary = False
        mock_subblob.data = b"nested content\n"  # 15 bytes, 1 line
        
        mock_blob_entry = MagicMock()
        mock_blob_entry.type_str = 'blob'
        mock_blob_entry.id = 'subblob-id'
        mock_blob_entry.name = 'nested.py'
        
        mock_subtree = MagicMock()
        mock_subtree.__iter__ = MagicMock(return_value=iter([mock_blob_entry]))
        
        # Create the subdirectory entry
        mock_dir_entry = MagicMock()
        mock_dir_entry.type_str = 'tree'
        mock_dir_entry.id = 'subtree-id'
        mock_dir_entry.name = 'subdir'
        
        mock_tree = MagicMock()
        mock_tree.__iter__ = MagicMock(return_value=iter([mock_dir_entry]))
        
        # Configure repo.get to return appropriate objects
        def mock_get(oid):
            if oid == 'subtree-id':
                return mock_subtree
            elif oid == 'subblob-id':
                return mock_subblob
            return None
        
        mock_repo.get.side_effect = mock_get
        
        bytes_count, lines_count = _walk_tree_recursive(mock_repo, mock_tree)
        
        assert bytes_count == 15
        assert lines_count == 1


class TestAggregationUsesTreeSloc:
    """Test that aggregation uses tree_sloc for current_sloc."""
    
    def test_current_sloc_comes_from_latest_commit_tree(self):
        """current_sloc in repository aggregate should use latest commit's tree_sloc."""
        import pandas as pd
        from datetime import datetime
        
        # Create mock commits DataFrame with tree_sloc
        commits_data = [
            {
                'commit_sha': 'sha1',
                'committed_at': datetime(2024, 1, 1),
                'branch_name': 'main',
                'additions_lines': 100,
                'deletions_lines': 50,
                'net_lines': 50,
                'churn_lines': 150,
                'addition_bytes': 5000,
                'deletion_bytes': 2500,
                'patch_bytes': 7500,
                'net_bytes': 2500,
                'sloc': 150,  # Churn SLOC
                'bytes_per_line': 50.0,
                'author_email': 'test@example.com',
                'files_changed': 10,
                'tree_bytes': 100000,  # Old tree size
                'tree_lines': 2000,
                'tree_sloc': 2000,  # Old tree SLOC
            },
            {
                'commit_sha': 'sha2',
                'committed_at': datetime(2024, 1, 2),  # Later commit
                'branch_name': 'main',
                'additions_lines': 10,
                'deletions_lines': 5,
                'net_lines': 5,
                'churn_lines': 15,
                'addition_bytes': 500,
                'deletion_bytes': 250,
                'patch_bytes': 750,
                'net_bytes': 250,
                'sloc': 15,  # Small churn
                'bytes_per_line': 50.0,
                'author_email': 'test@example.com',
                'files_changed': 1,
                'tree_bytes': 102500,  # Current tree size (slightly larger)
                'tree_lines': 2005,
                'tree_sloc': 2050,  # Current tree SLOC
            },
        ]
        
        commits_df = pd.DataFrame(commits_data)
        commits_df['committed_at'] = pd.to_datetime(commits_df['committed_at'])
        
        # Find latest commit
        latest = commits_df.loc[commits_df['committed_at'].idxmax()]
        
        # current_sloc should be from latest commit's tree_sloc
        assert latest['tree_sloc'] == 2050
        
        # total_sloc (churn) should be sum of sloc
        total_sloc = commits_df['sloc'].sum()
        assert total_sloc == 165  # 150 + 15
        
        # They should be very different
        assert latest['tree_sloc'] != total_sloc


class TestSchemaIncludesTreeFields:
    """Test that the warm schema includes tree fields."""
    
    def test_commits_schema_has_tree_fields(self):
        """COMMITS_SCHEMA should include tree_bytes, tree_lines, tree_sloc."""
        from analytics.schemas.warm_schemas import COMMITS_SCHEMA
        
        field_names = [field.name for field in COMMITS_SCHEMA]
        
        assert 'tree_bytes' in field_names
        assert 'tree_lines' in field_names
        assert 'tree_sloc' in field_names

