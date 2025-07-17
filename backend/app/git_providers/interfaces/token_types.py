from enum import Enum
from pydantic import BaseModel


class TokenType(str, Enum):
    # OAUTH = "oauth"
    GROUP_ACCESS_TOKEN = "group_access_token"  # GitLab
    WORKSPACE_ACCESS_TOKEN = "workspace_access_token"  # Bitbucket
    PROJECT_ACCESS_TOKEN = "project_access_token" # Bitbucket
    REPOSITORY_ACCESS_TOKEN = "repository_access_token" # Bitbucket

    def __str__(self) -> str:
        return self.name

class AccessTokenData(BaseModel):
    """Unified access token model"""
    token_type: TokenType = TokenType.GROUP_ACCESS_TOKEN
    token: str
    workspace_or_group: str | None = None
    name: str | None = None
    metadata: dict = {}

    # def is_oauth(self) -> bool:
    #     return self.token_type == TokenType.OAUTH

    def is_access_token(self) -> bool:
        return self.token_type in [TokenType.GROUP_ACCESS_TOKEN, TokenType.WORKSPACE_ACCESS_TOKEN]


# class BitbucketAccessToken(BaseModel):
#     token_type: BitbucketTokenType
#     token: str
#     workspace: str
#     project_key: str | None = None  # For project tokens
#     repository_slug: str | None = None  # For repo tokens