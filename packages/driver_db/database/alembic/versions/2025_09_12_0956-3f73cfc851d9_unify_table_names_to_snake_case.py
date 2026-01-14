"""unify table names to snake_case

Revision ID: 3f73cfc851d9
Revises: 20250909_add_checklist
Create Date: 2025-09-12 09:56:09.013169

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "3f73cfc851d9"
down_revision = "20250909_add_checklist"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Rename tables with v2_ prefix
    op.rename_table("v2_primary_asset", "primary_asset")
    op.rename_table("v2_version", "version")
    op.rename_table("v2_node", "node")
    op.rename_table("v2_primary_asset_tag", "primary_asset_tag")
    op.rename_table("v2_runtime_llm_session", "runtime_llm_session")
    op.rename_table("v2_runtime_llm_message_history", "runtime_llm_message_history")
    op.rename_table("v2_runtime_llm_messages", "runtime_llm_messages")
    op.rename_table("v2_autodoc_status_history", "autodoc_status_history")
    op.rename_table("v2_api_key", "api_key")

    # Rename plural tables to singular
    op.rename_table("derived_contents", "derived_content")
    op.rename_table("document_sources", "document_source")
    op.rename_table("tags", "tag")
    op.rename_table("github_app_installations", "github_app_installation")
    op.rename_table("git_provider_apps", "git_provider_app")
    op.rename_table("git_provider_app_installations", "git_provider_app_installation")
    op.rename_table("usage_sessions", "usage_session")
    op.rename_table("usage_events", "usage_event")

    # Rename tables without consistent underscores
    op.rename_table("runtimelogagentinstance", "runtime_log_agent_instance")
    op.rename_table("runtimelogagentmessage", "runtime_log_agent_message")
    op.rename_table("chunkandembedding", "chunk_and_embedding")
    op.rename_table("inspectorrun", "inspector_run")


def downgrade() -> None:
    # Reverse: Rename tables back to original names
    op.rename_table("primary_asset", "v2_primary_asset")
    op.rename_table("version", "v2_version")
    op.rename_table("node", "v2_node")
    op.rename_table("primary_asset_tag", "v2_primary_asset_tag")
    op.rename_table("runtime_llm_session", "v2_runtime_llm_session")
    op.rename_table("runtime_llm_message_history", "v2_runtime_llm_message_history")
    op.rename_table("runtime_llm_messages", "v2_runtime_llm_messages")
    op.rename_table("autodoc_status_history", "v2_autodoc_status_history")
    op.rename_table("api_key", "v2_api_key")

    # Reverse: Rename singular tables back to plural
    op.rename_table("derived_content", "derived_contents")
    op.rename_table("document_source", "document_sources")
    op.rename_table("tag", "tags")
    op.rename_table("github_app_installation", "github_app_installations")
    op.rename_table("git_provider_app", "git_provider_apps")
    op.rename_table("git_provider_app_installation", "git_provider_app_installations")
    op.rename_table("usage_session", "usage_sessions")
    op.rename_table("usage_event", "usage_events")

    # Reverse: Rename tables back to no underscores
    op.rename_table("runtime_log_agent_instance", "runtimelogagentinstance")
    op.rename_table("runtime_log_agent_message", "runtimelogagentmessage")
    op.rename_table("chunk_and_embedding", "chunkandembedding")
    op.rename_table("inspector_run", "inspectorrun")
