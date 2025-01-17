from datetime import datetime

import strawberry


@strawberry.type
class GitProvider:
    display_name: str
    name: str
    logo_url: str


@strawberry.type
class GitRepository:
    provider_name: str
    repo_name: str
    org: str
    last_updated: datetime
    metadata: dict
