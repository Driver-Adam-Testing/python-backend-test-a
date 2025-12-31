"""Tests for analytics cleanup when codebase is deleted.

Run with: pytest app/api/routes/v2/test_primary_assets_analytics.py -v
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

# Add backend to path for imports
_backend_path = Path(__file__).parent.parent.parent.parent.parent
if str(_backend_path) not in sys.path:
    sys.path.insert(0, str(_backend_path))


class TestDeleteAnalyticsFolder:
    """Tests for _delete_analytics_folder helper."""

    def test_deletes_analytics_files(self):
        """Analytics folder is deleted when it exists."""
        codebase_id = str(uuid4())
        
        # Mock bucket
        mock_bucket = MagicMock()
        mock_objects = MagicMock()
        mock_bucket.objects.filter.return_value = mock_objects
        mock_objects.__iter__ = lambda self: iter([MagicMock()])  # Has objects
        
        _delete_analytics_folder(mock_bucket, codebase_id)
        
        mock_bucket.objects.filter.assert_called_with(Prefix=f"analytics/{codebase_id}/")
        mock_objects.delete.assert_called_once()

    def test_handles_empty_folder(self):
        """Gracefully handles when no analytics files exist."""
        codebase_id = str(uuid4())
        
        mock_bucket = MagicMock()
        mock_objects = MagicMock()
        mock_bucket.objects.filter.return_value = mock_objects
        mock_objects.__iter__ = lambda self: iter([])  # No objects
        
        # Should not raise
        _delete_analytics_folder(mock_bucket, codebase_id)
        
        mock_bucket.objects.filter.assert_called_with(Prefix=f"analytics/{codebase_id}/")

    def test_handles_s3_error(self):
        """Logs warning and continues on S3 error."""
        codebase_id = str(uuid4())
        
        mock_bucket = MagicMock()
        mock_bucket.objects.filter.side_effect = Exception("S3 error")
        
        # Should not raise
        _delete_analytics_folder(mock_bucket, codebase_id)


class TestUpdateOrgFilesAfterDeletion:
    """Tests for _update_org_files_after_deletion helper."""

    def test_removes_codebase_from_list(self):
        """Deleted codebase is removed from codebases_list.json."""
        codebase_id = str(uuid4())
        other_id = str(uuid4())
        organization_id = "test-org"
        bucket_name = "test-bucket"
        
        initial_list = {
            "organization_id": organization_id,
            "codebases": [
                {"codebase_id": codebase_id, "total_commits": 100, "current_sloc": 5000, "total_contributors": 10},
                {"codebase_id": other_id, "total_commits": 50, "current_sloc": 2000, "total_contributors": 5},
            ],
            "generated_at": "2024-01-01T00:00:00Z",
        }
        
        mock_client = MagicMock()
        mock_client.get_object.return_value = {
            'Body': MagicMock(read=lambda: json.dumps(initial_list).encode('utf-8'))
        }
        
        _update_org_files_after_deletion(mock_client, bucket_name, organization_id, codebase_id)
        
        # Verify codebases_list.json was updated
        list_call = [c for c in mock_client.put_object.call_args_list 
                     if c.kwargs.get('Key') == 'analytics/codebases_list.json'][0]
        updated_list = json.loads(list_call.kwargs['Body'])
        
        assert len(updated_list['codebases']) == 1
        assert updated_list['codebases'][0]['codebase_id'] == other_id

    def test_recomputes_org_summary(self):
        """Org summary is recomputed with correct totals."""
        codebase_id = str(uuid4())
        other_id = str(uuid4())
        organization_id = "test-org"
        bucket_name = "test-bucket"
        
        initial_list = {
            "organization_id": organization_id,
            "codebases": [
                {"codebase_id": codebase_id, "total_commits": 100, "current_sloc": 5000, "total_contributors": 10},
                {"codebase_id": other_id, "total_commits": 50, "current_sloc": 2000, "total_contributors": 5},
            ],
        }
        
        mock_client = MagicMock()
        mock_client.get_object.return_value = {
            'Body': MagicMock(read=lambda: json.dumps(initial_list).encode('utf-8'))
        }
        
        _update_org_files_after_deletion(mock_client, bucket_name, organization_id, codebase_id)
        
        # Verify org_summary.json was updated
        summary_call = [c for c in mock_client.put_object.call_args_list 
                        if c.kwargs.get('Key') == 'analytics/org_summary.json'][0]
        summary = json.loads(summary_call.kwargs['Body'])
        
        # Should only have "other" codebase stats
        assert summary['total_codebases'] == 1
        assert summary['total_commits'] == 50
        assert summary['total_sloc'] == 2000
        assert summary['total_contributors'] == 5

    def test_handles_missing_codebases_list(self):
        """Gracefully handles when codebases_list.json doesn't exist."""
        codebase_id = str(uuid4())
        organization_id = "test-org"
        bucket_name = "test-bucket"
        
        mock_client = MagicMock()
        mock_client.exceptions = MagicMock()
        mock_client.exceptions.NoSuchKey = type('NoSuchKey', (Exception,), {})
        mock_client.get_object.side_effect = mock_client.exceptions.NoSuchKey()
        
        # Should not raise
        _update_org_files_after_deletion(mock_client, bucket_name, organization_id, codebase_id)
        
        # Should not attempt to upload
        mock_client.put_object.assert_not_called()

    def test_handles_codebase_not_in_list(self):
        """Gracefully handles when codebase is not in the list."""
        codebase_id = str(uuid4())
        other_id = str(uuid4())
        organization_id = "test-org"
        bucket_name = "test-bucket"
        
        initial_list = {
            "organization_id": organization_id,
            "codebases": [
                {"codebase_id": other_id, "total_commits": 50},
            ],
        }
        
        mock_client = MagicMock()
        mock_client.get_object.return_value = {
            'Body': MagicMock(read=lambda: json.dumps(initial_list).encode('utf-8'))
        }
        
        # Should not raise
        _update_org_files_after_deletion(mock_client, bucket_name, organization_id, codebase_id)
        
        # Should not upload since nothing changed
        mock_client.put_object.assert_not_called()

    def test_handles_s3_read_error(self):
        """Gracefully handles S3 read errors."""
        codebase_id = str(uuid4())
        organization_id = "test-org"
        bucket_name = "test-bucket"
        
        mock_client = MagicMock()
        mock_client.get_object.side_effect = Exception("S3 error")
        
        # Should not raise
        _update_org_files_after_deletion(mock_client, bucket_name, organization_id, codebase_id)

    def test_handles_s3_write_error(self):
        """Gracefully handles S3 write errors."""
        codebase_id = str(uuid4())
        other_id = str(uuid4())
        organization_id = "test-org"
        bucket_name = "test-bucket"
        
        initial_list = {
            "organization_id": organization_id,
            "codebases": [
                {"codebase_id": codebase_id, "total_commits": 100},
                {"codebase_id": other_id, "total_commits": 50},
            ],
        }
        
        mock_client = MagicMock()
        mock_client.get_object.return_value = {
            'Body': MagicMock(read=lambda: json.dumps(initial_list).encode('utf-8'))
        }
        mock_client.put_object.side_effect = Exception("S3 write error")
        
        # Should not raise
        _update_org_files_after_deletion(mock_client, bucket_name, organization_id, codebase_id)

    def test_deletes_last_codebase(self):
        """Org summary shows zeros when last codebase is deleted."""
        codebase_id = str(uuid4())
        organization_id = "test-org"
        bucket_name = "test-bucket"
        
        initial_list = {
            "organization_id": organization_id,
            "codebases": [
                {"codebase_id": codebase_id, "total_commits": 100, "current_sloc": 5000, "total_contributors": 10},
            ],
        }
        
        mock_client = MagicMock()
        mock_client.get_object.return_value = {
            'Body': MagicMock(read=lambda: json.dumps(initial_list).encode('utf-8'))
        }
        
        _update_org_files_after_deletion(mock_client, bucket_name, organization_id, codebase_id)
        
        # Verify org_summary.json shows zeros
        summary_call = [c for c in mock_client.put_object.call_args_list 
                        if c.kwargs.get('Key') == 'analytics/org_summary.json'][0]
        summary = json.loads(summary_call.kwargs['Body'])
        
        assert summary['total_codebases'] == 0
        assert summary['total_commits'] == 0
        assert summary['total_sloc'] == 0
        assert summary['total_contributors'] == 0

