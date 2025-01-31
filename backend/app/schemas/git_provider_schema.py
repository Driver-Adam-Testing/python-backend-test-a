from database.models_v1 import GitProviderKind
from pydantic import BaseModel, Field


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


class CreateGitProviderAppRequest(BaseModel):
    organization_id: str
    name: str
    provider_kind: GitProviderKind
    shared_provider: bool
    base_url: str
    client_id: str
    client_secret: str
    redirect_uri: str
    scopes: list[str] = Field(default_factory=list)


class GitProviderAppSecret(BaseModel):
    client_secret: str
