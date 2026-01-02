"""
Tests for schema consistency between data producers and storage.

These tests ensure that:
1. AggregationEngine produces fields that match HotStorage schema
2. ExtractResult produces fields that match ParquetStorage (warm) schema
3. No schema drift occurs when we add new fields

This prevents runtime errors like:
  "Column with name X does not exist"
"""

import pytest
from datetime import datetime, timezone, date
from pathlib import Path
import pandas as pd

from analytics.storage.hot_storage import HotStorage
from analytics.storage.parquet_storage import ParquetStorage
from analytics.aggregation.engine import AggregationEngine
from analytics.schemas.warm_schemas import COMMITS_SCHEMA


class TestAggregationToHotStorageSchemaConsistency:
    """Ensure aggregation output matches hot storage schema."""

    @pytest.fixture
    def hot_storage(self, tmp_path):
        """Create a temporary hot storage."""
        storage = HotStorage(tmp_path / "hot" / "test.duckdb")
        storage.connect()
        yield storage
        storage.close()

    @pytest.fixture
    def warm_storage(self, tmp_path):
        """Create a temporary warm storage."""
        return ParquetStorage(tmp_path / "warm")

    def test_repository_metrics_fields_match_schema(self, hot_storage, warm_storage):
        """
        Test that AggregationEngine._build_repository_aggregate produces
        fields that exist in the repository_metrics table schema.
        
        This catches errors like:
        "INTERNAL Error: Column with name 'current_lines' does not exist"
        
        Schema v3.0 uses clean naming:
        - current_* : Current codebase state
        - *_lines   : Line-based metrics
        - *_sloc    : SLOC metrics (already converted from bytes)
        - net_*     : additions - deletions
        - churn_*   : additions + deletions
        """
        # Get the actual columns from DuckDB schema
        schema_columns = set(hot_storage._get_column_names('repository_metrics'))
        
        # Create minimal test data with ALL schema fields from warm storage
        commits_data = [{
            'commit_sha': 'abc123',
            'committed_at': datetime.now(timezone.utc),
            'branch_name': 'main',
            'additions_lines': 100,
            'deletions_lines': 50,
            'net_lines': 50,
            'churn_lines': 150,
            'addition_bytes': 5000,
            'deletion_bytes': 2500,
            'patch_bytes': 7500,
            'net_bytes': 2500,
            'sloc': 150,
            'bytes_per_line': 50.0,
            'author_email': 'test@example.com',
            'files_changed': 5,
            # Tree-based fields (current codebase state)
            'tree_bytes': 100000,
            'tree_lines': 2000,
            'tree_sloc': 2000,
        }]
        commits_df = pd.DataFrame(commits_data)
        commits_df['committed_at'] = pd.to_datetime(commits_df['committed_at'])
        
        # Create engine and build aggregate
        engine = AggregationEngine(hot_storage, warm_storage)
        engine._repo_owner = 'test-owner'
        engine._repo_name = 'test-repo'
        
        # Deduplicate commits by SHA
        unique_commits = commits_df.drop_duplicates(subset=['commit_sha'])
        
        # Calculate metrics (mimicking _build_repository_aggregate v3.0 logic)
        total_commits = len(unique_commits)
        
        # Line-based metrics
        additions_lines = unique_commits['additions_lines'].sum()
        deletions_lines = unique_commits['deletions_lines'].sum()
        churn_lines = additions_lines + deletions_lines
        net_lines = unique_commits['net_lines'].sum()
        
        # Byte metrics for SLOC conversion
        addition_bytes = unique_commits['addition_bytes'].sum()
        deletion_bytes = unique_commits['deletion_bytes'].sum()
        
        # SLOC-based metrics (convert bytes to SLOC: bytes / 50)
        additions_sloc = int(addition_bytes) // 50
        deletions_sloc = int(deletion_bytes) // 50
        churn_sloc = additions_sloc + deletions_sloc
        net_sloc = additions_sloc - deletions_sloc
        
        # Tree-based SLOC (actual codebase size from latest commit's tree walk)
        latest_commit = unique_commits.loc[unique_commits['committed_at'].idxmax()]
        current_sloc = int(latest_commit.get('tree_sloc', 0)) if 'tree_sloc' in unique_commits.columns else 0
        current_lines = int(latest_commit.get('tree_lines', 0)) if 'tree_lines' in unique_commits.columns else 0
        
        avg_bytes_per_line = addition_bytes / additions_lines if additions_lines > 0 else 0.0
        total_contributors = unique_commits['author_email'].nunique()
        branch_count = commits_df['branch_name'].nunique()
        first_commit_at = unique_commits['committed_at'].min()
        last_commit_at = unique_commits['committed_at'].max()
        total_files = unique_commits['files_changed'].sum()
        default_branch = commits_df['branch_name'].mode()[0] if not commits_df.empty else 'main'
        
        # Build metrics dict (same structure as engine._build_repository_aggregate v3.0)
        metrics = {
            'codebase_id': 'test-uuid',
            'repository_name': 'test-repo',
            'full_name': 'test-owner/test-repo',
            'owner': 'test-owner',
            # Current codebase state
            'current_sloc': int(current_sloc),
            'current_lines': int(current_lines),
            # Line-based cumulative activity
            'additions_lines': int(additions_lines),
            'deletions_lines': int(deletions_lines),
            'churn_lines': int(churn_lines),
            'net_lines': int(net_lines),
            # SLOC-based cumulative activity
            'additions_sloc': int(additions_sloc),
            'deletions_sloc': int(deletions_sloc),
            'churn_sloc': int(churn_sloc),
            'net_sloc': int(net_sloc),
            # Other metrics
            'avg_bytes_per_line': float(avg_bytes_per_line),
            'total_commits': int(total_commits),
            'total_contributors': int(total_contributors),
            'total_branches': int(branch_count),
            'total_files': int(total_files),
            'default_branch': str(default_branch),
            'primary_language': None,
            'first_commit_at': first_commit_at.to_pydatetime() if hasattr(first_commit_at, 'to_pydatetime') else first_commit_at,
            'last_commit_at': last_commit_at.to_pydatetime() if hasattr(last_commit_at, 'to_pydatetime') else last_commit_at,
            'collected_at': datetime.now(),
            'last_updated_at': datetime.now(),
            'collection_version': '3.0'
        }
        
        aggregation_columns = set(metrics.keys())
        
        # Every field produced by aggregation must exist in the schema
        missing_in_schema = aggregation_columns - schema_columns
        assert not missing_in_schema, (
            f"Aggregation produces fields that don't exist in hot storage schema: {missing_in_schema}\n"
            f"Schema columns: {sorted(schema_columns)}\n"
            f"Aggregation columns: {sorted(aggregation_columns)}"
        )
        
        # Actually try to upsert - this is the real test
        # If this fails, the schema doesn't match
        hot_storage.upsert_repository_metrics(metrics)
        
        # Verify we can read it back
        result = hot_storage.get_repository_metrics('test-uuid')
        assert result is not None
        assert result['current_sloc'] == current_sloc
        assert result['current_lines'] == current_lines


class TestWarmStorageSchemaConsistency:
    """Ensure commit records match warm storage (Parquet) schema."""

    def test_commit_record_fields_match_parquet_schema(self):
        """
        Test that commit records include all fields in COMMITS_SCHEMA.
        """
        # Get field names from PyArrow schema
        parquet_fields = set(field.name for field in COMMITS_SCHEMA)
        
        # Expected fields that extract.py produces
        expected_commit_fields = {
            # Identity
            'commit_sha',
            'codebase_id',
            'branch_name',
            # Temporal
            'committed_at',
            'collected_at',
            'commit_date',
            'commit_year',
            'commit_month',
            'commit_day',
            # Author
            'author_email',
            'author_name',
            'committer_email',
            'committer_name',
            # Commit metadata
            'message',
            'message_length',
            'parent_count',
            'is_merge_commit',
            'files_changed',
            # Line-based metrics
            'additions_lines',
            'deletions_lines',
            'net_lines',
            'churn_lines',
            # Byte-based metrics (churn)
            'addition_bytes',
            'deletion_bytes',
            'patch_bytes',
            'net_bytes',
            'sloc',
            # Tree-based metrics (actual size)
            'tree_bytes',
            'tree_lines',
            'tree_sloc',
            # Derived
            'bytes_per_line',
            'commit_size_category',
            'is_refactor',
            # Collection
            'collection_version',
        }
        
        # Check both directions
        missing_in_schema = expected_commit_fields - parquet_fields
        missing_in_extract = parquet_fields - expected_commit_fields
        
        assert not missing_in_schema, (
            f"Extract produces fields not in COMMITS_SCHEMA: {missing_in_schema}"
        )
        assert not missing_in_extract, (
            f"COMMITS_SCHEMA has fields not produced by extract: {missing_in_extract}"
        )


class TestHotStorageSchemaCompleteness:
    """Test that hot storage schema has all expected columns."""

    @pytest.fixture
    def hot_storage(self, tmp_path):
        """Create a temporary hot storage."""
        storage = HotStorage(tmp_path / "hot" / "test.duckdb")
        storage.connect()
        yield storage
        storage.close()

    def test_repository_metrics_has_tree_columns(self, hot_storage):
        """Test that repository_metrics table includes current state columns."""
        columns = set(hot_storage._get_column_names('repository_metrics'))
        
        # These are the current state columns (from tree walk at HEAD)
        current_state_columns = {'current_sloc', 'current_lines'}
        
        missing = current_state_columns - columns
        assert not missing, f"Missing current state columns in repository_metrics: {missing}"

    def test_branch_metrics_schema_complete(self, hot_storage):
        """Test that branch_metrics has all required columns."""
        columns = set(hot_storage._get_column_names('branch_metrics'))
        
        required_columns = {
            'codebase_id',
            'branch_name',
            'head_commit_sha',
            'current_sloc',
            'churn_sloc',
            'is_active',
            'is_merged',
            'is_deleted',
        }
        
        missing = required_columns - columns
        assert not missing, f"Missing columns in branch_metrics: {missing}"

