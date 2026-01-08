"""Integration tests for branch lifecycle detection."""
import json
import pytest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch
import tempfile


class TestBranchLifecycleIntegration:
    """Integration tests for branch lifecycle in incremental mode."""

    def test_branch_diff_runs_in_full_mode(self):
        """Branch diff runs in ALL modes (not just incremental) to detect deletions."""
        from analytics.pipeline.orchestrator import (
            AnalyticsPipeline,
            PipelineConfig,
            PipelineContext,
            PipelineInput,
        )
        from analytics.pipeline.phases.branches import BranchesResult, BranchInfo

        config = PipelineConfig(work_dir=Path(tempfile.mkdtemp()))
        pipeline = AnalyticsPipeline(config)

        # Non-incremental input - branch diff should still run!
        input_data = PipelineInput(
            codebase_id="test-codebase",
            organization_id="test-org",
            clone_url="https://github.com/test/repo",
            repo_owner="test",
            repo_name="repo",
            incremental=False,  # Not incremental, but should still detect deletions
        )

        ctx = PipelineContext(config=config, input=input_data)
        ctx.branches_result = BranchesResult(
            success=True,
            branches=[
                BranchInfo(
                    name="main",
                    head_sha="abc123",
                    divergence_point_sha=None,
                    parent_branch=None,
                    created_at=None,
                    last_commit_at=datetime.now(timezone.utc),
                    is_default=True,
                )
            ],
            default_branch="main",
        )

        # Mock previous branches.json with a deleted branch
        previous_branches = {
            "codebase_id": "test-codebase",
            "branches": [
                {"name": "main", "head_commit_sha": "abc123", "commits": 100},
                {"name": "feature-old", "head_commit_sha": "def456", "commits": 10},
            ],
        }

        with patch.object(pipeline, '_download_branches_json', return_value=previous_branches):
            ctx.repo = MagicMock()
            ctx.repo.branches = MagicMock()
            ctx.repo.branches.local = ["main"]
            ctx.repo.branches.remote = []
            ctx.repo.branches.__getitem__ = MagicMock(return_value=MagicMock(target="abc123"))
            ctx.repo.descendant_of = MagicMock(return_value=False)

            pipeline._phase_branch_diff(ctx)

        # Branch diff should run even in full mode - should detect deletion
        assert len(ctx.deleted_branches) == 1
        assert ctx.deleted_branches[0]["name"] == "feature-old"

    def test_branch_diff_detects_deleted_branch(self):
        """Deleted branches are detected and marked in incremental mode."""
        from analytics.pipeline.orchestrator import (
            AnalyticsPipeline,
            PipelineConfig,
            PipelineContext,
            PipelineInput,
        )
        from analytics.pipeline.phases.branches import BranchesResult, BranchInfo

        config = PipelineConfig(work_dir=Path(tempfile.mkdtemp()))
        pipeline = AnalyticsPipeline(config)

        # Incremental input
        input_data = PipelineInput(
            codebase_id="test-codebase",
            organization_id="test-org",
            clone_url="https://github.com/test/repo",
            repo_owner="test",
            repo_name="repo",
            incremental=True,
        )

        ctx = PipelineContext(config=config, input=input_data)

        # Current branches: only main (feature-old was deleted)
        ctx.branches_result = BranchesResult(
            success=True,
            branches=[
                BranchInfo(
                    name="main",
                    head_sha="abc123",
                    divergence_point_sha=None,
                    parent_branch=None,
                    created_at=None,
                    last_commit_at=datetime.now(timezone.utc),
                    is_default=True,
                )
            ],
            default_branch="main",
        )

        # Mock previous branches.json with feature-old
        previous_branches = {
            "codebase_id": "test-codebase",
            "branches": [
                {"name": "main", "head_commit_sha": "abc123", "commits": 100},
                {"name": "feature-old", "head_commit_sha": "def456", "commits": 10},
            ],
        }

        with patch.object(pipeline, '_download_branches_json', return_value=previous_branches):
            # Mock repo for merge detection (branch was not merged)
            ctx.repo = MagicMock()
            ctx.repo.branches = MagicMock()
            ctx.repo.branches.local = ["main"]
            ctx.repo.branches.remote = []
            ctx.repo.branches.__getitem__ = MagicMock(return_value=MagicMock(target="abc123"))
            ctx.repo.descendant_of = MagicMock(return_value=False)  # Not merged

            # Run branch diff phase
            pipeline._phase_branch_diff(ctx)

        # Should have one deleted branch
        assert len(ctx.deleted_branches) == 1
        deleted = ctx.deleted_branches[0]
        assert deleted["name"] == "feature-old"
        assert deleted["is_deleted"] is True
        assert deleted["is_merged"] is False
        assert deleted["deleted_at"] is not None
        assert deleted["merged_at"] is None

    def test_branch_diff_detects_merged_branch(self):
        """Merged and deleted branches are correctly identified."""
        from analytics.pipeline.orchestrator import (
            AnalyticsPipeline,
            PipelineConfig,
            PipelineContext,
            PipelineInput,
            _was_merged,
        )
        from analytics.pipeline.phases.branches import BranchesResult, BranchInfo

        config = PipelineConfig(work_dir=Path(tempfile.mkdtemp()))
        pipeline = AnalyticsPipeline(config)

        input_data = PipelineInput(
            codebase_id="test-codebase",
            organization_id="test-org",
            clone_url="https://github.com/test/repo",
            repo_owner="test",
            repo_name="repo",
            incremental=True,
        )

        ctx = PipelineContext(config=config, input=input_data)

        # Current: only main (feature-merged was deleted after merging)
        ctx.branches_result = BranchesResult(
            success=True,
            branches=[
                BranchInfo(
                    name="main",
                    head_sha="abc123def456789012345678901234567890abcd",
                    divergence_point_sha=None,
                    parent_branch=None,
                    created_at=None,
                    last_commit_at=datetime.now(timezone.utc),
                    is_default=True,
                )
            ],
            default_branch="main",
        )

        previous_branches = {
            "codebase_id": "test-codebase",
            "branches": [
                {"name": "main", "head_commit_sha": "abc123def456789012345678901234567890abcd", "commits": 100},
                {"name": "feature-merged", "head_commit_sha": "def456789012345678901234567890abcdef1234", "commits": 5},
            ],
        }

        # Mock _was_merged to return True for the merged branch
        with patch.object(pipeline, '_download_branches_json', return_value=previous_branches):
            with patch('analytics.pipeline.orchestrator._was_merged', return_value=True):
                pipeline._phase_branch_diff(ctx)

        assert len(ctx.deleted_branches) == 1
        deleted = ctx.deleted_branches[0]
        assert deleted["name"] == "feature-merged"
        assert deleted["is_deleted"] is True
        assert deleted["is_merged"] is True
        assert deleted["deleted_at"] is not None
        assert deleted["merged_at"] is not None
        assert deleted["status"] == "merged"


class TestExporterWithDeletedBranches:
    """Tests for exporter including deleted branches."""

    def test_exporter_includes_deleted_branches(self, tmp_path):
        """Exporter includes deleted branches in branches.json."""
        from analytics.export.exporter import DriverJSONExporter
        from analytics.storage.hot_storage import HotStorage

        # Create a mock hot storage
        hot_storage = MagicMock(spec=HotStorage)
        hot_storage.get_all_branch_metrics.return_value = [
            {
                "branch_name": "main",
                "is_default_branch": True,
                "total_commits": 100,
                "last_commit_at": datetime.now(timezone.utc),
                "is_active": True,
                "head_commit_sha": "abc123",
            }
        ]

        # Deleted branches
        deleted_branches = [
            {
                "name": "feature-old",
                "is_merged": False,
                "is_deleted": True,
                "deleted_at": datetime.now(timezone.utc),
                "merged_at": None,
                "commits": 10,
                "head_commit_sha": "def456",
                "status": "deleted",
            }
        ]

        exporter = DriverJSONExporter(
            codebase_id="test-codebase",
            hot_storage=hot_storage,
            output_dir=tmp_path,
            deleted_branches=deleted_branches,
        )

        # Export branches
        result = exporter._export_branches()

        assert result is not None
        assert result.name == "branches.json"

        # Read and verify
        data = json.loads(result.read_text())
        assert len(data["branches"]) == 2

        # Find the deleted branch
        deleted = next(b for b in data["branches"] if b["name"] == "feature-old")
        assert deleted["is_deleted"] is True
        assert deleted["is_merged"] is False
        assert deleted["is_active"] is False

        # Find the active branch
        active = next(b for b in data["branches"] if b["name"] == "main")
        assert active["is_deleted"] is False
        assert active["is_active"] is True

    def test_exporter_handles_only_deleted_branches(self, tmp_path):
        """Exporter handles case with only deleted branches (no active)."""
        from analytics.export.exporter import DriverJSONExporter
        from analytics.storage.hot_storage import HotStorage

        hot_storage = MagicMock(spec=HotStorage)
        hot_storage.get_all_branch_metrics.return_value = []  # No active branches

        deleted_branches = [
            {
                "name": "orphan-branch",
                "is_merged": False,
                "is_deleted": True,
                "deleted_at": datetime.now(timezone.utc),
                "merged_at": None,
                "commits": 5,
                "head_commit_sha": "xyz789",
                "status": "deleted",
            }
        ]

        exporter = DriverJSONExporter(
            codebase_id="test-codebase",
            hot_storage=hot_storage,
            output_dir=tmp_path,
            deleted_branches=deleted_branches,
        )

        result = exporter._export_branches()

        assert result is not None
        data = json.loads(result.read_text())
        assert len(data["branches"]) == 1
        assert data["branches"][0]["name"] == "orphan-branch"
        assert data["branches"][0]["is_deleted"] is True

    def test_exporter_handles_no_branches(self, tmp_path):
        """Exporter returns None when no branches at all."""
        from analytics.export.exporter import DriverJSONExporter
        from analytics.storage.hot_storage import HotStorage

        hot_storage = MagicMock(spec=HotStorage)
        hot_storage.get_all_branch_metrics.return_value = []

        exporter = DriverJSONExporter(
            codebase_id="test-codebase",
            hot_storage=hot_storage,
            output_dir=tmp_path,
            deleted_branches=[],  # No deleted branches either
        )

        result = exporter._export_branches()
        assert result is None

    def test_exporter_filters_deleted_branches_from_hot_storage(self, tmp_path):
        """Exporter filters out deleted branches from hot storage results.
        
        This tests the bug fix where hot storage returns deleted branches
        (because commits still have branch_name references) but they should
        be exported as deleted, not active.
        """
        from analytics.export.exporter import DriverJSONExporter
        from analytics.storage.hot_storage import HotStorage

        # Hot storage still returns test-branch because commits have branch_name
        hot_storage = MagicMock(spec=HotStorage)
        hot_storage.get_all_branch_metrics.return_value = [
            {
                "branch_name": "main",
                "is_default_branch": True,
                "total_commits": 100,
                "last_commit_at": datetime.now(timezone.utc),
                "is_active": True,
                "head_commit_sha": "abc123",
            },
            {
                "branch_name": "test-branch",  # Deleted but still in hot storage!
                "is_default_branch": False,
                "total_commits": 3,
                "last_commit_at": datetime.now(timezone.utc),
                "is_active": True,  # Hot storage thinks it's active
                "head_commit_sha": "def456",
            }
        ]

        # But we know test-branch was deleted
        deleted_branches = [
            {
                "name": "test-branch",
                "is_merged": True,
                "is_deleted": True,
                "deleted_at": datetime.now(timezone.utc),
                "merged_at": datetime.now(timezone.utc),
                "commits": 3,
                "head_commit_sha": "def456",
                "status": "merged",
                "current_sloc": 10,
                "additions_sloc": 10,  # v3.0 schema: stored directly as SLOC
            }
        ]

        exporter = DriverJSONExporter(
            codebase_id="test-codebase",
            hot_storage=hot_storage,
            output_dir=tmp_path,
            deleted_branches=deleted_branches,
        )

        result = exporter._export_branches()
        assert result is not None
        
        data = json.loads(result.read_text())
        
        # Should have exactly 2 branches (main active, test-branch deleted)
        assert len(data["branches"]) == 2

        # Verify main is active
        main_branch = next(b for b in data["branches"] if b["name"] == "main")
        assert main_branch["is_active"] is True
        assert main_branch["is_deleted"] is False

        # Verify test-branch is deleted (not duplicated as active)
        test_branch = next(b for b in data["branches"] if b["name"] == "test-branch")
        assert test_branch["is_deleted"] is True
        assert test_branch["is_merged"] is True
        assert test_branch["is_active"] is False
        assert test_branch["status"] == "merged"
        # Verify historical metrics are preserved
        assert test_branch["current_sloc"] == 10
        assert test_branch["additions_sloc"] == 10  # 500 bytes / 50 = 10 SLOC

    def test_branch_diff_carries_forward_deleted_branches(self):
        """Branch diff carries forward previously deleted branches.
        
        This ensures deleted branches stay deleted across pipeline runs,
        rather than reappearing as 'stale' active branches.
        """
        from analytics.pipeline.orchestrator import (
            AnalyticsPipeline,
            PipelineConfig,
            PipelineContext,
            PipelineInput,
        )
        from analytics.pipeline.phases.branches import BranchesResult, BranchInfo

        config = PipelineConfig(work_dir=Path(tempfile.mkdtemp()))
        pipeline = AnalyticsPipeline(config)

        input_data = PipelineInput(
            codebase_id="test-codebase",
            organization_id="test-org",
            clone_url="https://github.com/test/repo",
            repo_owner="test",
            repo_name="repo",
            incremental=True,
        )

        ctx = PipelineContext(config=config, input=input_data)

        # Current: only main
        ctx.branches_result = BranchesResult(
            success=True,
            branches=[
                BranchInfo(
                    name="main",
                    head_sha="abc123",
                    divergence_point_sha=None,
                    parent_branch=None,
                    created_at=None,
                    last_commit_at=datetime.now(timezone.utc),
                    is_default=True,
                )
            ],
            default_branch="main",
        )

        # Previous branches.json includes an already-deleted branch
        previous_branches = {
            "codebase_id": "test-codebase",
            "branches": [
                {"name": "main", "head_commit_sha": "abc123", "commits": 100, "is_deleted": False},
                {
                    "name": "old-deleted-branch",
                    "head_commit_sha": "xyz789",
                    "commits": 5,
                    "is_deleted": True,  # Already marked as deleted!
                    "is_merged": True,
                    "status": "merged",
                    "deleted_at": "2024-01-01T00:00:00Z",
                },
            ],
        }

        with patch.object(pipeline, '_download_branches_json', return_value=previous_branches):
            ctx.repo = MagicMock()
            pipeline._phase_branch_diff(ctx)

        # Should carry forward the deleted branch (so it stays deleted in export)
        assert len(ctx.deleted_branches) == 1
        assert ctx.deleted_branches[0]["name"] == "old-deleted-branch"
        assert ctx.deleted_branches[0]["is_deleted"] is True
        assert ctx.deleted_branches[0]["status"] == "merged"

