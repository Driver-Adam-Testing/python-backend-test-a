import enum

from pydantic import BaseModel, computed_field, constr


class Auth0SpaCreateAppRequest(BaseModel):
    name: constr(strip_whitespace=True, min_length=1)
    app_type: str = "spa"
    callbacks: list[str]
    allowed_logout_urls: list[str]
    web_origins: list[str]
    allowed_origins: list[str] | None = []
    initiate_login_uri: str | None = None
    oidc_conformant: bool = True
    token_endpoint_auth_method: str = "none"
    grant_types: list[str] | None = ["authorization_code", "refresh_token", "implicit"]
    organization_usage: str = "require"
    organization_require_behavior: str = "pre_login_prompt"


class Auth0ApiCreateRequest(BaseModel):
    name: constr(strip_whitespace=True, min_length=1)
    identifier: str
    signing_alg: str = "RS256"
    token_lifetime: int = 86400
    skip_consent_for_verifiable_first_party_clients: bool = True
    allow_offline_access: bool = True
    enforce_policies: bool = True  # RBAC
    include_email_in_tokens: bool = False
    scopes: list[dict]
    allow_skip_consent: bool = True
    enable_permissions_in_token: bool = True


class Auth0M2MCreateRequest(BaseModel):
    name: constr(strip_whitespace=True, min_length=1)
    app_type: str = "non_interactive"
    logo_uri: str | None = None
    grant_types: list[str] = ["client_credentials"]


class DomainType(enum.Enum):
    WEBAPP = "WEB_APP"
    API = "API"
    TCP = "TCP"


class DomainStatus(enum.Enum):
    CREATED = "CREATED"
    FAILED = "FAILED"


class NgrokReservedDomain(BaseModel):
    domain_type: DomainType
    subdomain: str
    domain: str
    description: str
    region: str = "us"
    status: DomainStatus
    metadata: dict | None = None

    @computed_field
    @property
    def domain_url(self) -> str:
        return f"https://{self.domain}"


class NgrokReservedTcpAddress(BaseModel):
    address: str
    description: str
    region: str = "us"
    status: DomainStatus
    metadata: dict | None = None

    @computed_field
    @property
    def address_url(self) -> str:
        return f"tcp://{self.address}"


class DeveloperResourceType(enum.Enum):
    WEB_APP = "WEB_APP"
    API = "API"
    M2M = "M2M"
    DB = "DB"


class DeveloperResource(BaseModel):
    resource_name: str
    resource_type: DeveloperResourceType
    resource: dict


class WebAppResourceConfig(BaseModel):
    resource_name: str = "webapp-frontend"
    vite_config: dict
    env: dict


class ApiResourceConfig(BaseModel):
    resource_name: str = "backend"
    env: dict


class Developer(BaseModel):
    full_name: str
    email: str
    region: str = "us"  # Default to "us" region
    reserved_domains: list[NgrokReservedDomain] = []
    reserved_tcp_address: NgrokReservedTcpAddress | None = None
    auth0_webapp: dict | None = None
    auth0_api: dict | None = None
    auth0_m2m: dict | None = None
    resources: list[DeveloperResource] = []

    @computed_field
    @property
    def s3_bucket_name(self) -> str:
        return f"{self.full_name.lower().replace(' ', '-')}-codebase-dropzone"
