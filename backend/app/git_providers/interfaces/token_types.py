from enum import Enum
from pydantic import BaseModel


class TokenType(str, Enum):
    # OAUTH = "oauth"
    GROUP_ACCESS_TOKEN = "group_access_token"  # GitLab
    WORKSPACE_ACCESS_TOKEN = "workspace_access_token"  # Bitbucket


class AccessTokenData(BaseModel):
    """Unified access token model"""
    token_type: TokenType
    token: str
    workspace_or_group: str | None = None
    name: str | None = None
    metadata: dict = {}

    # def is_oauth(self) -> bool:
    #     return self.token_type == TokenType.OAUTH

    def is_access_token(self) -> bool:
        return self.token_type in [TokenType.GROUP_ACCESS_TOKEN, TokenType.WORKSPACE_ACCESS_TOKEN]