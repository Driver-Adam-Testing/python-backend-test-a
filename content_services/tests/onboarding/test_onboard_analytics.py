"""Unit tests for analytics auto-trigger on codebase connection.

Tests the analytics_trigger module which provides helper functions for
spawning analytics tasks when a codebase is connected.
"""
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

# Add src directory to Python path for imports
_src_path = Path(__file__).resolve().parent.parent.parent / "src"
if str(_src_path) not in sys.path:
    sys.path.insert(0, str(_src_path))

import pytest

# Import the module under test (doesn't have heavy dependencies)
from onboarding.analytics_trigger import (
    build_clone_url,
    get_provider_auth_token,
    spawn_analytics_task,
    get_provider_token_fetchers,
    _PROVIDER_CLONE_URLS,
)


class TestGetProviderAuthToken:
    """Tests for multi-provider auth token retrieval."""

    def test_github_returns_token(self):
        """GitHub provider returns access token."""
        mock_fetcher = Mock(return_value='ghs_test_token_123')
        with patch('onboarding.analytics_trigger.get_provider_token_fetchers', return_value={'github': mock_fetcher}):
            result = get_provider_auth_token('github', '12345678')

        assert result == 'ghs_test_token_123'
        mock_fetcher.assert_called_once_with('12345678')

    def test_gitlab_returns_token(self):
        """GitLab provider returns access token."""
        mock_fetcher = Mock(return_value='glpat_test_token')
        with patch('onboarding.analytics_trigger.get_provider_token_fetchers', return_value={'gitlab': mock_fetcher}):
            result = get_provider_auth_token('gitlab', '87654321')

        assert result == 'glpat_test_token'
        mock_fetcher.assert_called_once_with('87654321')

    def test_gitlab_enterprise_returns_token(self):
        """GitLab Enterprise provider returns access token."""
        mock_fetcher = Mock(return_value='glpat_enterprise_token')
        with patch('onboarding.analytics_trigger.get_provider_token_fetchers', return_value={'gitlab_enterprise': mock_fetcher}):
            result = get_provider_auth_token('gitlab_enterprise', '11111111')

        assert result == 'glpat_enterprise_token'

    def test_bitbucket_returns_token(self):
        """Bitbucket provider returns access token."""
        mock_fetcher = Mock(return_value='bb_token_xxx')
        with patch('onboarding.analytics_trigger.get_provider_token_fetchers', return_value={'bitbucket': mock_fetcher}):
            result = get_provider_auth_token('bitbucket', '11111111')

        assert result == 'bb_token_xxx'

    def test_azure_devops_returns_token(self):
        """Azure DevOps provider returns access token."""
        mock_fetcher = Mock(return_value='pat_xxx')
        with patch('onboarding.analytics_trigger.get_provider_token_fetchers', return_value={'azure_devops': mock_fetcher}):
            result = get_provider_auth_token('azure_devops', '22222222')

        assert result == 'pat_xxx'

    def test_returns_none_for_null_install_id(self):
        """None install_id returns None (no API call)."""
        result = get_provider_auth_token('github', None)
        assert result is None

    def test_returns_none_for_empty_install_id(self):
        """Empty string install_id returns None."""
        result = get_provider_auth_token('github', '')
        assert result is None

    def test_returns_none_for_unsupported_provider(self):
        """Unsupported provider returns None."""
        with patch('onboarding.analytics_trigger.get_provider_token_fetchers', return_value={}):
            result = get_provider_auth_token('unknown_provider', '12345678')
        assert result is None

    def test_returns_none_on_access_token_error(self):
        """AccessTokenError (404) returns None, doesn't raise."""
        from shared.inspector.onboarding.onboard_utils import AccessTokenError
        mock_fetcher = Mock(side_effect=AccessTokenError('Installation not found'))
        with patch('onboarding.analytics_trigger.get_provider_token_fetchers', return_value={'github': mock_fetcher}):
            result = get_provider_auth_token('github', '99999999')

        assert result is None  # Doesn't raise

    def test_returns_none_on_unexpected_error(self):
        """Unexpected errors return None, don't raise."""
        mock_fetcher = Mock(side_effect=Exception('Network error'))
        with patch('onboarding.analytics_trigger.get_provider_token_fetchers', return_value={'github': mock_fetcher}):
            result = get_provider_auth_token('github', '12345678')

        assert result is None


class TestBuildCloneUrl:
    """Tests for clone URL construction for all providers."""

    def test_github_with_token(self):
        """GitHub with token uses x-access-token format."""
        url = build_clone_url('github', 'lodash/lodash', 'ghs_xxx')
        assert url == 'https://x-access-token:ghs_xxx@github.com/lodash/lodash.git'

    def test_github_without_token(self):
        """GitHub without token uses public URL."""
        url = build_clone_url('github', 'lodash/lodash', None)
        assert url == 'https://github.com/lodash/lodash.git'

    def test_gitlab_with_token(self):
        """GitLab uses oauth2 format."""
        url = build_clone_url('gitlab', 'group/project', 'glpat_xxx')
        assert url == 'https://oauth2:glpat_xxx@gitlab.com/group/project.git'

    def test_gitlab_without_token(self):
        """GitLab without token uses public URL."""
        url = build_clone_url('gitlab', 'group/project', None)
        assert url == 'https://gitlab.com/group/project.git'

    def test_bitbucket_with_token(self):
        """Bitbucket uses x-token-auth format."""
        url = build_clone_url('bitbucket', 'workspace/repo', 'bb_token')
        assert url == 'https://x-token-auth:bb_token@bitbucket.org/workspace/repo.git'

    def test_bitbucket_without_token(self):
        """Bitbucket without token uses public URL."""
        url = build_clone_url('bitbucket', 'workspace/repo', None)
        assert url == 'https://bitbucket.org/workspace/repo.git'

    def test_azure_devops_with_token(self):
        """Azure DevOps uses token in URL."""
        url = build_clone_url('azure_devops', 'org/project/_git/repo', 'pat_xxx')
        assert url == 'https://pat_xxx@dev.azure.com/org/project/_git/repo.git'

    def test_azure_devops_without_token(self):
        """Azure DevOps without token uses public URL."""
        url = build_clone_url('azure_devops', 'org/project/_git/repo', None)
        assert url == 'https://dev.azure.com/org/project/_git/repo.git'

    def test_unknown_provider_returns_none(self):
        """Unknown providers return None."""
        url = build_clone_url('unknown', 'org/repo', None)
        assert url is None


class TestSpawnAnalyticsTask:
    """Tests for analytics task spawning.
    
    Note: We need to mock workflows.analytics_workflow module since the imports
    are deferred inside spawn_analytics_task function.
    """

    def test_spawns_github_task_with_correct_input(self):
        """Spawns task with properly constructed input for GitHub."""
        mock_task = Mock()
        mock_task.run_no_wait.return_value = Mock(workflow_run_id='run_123')
        mock_input_cls = Mock(side_effect=lambda **kwargs: Mock(**kwargs))

        with patch('onboarding.analytics_trigger.get_provider_auth_token', return_value='ghs_xxx'), \
             patch.dict('sys.modules', {'workflows.analytics_workflow': Mock(
                 analytics_task=mock_task,
                 AnalyticsInput=mock_input_cls
             )}):
            result = spawn_analytics_task(
                codebase_id='uuid-123',
                organization_id='org_abc',
                codebase_name='lodash/lodash',
                provider='github',
                install_id='12345678',
            )

        assert result == 'run_123'
        call_args = mock_task.run_no_wait.call_args[0][0]
        assert call_args.codebase_id == 'uuid-123'
        assert call_args.organization_id == 'org_abc'
        assert call_args.clone_url == 'https://x-access-token:ghs_xxx@github.com/lodash/lodash.git'
        assert call_args.repo_owner == 'lodash'
        assert call_args.repo_name == 'lodash'
        assert call_args.auth_token == 'ghs_xxx'

    def test_spawns_gitlab_task(self):
        """Spawns task for GitLab provider."""
        mock_task = Mock()
        mock_task.run_no_wait.return_value = Mock(workflow_run_id='run_gl')
        mock_input_cls = Mock(side_effect=lambda **kwargs: Mock(**kwargs))

        with patch('onboarding.analytics_trigger.get_provider_auth_token', return_value='glpat_xxx'), \
             patch.dict('sys.modules', {'workflows.analytics_workflow': Mock(
                 analytics_task=mock_task,
                 AnalyticsInput=mock_input_cls
             )}):
            result = spawn_analytics_task(
                codebase_id='uuid-gl',
                organization_id='org_gl',
                codebase_name='group/project',
                provider='gitlab',
                install_id='gl_install',
            )

        assert result == 'run_gl'
        call_args = mock_task.run_no_wait.call_args[0][0]
        assert 'oauth2:glpat_xxx' in call_args.clone_url

    def test_spawns_bitbucket_task(self):
        """Spawns task for Bitbucket provider."""
        mock_task = Mock()
        mock_task.run_no_wait.return_value = Mock(workflow_run_id='run_bb')
        mock_input_cls = Mock(side_effect=lambda **kwargs: Mock(**kwargs))

        with patch('onboarding.analytics_trigger.get_provider_auth_token', return_value='bb_token'), \
             patch.dict('sys.modules', {'workflows.analytics_workflow': Mock(
                 analytics_task=mock_task,
                 AnalyticsInput=mock_input_cls
             )}):
            result = spawn_analytics_task(
                codebase_id='uuid-bb',
                organization_id='org_bb',
                codebase_name='workspace/repo',
                provider='bitbucket',
                install_id='bb_install',
            )

        assert result == 'run_bb'
        call_args = mock_task.run_no_wait.call_args[0][0]
        assert 'x-token-auth:bb_token' in call_args.clone_url

    def test_spawns_azure_devops_task(self):
        """Spawns task for Azure DevOps provider."""
        mock_task = Mock()
        mock_task.run_no_wait.return_value = Mock(workflow_run_id='run_ado')
        mock_input_cls = Mock(side_effect=lambda **kwargs: Mock(**kwargs))

        with patch('onboarding.analytics_trigger.get_provider_auth_token', return_value='pat_xxx'), \
             patch.dict('sys.modules', {'workflows.analytics_workflow': Mock(
                 analytics_task=mock_task,
                 AnalyticsInput=mock_input_cls
             )}):
            result = spawn_analytics_task(
                codebase_id='uuid-ado',
                organization_id='org_ado',
                codebase_name='org/project/_git/repo',
                provider='azure_devops',
                install_id='ado_install',
            )

        assert result == 'run_ado'
        call_args = mock_task.run_no_wait.call_args[0][0]
        assert 'pat_xxx@dev.azure.com' in call_args.clone_url

    def test_skips_manual_uploads(self):
        """Manual uploads are skipped - returns None without calling Hatchet."""
        result = spawn_analytics_task(
            codebase_id='uuid-manual',
            organization_id='org_manual',
            codebase_name='uploaded-repo',
            provider='manual',
            install_id=None,
        )

        assert result is None

    def test_spawns_for_public_repo_without_token(self):
        """Public repos spawn without auth token."""
        mock_task = Mock()
        mock_task.run_no_wait.return_value = Mock(workflow_run_id='run_456')
        mock_input_cls = Mock(side_effect=lambda **kwargs: Mock(**kwargs))

        with patch('onboarding.analytics_trigger.get_provider_auth_token', return_value=None), \
             patch.dict('sys.modules', {'workflows.analytics_workflow': Mock(
                 analytics_task=mock_task,
                 AnalyticsInput=mock_input_cls
             )}):
            result = spawn_analytics_task(
                codebase_id='uuid-123',
                organization_id='org_abc',
                codebase_name='public/repo',
                provider='github',
                install_id=None,
            )

        assert result == 'run_456'
        call_args = mock_task.run_no_wait.call_args[0][0]
        assert call_args.clone_url == 'https://github.com/public/repo.git'
        assert call_args.auth_token is None

    def test_returns_none_on_spawn_failure(self):
        """Spawn failure returns None, doesn't raise."""
        mock_task = Mock()
        mock_task.run_no_wait.side_effect = Exception('Hatchet unavailable')
        mock_input_cls = Mock(side_effect=lambda **kwargs: Mock(**kwargs))

        with patch('onboarding.analytics_trigger.get_provider_auth_token', return_value='ghs_xxx'), \
             patch.dict('sys.modules', {'workflows.analytics_workflow': Mock(
                 analytics_task=mock_task,
                 AnalyticsInput=mock_input_cls
             )}):
            result = spawn_analytics_task(
                codebase_id='uuid-123',
                organization_id='org_abc',
                codebase_name='lodash/lodash',
                provider='github',
                install_id='12345678',
            )

        assert result is None  # Doesn't raise

    def test_returns_none_for_unsupported_provider(self):
        """Unsupported provider returns None."""
        mock_task = Mock()
        mock_input_cls = Mock(side_effect=lambda **kwargs: Mock(**kwargs))

        with patch.dict('sys.modules', {'workflows.analytics_workflow': Mock(
                 analytics_task=mock_task,
                 AnalyticsInput=mock_input_cls
             )}):
            result = spawn_analytics_task(
                codebase_id='uuid-123',
                organization_id='org_abc',
                codebase_name='some/repo',
                provider='unsupported_vcs',
                install_id='12345678',
            )

        assert result is None
        mock_task.run_no_wait.assert_not_called()

    def test_extracts_repo_owner_and_name_correctly(self):
        """Repo owner and name are correctly extracted from codebase_name."""
        mock_task = Mock()
        mock_task.run_no_wait.return_value = Mock(workflow_run_id='run_xyz')
        mock_input_cls = Mock(side_effect=lambda **kwargs: Mock(**kwargs))

        with patch('onboarding.analytics_trigger.get_provider_auth_token', return_value=None), \
             patch.dict('sys.modules', {'workflows.analytics_workflow': Mock(
                 analytics_task=mock_task,
                 AnalyticsInput=mock_input_cls
             )}):
            result = spawn_analytics_task(
                codebase_id='uuid-nested',
                organization_id='org_nested',
                codebase_name='group/subgroup/repo',
                provider='gitlab',
                install_id=None,
            )

        call_args = mock_task.run_no_wait.call_args[0][0]
        assert call_args.repo_owner == 'group/subgroup'
        assert call_args.repo_name == 'repo'

    def test_handles_single_name_without_slash(self):
        """Handles codebase_name without slash (no owner)."""
        mock_task = Mock()
        mock_task.run_no_wait.return_value = Mock(workflow_run_id='run_single')
        mock_input_cls = Mock(side_effect=lambda **kwargs: Mock(**kwargs))

        with patch('onboarding.analytics_trigger.get_provider_auth_token', return_value=None), \
             patch.dict('sys.modules', {'workflows.analytics_workflow': Mock(
                 analytics_task=mock_task,
                 AnalyticsInput=mock_input_cls
             )}):
            result = spawn_analytics_task(
                codebase_id='uuid-single',
                organization_id='org_single',
                codebase_name='monorepo',
                provider='github',
                install_id=None,
            )

        call_args = mock_task.run_no_wait.call_args[0][0]
        assert call_args.repo_owner == ''
        assert call_args.repo_name == 'monorepo'
