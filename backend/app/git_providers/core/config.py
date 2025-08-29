from uuid import UUID

from database.models import GitProviderKind
from pydantic import BaseModel, computed_field


class GitProviderConfig(BaseModel):
    application_id: UUID
    name: str
    provider_kind: GitProviderKind
    base_url: str
    client_id: str | None = None
    client_secret: str | None = None
    redirect_uri: str | None = None
    token_endpoint: str | None = None
    user_endpoint: str | None = None
    authorize_endpoint: str | None = None
    token_info_endpoint: str | None = None
    scope: str | None = None

    @computed_field
    @property
    def authorize_url(self) -> str | None:
        if self.base_url and self.authorize_endpoint:
            return f"{self.base_url}/{self.authorize_endpoint}"
        return None

    @computed_field
    @property
    def access_token_url(self) -> str | None:
        if self.base_url and self.token_endpoint:
            return f"{self.base_url}/{self.token_endpoint}"
        return None

    @computed_field
    @property
    def user_info_url(self) -> str | None:
        if self.base_url and self.user_endpoint:
            return f"{self.base_url}/{self.user_endpoint}"
        return None
