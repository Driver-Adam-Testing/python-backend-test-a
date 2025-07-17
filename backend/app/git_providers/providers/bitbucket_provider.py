# import json
# import logging
# from typing import List, Dict, Optional, Tuple
# from app.git_providers.interfaces.provider_interface import GitProviderInterface
# from app.git_providers.interfaces.token_types import AccessTokenData, TokenType
# from app.git_providers.core.config import GitProviderConfig
# from app.git_providers.resources.bitbucket_api_resources import BitbucketAPIResources
# from app.git_providers.utils.errors import GitProviderAccessTokenError
# from app.git_providers.utils.git_provider_utils import generate_codebase_metadata
# from app.schemas.git_provider_schema import GitRepository, GitProviderAppTokenSecret
# from app.schemas.secret_management_schema import APP_INSTALL_WAT_NAME_PREFIX
# from database.models_v1 import GitProviderApp, GitProviderAppInstallation
# from shared.file_storage.aws_s3_client import AWSS3Client
# from shared.interfaces.aws_client_config import AWSClientConfig
# from shared.secret_management.aws_secret_management import (
#     AWSSecretManagementStrategy,
#     format_secret_name
# )
#
# logger = logging.getLogger(__name__)
#
#
# class BitbucketProvider(GitProviderInterface):
#     """Bitbucket provider implementation supporting Workspace Access Tokens only"""
#
#     def __init__(self, config: GitProviderConfig, secrets_manager: AWSSecretManagementStrategy):
#         self.config = config
#         self.secrets_manager = secrets_manager
#         self.api_strategy = BitbucketAPIResources(config.base_url)
#         # No OAuth strategy needed - WAT only
#
#     @classmethod
#     def from_config(cls, app: GitProviderApp, aws_config: AWSClientConfig) -> 'BitbucketProvider':
#         """Create BitbucketProvider from app configuration"""
#         from app.git_providers.core.config_loader import load_provider_config
#
#         secrets_manager = AWSSecretManagementStrategy(aws_config)
#
#         # Bitbucket with WAT doesn't need app-level secrets
#         config = load_provider_config(app, client_secret=None)
#
#         return cls(config, secrets_manager)
#
#     def validate_access_token(self, token_data: Dict) -> Tuple[bool, Optional[str]]:
#         """Validate Bitbucket Workspace Access Token"""
#         access_token = AccessTokenData(**token_data)
#
#         # if access_token.token_type != TokenType.WORKSPACE_ACCESS_TOKEN:
#         #     return False, "Bitbucket only supports Workspace Access Tokens"
#
#         # Validate WAT by checking workspace access
#         try:
#             is_valid, message = self.api_strategy.validate_workspace_access(
#                 access_token.name,
#                 access_token.token
#             )
#             return (is_valid, None) if is_valid else (False, message)
#         except Exception as e:
#             logger.error(f"WAT validation failed: {e}")
#             return False, str(e)
#
#     def create_installation(self, organization_id: str, app_id: str,
#                             token_data: Dict) -> GitProviderAppInstallation:
#         """Create Bitbucket installation record"""
#         access_token = AccessTokenData(**token_data)
#
#         return GitProviderAppInstallation(
#             git_provider_app_id=app_id,
#             organization_id=organization_id,
#             misc_metadata={
#                 "kind": token_data["token_type"],
#                 "name": access_token.name,
#             }
#         )
#
#     def store_secrets(self, installation: GitProviderAppInstallation,
#                       token_data: Dict) -> None:
#         """Store Bitbucket WAT in AWS Secrets Manager"""
#         access_token = AccessTokenData(**token_data)
#
#         # Generate webhook secret
#         import secrets
#         webhook_secret = secrets.token_urlsafe(32)
#
#         secret_key = format_secret_name(APP_INSTALL_WAT_NAME_PREFIX, str(installation.id))
#         secret_value = json.dumps(
#             GitProviderAppTokenSecret(
#                 token=access_token.token,
#                 secret_token=webhook_secret
#             ).model_dump()
#         )
#
#         self.secrets_manager.write_secret(secret_key, secret_value)
#         logger.info(f"Stored WAT for Bitbucket installation {installation.id}")
#
#     def fetch_secrets(self, installation: GitProviderAppInstallation) -> dict:
#         """Fetch stored secrets for a Bitbucket installation"""
#         secret_key = format_secret_name(APP_INSTALL_WAT_NAME_PREFIX, str(installation.id))
#         secret_value = self.secrets_manager.read_secret(secret_key)
#
#         if not secret_value:
#             raise ValueError(f"WAT not found for installation: {installation.id}")
#
#         return secret_value
#
#     def fetch_repositories(self, installation: GitProviderAppInstallation) -> List[GitRepository]:
#         """Fetch Bitbucket repositories using WAT"""
#         logger.info(f"Fetching repositories for installation: {installation.id}")
#
#         try:
#             # Get WAT from secrets
#             access_token = self._fetch_workspace_access_token(str(installation.id))
#
#             # Get workspace from installation metadata
#             workspace = installation.misc_metadata.get("name")
#             if not workspace:
#                 raise ValueError("Workspace not found in installation metadata")
#
#             # Fetch repositories from API
#             repos_data = self.api_strategy.list_repositories(workspace, access_token)
#
#             # Convert to GitRepository objects
#             repos = []
#             for repo in repos_data:
#                 print(repo)
#                 # Fetch latest commit for each repo if needed
#                 latest_commit = None
#                 try:
#                     commit_hash = self.api_strategy.get_latest_commit(
#                         workspace, repo["slug"], access_token
#                     )
#                     latest_commit = {"id": commit_hash}
#                 except Exception as e:
#                     logger.warning(f"Failed to fetch latest commit for {repo['name']}: {e}")
#
#                 repos.append(GitRepository(
#                     org=repo["owner"]["display_name"],
#                     installation_id=str(installation.id),
#                     provider_kind=installation.git_provider_app.provider_kind,
#                     provider_name=str(installation.git_provider_app.provider_kind),
#                     repo_name=repo["name"],
#                     repo_id=repo["uuid"],
#                     repo_full_name=repo["full_name"],
#                     repo_url=repo["links"]["html"]["href"],
#                     latest_commit=latest_commit,
#                     last_updated=repo.get("updated_on"),
#                     metadata={
#                         "workspace": workspace,
#                         "slug": repo["slug"],
#                         "is_private": repo.get("is_private", True),
#                         "language": repo.get("language"),
#                         "created_on": repo.get("created_on"),
#                         "updated_on": repo.get("updated_on")
#                     }
#                 ))
#
#             return repos
#
#         except Exception as e:
#             logger.error(f"Failed to fetch repositories: {e}")
#             raise
#
#     def clone_repository(self, repo_info: GitRepository, user_id: str,
#                          org_id: str, upload_key: str, bucket_name: str) -> str:
#         """Clone Bitbucket repository and upload to S3"""
#         logger.info(f"Cloning Bitbucket repository: {repo_info.repo_name}")
#
#         try:
#             # Get WAT
#             access_token = self._fetch_workspace_access_token(repo_info.installation_id)
#
#             # Get repository details
#             workspace = repo_info.metadata["workspace"]
#             repo_slug = repo_info.metadata["slug"]
#
#             # Get latest commit if not specified
#             commit = repo_info.latest_commit.get("id") if repo_info.latest_commit else None
#             if not commit:
#                 logger.warning(f"No commit specified for {repo_info.repo_name}, fetching latest")
#                 commit = self.api_strategy.get_latest_commit(
#                     workspace, repo_slug, access_token
#                 )
#
#             # Download repository
#             logger.info(f"Downloading repository {workspace}/{repo_slug} at commit {commit}")
#             zip_content = self.api_strategy.download_repo(
#                 workspace, repo_slug, commit, access_token
#             )
#
#             # Generate metadata
#             metadata = generate_codebase_metadata(
#                 org_id=org_id,
#                 org_name=workspace,
#                 repo=repo_info.repo_name,
#                 repo_id=repo_info.repo_id,
#                 owner=workspace,
#                 provider="bitbucket",
#                 commit=commit,
#                 upload_key=upload_key
#             )
#
#             # Upload to S3
#             logger.info(f"Uploading repository to S3: {upload_key}")
#             s3_client = AWSS3Client(self.secrets_manager.aws_config)
#
#             upload_success = s3_client.upload_to_s3(
#                 file_content=zip_content,
#                 bucket_name=bucket_name,
#                 s3_key=upload_key,
#                 metadata_dict=metadata
#             )
#
#             if not upload_success:
#                 raise ValueError("Failed to upload repository to S3")
#
#             # Generate presigned URL
#             download_url = s3_client.generate_get_presigned_url(bucket_name, upload_key)
#             logger.info(f"Repository cloned successfully: {repo_info.repo_name}")
#
#             return download_url
#
#         except Exception as e:
#             logger.error(f"Failed to clone repository: {e}")
#             raise
#
#     def handle_webhook(self, event_type: str, payload: Dict,
#                        installation_id: str) -> Dict:
#         """Handle Bitbucket webhook events"""
#         logger.info(f"Handling Bitbucket webhook: {event_type} for installation {installation_id}")
#
#         try:
#             # Bitbucket event types are prefixed (e.g., "repo:push")
#             if event_type == "repo:push":
#                 return self._handle_push_event(payload, installation_id)
#             elif event_type == "pullrequest:created" or event_type == "pullrequest:updated":
#                 return self._handle_pull_request_event(payload, installation_id, event_type)
#             elif event_type == "repo:fork":
#                 return self._handle_fork_event(payload, installation_id)
#             else:
#                 logger.info(f"Ignoring Bitbucket event type: {event_type}")
#                 return {"status": "ignored", "event": event_type}
#
#         except Exception as e:
#             logger.error(f"Error handling webhook: {e}")
#             raise
#
#     def revoke_access(self, installation: GitProviderAppInstallation) -> None:
#         """Revoke access for a Bitbucket installation"""
#         logger.info(f"Revoking access for Bitbucket installation {installation.id}")
#
#         # Delete WAT secret
#         secret_key = format_secret_name(APP_INSTALL_WAT_NAME_PREFIX, str(installation.id))
#         self.secrets_manager.delete_secret(secret_key)
#         logger.info(f"Deleted WAT secret for installation {installation.id}")
#
#     # Private helper methods
#
#     def _fetch_workspace_access_token(self, install_id: str) -> str:
#         """Fetch Workspace Access Token from secrets"""
#         secret_key = format_secret_name(APP_INSTALL_WAT_NAME_PREFIX, install_id)
#         secret_value = self.secrets_manager.read_secret(secret_key)
#
#         if not secret_value:
#             raise ValueError(f"WAT not found for installation: {install_id}")
#
#         return secret_value["token"]
#
#     def _handle_push_event(self, payload: Dict, installation_id: str) -> Dict:
#         """Handle push webhook event"""
#         push = payload.get("push", {})
#         repository = payload.get("repository", {})
#         changes = push.get("changes", [])
#
#         logger.info(f"Push event for repository {repository.get('name')} with {len(changes)} changes")
#
#         # Extract branch info from changes
#         branches = []
#         commits_count = 0
#
#         for change in changes:
#             if change.get("new", {}).get("type") == "branch":
#                 branch_name = change["new"]["name"]
#                 branches.append(branch_name)
#                 commits_count += len(change.get("commits", []))
#
#         return {
#             "status": "processed",
#             "event": "push",
#             "repository": repository.get("name"),
#             "branches": branches,
#             "commits": commits_count
#         }
#
#     def _handle_pull_request_event(self, payload: Dict, installation_id: str, event_type: str) -> Dict:
#         """Handle pull request webhook event"""
#         pullrequest = payload.get("pullrequest", {})
#         action = event_type.split(":")[-1]  # Extract action from event type
#
#         logger.info(f"Pull request event: {action} for PR {pullrequest.get('id')}")
#
#         return {
#             "status": "processed",
#             "event": "pull_request",
#             "action": action,
#             "pull_request_id": pullrequest.get("id"),
#             "title": pullrequest.get("title")
#         }
#
#     def _handle_fork_event(self, payload: Dict, installation_id: str) -> Dict:
#         """Handle fork webhook event"""
#         repository = payload.get("repository", {})
#         fork = payload.get("fork", {})
#
#         logger.info(f"Fork event for repository {repository.get('name')}")
#
#         return {
#             "status": "processed",
#             "event": "fork",
#             "original_repository": repository.get("name"),
#             "fork_name": fork.get("name"),
#             "fork_owner": fork.get("owner", {}).get("display_name")
#         }