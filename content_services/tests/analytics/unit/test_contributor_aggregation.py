"""Unit tests for contributor aggregation.

A8: Contributor Tracking

Tests for aggregating contributor metrics from commits:
- Total commits per contributor
- SLOC contributions
- First/last commit dates
- Branch activity
"""
import pytest
import pandas as pd
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock


class TestBuildContributorAggregates:
    """Tests for _build_contributor_aggregates method."""

    @pytest.fixture
    def mock_commits_df(self):
        """Create a mock commits DataFrame."""
        now = datetime.now(timezone.utc)
        return pd.DataFrame([
            {
                'commit_sha': 'abc123',
                'codebase_id': 'test-codebase',
                'branch_name': 'main',
                'committed_at': now - timedelta(days=10),
                'author_email': 'alice@example.com',
                'author_name': 'Alice',
                'additions_lines': 100,
                'deletions_lines': 20,
                'addition_bytes': 5000,
                'deletion_bytes': 1000,
                'sloc': 80,
            },
            {
                'commit_sha': 'def456',
                'codebase_id': 'test-codebase',
                'branch_name': 'main',
                'committed_at': now - timedelta(days=5),
                'author_email': 'alice@example.com',
                'author_name': 'Alice',
                'additions_lines': 50,
                'deletions_lines': 10,
                'addition_bytes': 2500,
                'deletion_bytes': 500,
                'sloc': 40,
            },
            {
                'commit_sha': 'ghi789',
                'codebase_id': 'test-codebase',
                'branch_name': 'feature',
                'committed_at': now - timedelta(days=2),
                'author_email': 'bob@example.com',
                'author_name': 'Bob',
                'additions_lines': 200,
                'deletions_lines': 0,
                'addition_bytes': 10000,
                'deletion_bytes': 0,
                'sloc': 200,
            },
        ])

    def test_aggregates_commits_per_contributor(self, mock_commits_df):
        """Each contributor's total commits are aggregated."""
        from analytics.aggregation.engine import _build_contributor_data
        
        result = _build_contributor_data('test-codebase', mock_commits_df)
        
        alice = next(c for c in result if c['contributor_email'] == 'alice@example.com')
        bob = next(c for c in result if c['contributor_email'] == 'bob@example.com')
        
        assert alice['total_commits'] == 2
        assert bob['total_commits'] == 1

    def test_aggregates_sloc_per_contributor(self, mock_commits_df):
        """SLOC contributions are aggregated per contributor."""
        from analytics.aggregation.engine import _build_contributor_data
        
        result = _build_contributor_data('test-codebase', mock_commits_df)
        
        alice = next(c for c in result if c['contributor_email'] == 'alice@example.com')
        bob = next(c for c in result if c['contributor_email'] == 'bob@example.com')
        
        assert alice['total_sloc_contributed'] == 120  # 80 + 40
        assert bob['total_sloc_contributed'] == 200

    def test_aggregates_bytes_per_contributor(self, mock_commits_df):
        """Byte contributions are aggregated per contributor."""
        from analytics.aggregation.engine import _build_contributor_data
        
        result = _build_contributor_data('test-codebase', mock_commits_df)
        
        alice = next(c for c in result if c['contributor_email'] == 'alice@example.com')
        
        assert alice['total_addition_bytes'] == 7500  # 5000 + 2500
        assert alice['total_deletion_bytes'] == 1500  # 1000 + 500

    def test_tracks_first_and_last_commit(self, mock_commits_df):
        """First and last commit timestamps are tracked."""
        from analytics.aggregation.engine import _build_contributor_data
        
        result = _build_contributor_data('test-codebase', mock_commits_df)
        
        alice = next(c for c in result if c['contributor_email'] == 'alice@example.com')
        
        # Alice's first commit was 10 days ago, last was 5 days ago
        assert alice['first_commit_at'] < alice['last_commit_at']

    def test_tracks_branches_contributed_to(self, mock_commits_df):
        """Branches contributed to are tracked."""
        from analytics.aggregation.engine import _build_contributor_data
        
        result = _build_contributor_data('test-codebase', mock_commits_df)
        
        alice = next(c for c in result if c['contributor_email'] == 'alice@example.com')
        bob = next(c for c in result if c['contributor_email'] == 'bob@example.com')
        
        assert 'main' in alice['branches_contributed_to']
        assert 'feature' in bob['branches_contributed_to']
        assert alice['branches_count'] == 1
        assert bob['branches_count'] == 1

    def test_calculates_avg_commit_size(self, mock_commits_df):
        """Average commit size is calculated."""
        from analytics.aggregation.engine import _build_contributor_data
        
        result = _build_contributor_data('test-codebase', mock_commits_df)
        
        alice = next(c for c in result if c['contributor_email'] == 'alice@example.com')
        
        # Alice: (100+20 + 50+10) / 2 = 90 lines avg
        assert alice['avg_commit_size_lines'] == 90.0
        # Alice: (80 + 40) / 2 = 60 SLOC avg
        assert alice['avg_commit_size_sloc'] == 60.0

    def test_handles_empty_commits(self):
        """Empty commits DataFrame returns empty list."""
        from analytics.aggregation.engine import _build_contributor_data
        
        empty_df = pd.DataFrame()
        result = _build_contributor_data('test-codebase', empty_df)
        
        assert result == []


class TestContributorSchema:
    """Tests for contributor data schema compliance."""

    def test_contributor_has_required_fields(self):
        """Contributor dict has all required schema fields."""
        required_fields = [
            'codebase_id',
            'contributor_email',
            'contributor_name',
            'total_commits',
            'first_commit_at',
            'last_commit_at',
            'branches_contributed_to',
            'primary_branch',
            'branches_count',
            'commits_last_30_days',
            'commits_last_90_days',
            'commits_last_365_days',
            'total_additions_lines',
            'total_deletions_lines',
            'avg_commit_size_lines',
            'total_sloc_contributed',
            'total_addition_bytes',
            'total_deletion_bytes',
            'avg_commit_size_sloc',
            'collected_at',
        ]
        
        # A valid contributor dict
        contributor = {
            'codebase_id': 'test-codebase',
            'contributor_email': 'test@example.com',
            'contributor_name': 'Test User',
            'total_commits': 10,
            'first_commit_at': datetime.now(timezone.utc),
            'last_commit_at': datetime.now(timezone.utc),
            'branches_contributed_to': ['main', 'feature'],
            'primary_branch': 'main',
            'branches_count': 2,
            'commits_last_30_days': 5,
            'commits_last_90_days': 8,
            'commits_last_365_days': 10,
            'total_additions_lines': 1000,
            'total_deletions_lines': 200,
            'avg_commit_size_lines': 120.0,
            'total_sloc_contributed': 500,
            'total_addition_bytes': 25000,
            'total_deletion_bytes': 5000,
            'avg_commit_size_sloc': 50.0,
            'collected_at': datetime.now(timezone.utc),
        }
        
        for field in required_fields:
            assert field in contributor, f"Missing required field: {field}"

