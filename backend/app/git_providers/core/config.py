from uuid import UUID

from database.models_v1 import GitProviderKind
from pydantic import BaseModel, computed_field


class GitProviderConfig(BaseModel):
    application_id: UUID
    name: str
    provider_kind: GitProviderKind
    base_url: str
    client_id: str | None = None
    client_secret: str | None = None
    redirect_uri: str | None = None
    token_endpoint: str
    user_endpoint: str
    authorize_endpoint: str
    token_info_endpoint: str | None = None
    scope: str | None = None

    @computed_field
    @property
    def authorize_url(self) -> str:
        return f"{self.base_url}/{self.authorize_endpoint}"

    @computed_field
    @property
    def access_token_url(self) -> str:
        return f"{self.base_url}/{self.token_endpoint}"

    @computed_field
    @property
    def user_info_url(self) -> str:
        return f"{self.base_url}/{self.user_endpoint}"
