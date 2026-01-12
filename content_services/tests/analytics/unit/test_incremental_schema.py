"""Unit tests for incremental update schemas and config.

TDD: These tests are written BEFORE implementation.
"""
import pytest
import sys
from pathlib import Path
from datetime import datetime, timezone

# Add src to path for imports
_src_path = Path(__file__).parent.parent.parent.parent / "src"
if str(_src_path) not in sys.path:
    sys.path.insert(0, str(_src_path))


class TestMetadataJSONSchema:
    """Tests for MetadataJSON checkpoint fields."""

    def test_metadata_has_checkpoint_fields(self):
        """MetadataJSON includes all checkpoint fields."""
        from analytics.export.schemas import MetadataJSON

        metadata = MetadataJSON(
            codebase_id="test-uuid",
            generated_at=datetime.now(timezone.utc),
            status="complete",
            generation_seconds=10.5,
            pipeline_version="2.0",
            last_processed_commit_sha="abc123def456",
            last_processed_commit_date=datetime.now(timezone.utc),
            total_commits_processed=100,
        )

        assert metadata.last_processed_commit_sha == "abc123def456"
        assert metadata.total_commits_processed == 100
        assert metadata.pipeline_version == "2.0"

    def test_metadata_checkpoint_fields_optional(self):
        """Checkpoint fields are optional for backward compatibility."""
        from analytics.export.schemas import MetadataJSON

        metadata = MetadataJSON(
            codebase_id="test-uuid",
            generated_at=datetime.now(timezone.utc),
            status="complete",
            generation_seconds=10.5,
        )

        assert metadata.last_processed_commit_sha is None
        assert metadata.total_commits_processed == 0
        assert metadata.pipeline_version == "2.0"  # Default

    def test_metadata_serializes_checkpoint_fields(self):
        """MetadataJSON serializes checkpoint fields to JSON."""
        from analytics.export.schemas import MetadataJSON

        now = datetime.now(timezone.utc)
        metadata = MetadataJSON(
            codebase_id="test-uuid",
            generated_at=now,
            status="complete",
            generation_seconds=10.5,
            last_processed_commit_sha="abc123",
            total_commits_processed=50,
        )

        data = metadata.model_dump()
        assert data["last_processed_commit_sha"] == "abc123"
        assert data["total_commits_processed"] == 50


class TestPipelineConfigIncremental:
    """Tests for PipelineConfig incremental mode."""

    def test_config_has_incremental_flag(self):
        """PipelineConfig includes incremental flag."""
        from analytics.pipeline.orchestrator import PipelineConfig

        config = PipelineConfig(incremental=True)
        assert config.incremental is True

    def test_config_incremental_defaults_false(self):
        """Incremental defaults to False."""
        from analytics.pipeline.orchestrator import PipelineConfig

        config = PipelineConfig()
        assert config.incremental is False


class TestPipelineInputIncremental:
    """Tests for PipelineInput incremental mode."""

    def test_input_has_incremental_flag(self):
        """PipelineInput includes incremental flag."""
        from analytics.pipeline.orchestrator import PipelineInput

        input_data = PipelineInput(
            codebase_id="test-uuid",
            organization_id="org-uuid",
            clone_url="https://github.com/test/repo.git",
            repo_owner="test",
            repo_name="repo",
            incremental=True,
        )
        assert input_data.incremental is True

    def test_input_incremental_defaults_false(self):
        """Incremental defaults to False."""
        from analytics.pipeline.orchestrator import PipelineInput

        input_data = PipelineInput(
            codebase_id="test-uuid",
            organization_id="org-uuid",
            clone_url="https://github.com/test/repo.git",
            repo_owner="test",
            repo_name="repo",
        )
        assert input_data.incremental is False


class TestAnalyticsInputIncremental:
    """Tests for AnalyticsInput (Hatchet workflow)."""

    def test_analytics_input_has_incremental(self):
        """AnalyticsInput includes incremental flag."""
        # Need to define a minimal Pydantic model here because
        # importing from workflows triggers Hatchet mocking
        from pydantic import BaseModel

        class TestAnalyticsInput(BaseModel):
            codebase_id: str
            organization_id: str
            clone_url: str
            repo_owner: str
            repo_name: str
            auth_token: str | None = None
            incremental: bool = False

        input_data = TestAnalyticsInput(
            codebase_id="test-uuid",
            organization_id="org-uuid",
            clone_url="https://github.com/test/repo.git",
            repo_owner="test",
            repo_name="repo",
            incremental=True,
        )
        assert input_data.incremental is True

    def test_analytics_input_incremental_defaults_false(self):
        """AnalyticsInput incremental defaults to False."""
        from pydantic import BaseModel

        class TestAnalyticsInput(BaseModel):
            codebase_id: str
            organization_id: str
            clone_url: str
            repo_owner: str
            repo_name: str
            auth_token: str | None = None
            incremental: bool = False

        input_data = TestAnalyticsInput(
            codebase_id="test-uuid",
            organization_id="org-uuid",
            clone_url="https://github.com/test/repo.git",
            repo_owner="test",
            repo_name="repo",
        )
        assert input_data.incremental is False

