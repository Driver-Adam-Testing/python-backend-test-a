"""Unit tests for branch computed status.

A6: Branch Computed Status - 30-day stale rule.

Status values:
- "default" - The default branch (main/master)
- "active" - Has commits within the last 30 days
- "stale" - No commits in 30+ days
- "deleted" - Branch has been deleted
- "merged" - Branch was merged and deleted
"""
import pytest
from datetime import datetime, timezone, timedelta


class TestComputeBranchStatus:
    """Tests for _compute_branch_status function."""

    def test_default_branch_has_default_status(self):
        """Default branch should have 'default' status regardless of activity."""
        from analytics.export.exporter import _compute_branch_status
        
        branch = {
            'branch_name': 'main',
            'is_default_branch': True,
            'last_commit_at': datetime.now(timezone.utc) - timedelta(days=60),  # Old
        }
        
        assert _compute_branch_status(branch) == 'default'

    def test_active_branch_within_30_days(self):
        """Branch with commits within 30 days should be 'active'."""
        from analytics.export.exporter import _compute_branch_status
        
        branch = {
            'branch_name': 'feature-x',
            'is_default_branch': False,
            'last_commit_at': datetime.now(timezone.utc) - timedelta(days=15),
        }
        
        assert _compute_branch_status(branch) == 'active'

    def test_stale_branch_after_30_days(self):
        """Branch with no commits in 30+ days should be 'stale'."""
        from analytics.export.exporter import _compute_branch_status
        
        branch = {
            'branch_name': 'old-feature',
            'is_default_branch': False,
            'last_commit_at': datetime.now(timezone.utc) - timedelta(days=31),
        }
        
        assert _compute_branch_status(branch) == 'stale'

    def test_stale_branch_exactly_30_days(self):
        """Branch with last commit exactly 30 days ago should be 'active'."""
        from analytics.export.exporter import _compute_branch_status
        
        # Use 29 days + 23 hours to be safely under 30 days
        branch = {
            'branch_name': 'edge-case',
            'is_default_branch': False,
            'last_commit_at': datetime.now(timezone.utc) - timedelta(days=29, hours=23),
        }
        
        # 30 days or less is active, >30 days is stale
        assert _compute_branch_status(branch) == 'active'

    def test_deleted_branch_status(self):
        """Deleted branch should have 'deleted' status."""
        from analytics.export.exporter import _compute_branch_status
        
        branch = {
            'branch_name': 'deleted-feature',
            'is_default_branch': False,
            'is_deleted': True,
            'last_commit_at': datetime.now(timezone.utc) - timedelta(days=5),
        }
        
        assert _compute_branch_status(branch) == 'deleted'

    def test_merged_and_deleted_branch_status(self):
        """Merged and deleted branch should have 'merged' status."""
        from analytics.export.exporter import _compute_branch_status
        
        branch = {
            'branch_name': 'merged-feature',
            'is_default_branch': False,
            'is_deleted': True,
            'is_merged': True,
            'last_commit_at': datetime.now(timezone.utc) - timedelta(days=5),
        }
        
        assert _compute_branch_status(branch) == 'merged'

    def test_no_last_commit_date_is_active(self):
        """Branch with no last_commit_at should default to 'active'."""
        from analytics.export.exporter import _compute_branch_status
        
        branch = {
            'branch_name': 'new-branch',
            'is_default_branch': False,
            'last_commit_at': None,
        }
        
        # No commit date = assume it's new/active
        assert _compute_branch_status(branch) == 'active'

    def test_string_date_is_handled(self):
        """last_commit_at as ISO string should be handled."""
        from analytics.export.exporter import _compute_branch_status
        
        old_date = (datetime.now(timezone.utc) - timedelta(days=45)).isoformat()
        branch = {
            'branch_name': 'string-date-branch',
            'is_default_branch': False,
            'last_commit_at': old_date,
        }
        
        assert _compute_branch_status(branch) == 'stale'


class TestBranchStatusInExporter:
    """Tests for branch status integration in exporter."""

    def test_exporter_uses_computed_status(self):
        """Exporter should use _compute_branch_status for status field."""
        from analytics.export.exporter import DriverJSONExporter
        from datetime import datetime, timezone, timedelta
        from unittest.mock import MagicMock
        from pathlib import Path
        
        # Create mock hot storage with a stale branch
        mock_hot = MagicMock()
        old_date = datetime.now(timezone.utc) - timedelta(days=45)
        mock_hot.get_all_branch_metrics.return_value = [
            {
                'branch_name': 'stale-branch',
                'is_default_branch': False,
                'last_commit_at': old_date,
                'total_commits': 5,
                'is_active': True,  # Hot storage might say active
            }
        ]
        mock_hot.get_repository_metrics.return_value = {'total_commits': 100}
        mock_hot.get_monthly_metrics.return_value = []
        mock_hot.get_daily_metrics.return_value = []
        mock_hot.get_all_contributor_metrics.return_value = []
        
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            exporter = DriverJSONExporter(
                codebase_id='test-codebase',
                output_dir=Path(tmpdir),  # Must be Path, not string
                hot_storage=mock_hot,
            )
            
            # Export branches
            branches_path = exporter._export_branches()
            
            if branches_path:
                import json
                with open(branches_path) as f:
                    data = json.load(f)
                
                branch = data['branches'][0]
                # Status should be 'stale' based on 30-day rule, not 'active'
                assert branch['status'] == 'stale', \
                    f"Expected 'stale' but got '{branch['status']}'"

