from enum import Enum

from database.models import GitProviderKind
from pydantic import BaseModel, Field


class TokenType(str, Enum):
    # OAUTH = "oauth"
    GROUP_ACCESS_TOKEN = "group_access_token"  # GitLab
    WORKSPACE_ACCESS_TOKEN = "workspace_access_token"  # Bitbucket
    PROJECT_ACCESS_TOKEN = "project_access_token"  # Bitbucket
    REPOSITORY_ACCESS_TOKEN = "repository_access_token"  # Bitbucket
    PERSONAL_ACCESS_TOKEN = "personal_access_token"  # Azure DevOps

    def __str__(self) -> str:
        return self.name


class AccessTokenData(BaseModel):
    """Unified access token model"""

    token_type: TokenType = TokenType.GROUP_ACCESS_TOKEN
    token: str
    workspace_or_group: str | None = None
    name: str | None = None
    metadata: dict = {}

    def is_access_token(self) -> bool:
        return self.token_type in [
            TokenType.GROUP_ACCESS_TOKEN,
            TokenType.WORKSPACE_ACCESS_TOKEN,
            TokenType.PERSONAL_ACCESS_TOKEN,
        ]


class GitProvider(BaseModel):
    display_name: str
    name: str
    logo_url: str


class GitRepository(BaseModel):
    provider_name: str
    provider_kind: GitProviderKind | None = None
    repo_name: str
    org: str
    last_updated: str
    metadata: dict
    latest_commit: dict | None = None
    default_branch: str | None = None
    installation_id: str | None = None


class GitProviderAppConfig(BaseModel):
    base_url: str
    client_id: str
    client_secret: str
    redirect_uri: str
    scope: str | None = None


class GroupAccessToken(AccessTokenData):
    name: str | None = None
    token: str
    token_type: TokenType = TokenType.GROUP_ACCESS_TOKEN


class CreateGitProviderAppRequest(BaseModel):
    organization_id: str = Field(serialization_alias="owner_organization_id")
    name: str
    provider_kind: GitProviderKind
    shared_provider: bool = False
    base_url: str
    client_id: str | None = None
    client_secret: str | None = None
    redirect_uri: str | None = None
    scopes: list[str] | None = Field(default_factory=list)


class GitProviderAppSecret(BaseModel):
    client_secret: str | None = None


class GitProviderAppTokenSecret(BaseModel):
    token: str
    secret_token: str | None = None


class WebhookInfo(BaseModel):
    callback_url: str
    custom_headers: dict
    secret_token: str
    ssl_verification: bool
    triggers: list[str]
