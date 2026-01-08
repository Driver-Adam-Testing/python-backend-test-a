"""Shared fixtures for onboarding tests.

Note: We mock the Hatchet client before importing any onboarding modules
to avoid needing real Hatchet credentials during tests.
"""
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock

# Add src directory to Python path for imports
_src_path = Path(__file__).resolve().parent.parent.parent / "src"
if str(_src_path) not in sys.path:
    sys.path.insert(0, str(_src_path))

# Mock hatchet_client BEFORE importing any workflow modules
# This prevents Hatchet from requiring credentials at import time
mock_hatchet = MagicMock()
sys.modules['hatchet_client'] = mock_hatchet
mock_hatchet.hatchet = MagicMock()

# Also mock the workflows module to prevent import errors
mock_analytics_workflow = MagicMock()
sys.modules['workflows.analytics_workflow'] = mock_analytics_workflow
mock_analytics_workflow.analytics_task = MagicMock()
mock_analytics_workflow.AnalyticsInput = MagicMock()

import pytest
from unittest.mock import patch


@pytest.fixture
def mock_analytics_task():
    """Mock analytics_task.run_no_wait() for trigger tests."""
    with patch('workflows.analytics_workflow.analytics_task') as mock_task:
        mock_task.run_no_wait.return_value = Mock(workflow_run_id='test_run_123')
        yield mock_task


@pytest.fixture
def mock_all_provider_auth():
    """Mock all provider token fetchers."""
    with patch('onboarding.onboard._get_provider_token_fetchers') as mock_fetchers:
        fetchers = {
            'github': Mock(return_value='ghs_xxx'),
            'gitlab': Mock(return_value='glpat_xxx'),
            'bitbucket': Mock(return_value='bb_xxx'),
            'azure_devops': Mock(return_value='pat_xxx'),
        }
        mock_fetchers.return_value = fetchers
        yield fetchers


@pytest.fixture
def mock_github_auth_failure():
    """Mock GitHub auth failure (app uninstalled)."""
    from shared.inspector.onboarding.onboard_utils import AccessTokenError
    with patch('onboarding.onboard._get_provider_token_fetchers') as mock_fetchers:
        mock_fetchers.return_value = {
            'github': Mock(side_effect=AccessTokenError('Installation 99999 not found'))
        }
        yield mock_fetchers
