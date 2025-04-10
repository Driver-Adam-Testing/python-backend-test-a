import json
from pathlib import Path

from auth0_apps import (
    create_api_app,
    create_m2m_app,
    create_spa_web_app,
    delete_auth0_api,
    delete_auth0_app,
)
from config import settings
from models import (
    ApiResourceConfig,
    Auth0SpaCreateAppRequest,
    Developer,
    DeveloperResource,
    DeveloperResourceType,
    DomainStatus,
    DomainType,
    GitHubAppPermissionsConfig,
    GitHubAppResource,
    GitHubAppWebhookConfig,
    NgrokReservedDomain,
    NgrokReservedTcpAddress,
    WebAppResourceConfig,
)
from ngrok import (
    create_reserved_domain,
    create_reserved_tcp_address,
    delete_reserved_domain,
    delete_reserved_tcp_address,
    generate_unique_subdomain,
)
from utils import generate_webhook_secret


def create_developer(full_name: str, email: str, region: str = "us") -> Developer:
    return Developer(
        full_name=full_name,
        email=email,
        region=region,
    )


def create_developer_domains(
    developer: Developer,
    domain_types: list[DomainType],
    ngrok_api_key: str,
) -> list[NgrokReservedDomain] | None:
    results = []
    for app_type in domain_types:
        subdomain = generate_unique_subdomain(
            developer.full_name, prefix=app_type.value
        )
        description = f"Reserved domain for {developer.full_name} ({app_type.value})"
        reserved_domain = create_reserved_domain(
            ngrok_api_key, subdomain, description, region=developer.region
        )
        if reserved_domain:
            results.append(
                NgrokReservedDomain(
                    domain_type=app_type,
                    subdomain=subdomain,
                    domain=reserved_domain["domain"],
                    description=description,
                    region=developer.region,
                    status=DomainStatus.CREATED,
                    metadata=reserved_domain,
                )
            )
    return results


def write_developer_state(developer: Developer, output_dir: str = "state") -> None:
    # Create output directory if it doesn't exist
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    # Create filename from developer's name
    filename = f"{developer.full_name.lower().replace(' ', '_')}_state.json"
    file_path = output_path / filename

    # Write the state to file
    with open(file_path, "w") as f:
        json.dump(developer.model_dump(mode="json"), f, indent=2)

    print(f"✅ Developer state written to: {file_path}")


def create_developer_tcp_tunnel(
    developer: Developer,
    ngrok_api_key: str,
) -> NgrokReservedTcpAddress | None:
    description = f"TCP tunnel for {developer.full_name}"
    try:
        return create_reserved_tcp_address(
            api_key=ngrok_api_key,
            description=description,
            region=developer.region,
            metadata=json.dumps({"developer": developer.full_name}),
        )
    except Exception as e:
        print(f"❌ Error creating TCP tunnel: {e!s}")
        return None


def setup_developer_resources(
    full_name: str, email: str, region: str = "us"
) -> Developer:
    ngrok_api_key = settings.NGROK_API_KEY
    developer = create_developer(full_name, email, region)

    # Create domains
    domain_types = [DomainType.WEBAPP, DomainType.API]
    # domain_types = [ DomainType.API]
    developer_domains = create_developer_domains(developer, domain_types, ngrok_api_key)
    developer.reserved_domains.extend(developer_domains)

    # Create TCP tunnel
    tcp_tunnel = create_developer_tcp_tunnel(developer, ngrok_api_key)
    if tcp_tunnel:
        developer.reserved_tcp_address = tcp_tunnel

    web_app_domain = next(
        domain
        for domain in developer.reserved_domains
        if domain.domain_type == DomainType.WEBAPP
    )
    print(f"Web App Domain: {web_app_domain.domain}")
    auth0_web_app = Auth0SpaCreateAppRequest(
        name=f"{developer.full_name} Cloud Local Web App",
        callbacks=[web_app_domain.domain_url, "http://localhost:3000"],
        allowed_logout_urls=[web_app_domain.domain_url, "http://localhost:3000"],
        web_origins=[web_app_domain.domain_url, "http://localhost:3000"],
        allowed_origins=[web_app_domain.domain_url, "http://localhost:3000"],
        initiate_login_uri=web_app_domain.domain_url,
    )
    web_app = create_spa_web_app(auth0_web_app)

    api_domain = next(
        domain
        for domain in developer.reserved_domains
        if domain.domain_type == DomainType.API
    )
    identifier = f"{api_domain.domain_url}/api/v1"
    api_app = create_api_app(
        name=f"{developer.full_name} Cloud Local API", identifier=identifier
    )

    m2m_app = create_m2m_app(
        name=f"{developer.full_name} Cloud Local M2M", identifier=identifier
    )

    developer.auth0_webapp = web_app
    developer.auth0_api = api_app
    developer.auth0_m2m = m2m_app

    web_app_resource = DeveloperResource(
        resource_name="Web App",
        resource_type=DeveloperResourceType.WEB_APP,
        resource=web_app,
    )
    api_resource = DeveloperResource(
        resource_name="API",
        resource_type=DeveloperResourceType.API,
        resource=api_app,
    )
    m2m_resource = DeveloperResource(
        resource_name="M2M",
        resource_type=DeveloperResourceType.M2M,
        resource=m2m_app,
    )
    db_resource = DeveloperResource(
        resource_name="DB",
        resource_type=DeveloperResourceType.DB,
        resource=tcp_tunnel.model_dump(mode="json"),
    )
    github_app = GitHubAppResource(
        app_name=f"{developer.sanitized_full_name}-gh-app",
        # app_id=123456,
        # client_id="your-client-id",
        # client_secret="your-client-secret",
        homepage_url=web_app_domain.domain_url,
        callback_url=f"{identifier}/git-provider/github/callback",
        request_oauth_on_installation=True,
        enable_device_flow=True,
        setup_url=f"https://github.com/app/{developer.sanitized_full_name}-gh-app",
        redirect_on_update=True,
        webhook=GitHubAppWebhookConfig(
            webhook_url=f"{identifier}/git-provider/github/webhook",
            webhook_secret=generate_webhook_secret(),
            ssl_verification_enabled=True,
        ),
        permissions=GitHubAppPermissionsConfig(
            repository_permissions={
                "contents": "read-only",
                "pull_requests": "read-only",
                "metadata": "read-only",
                "webhooks": "read-only",
            },
            organization_permissions={
                "events": "read-only",
                "members": "read-only",
                "webhooks": "read-only",
            },
            account_permissions={"email_addresses": "read-only"},
        ),
        subscribed_events=["push", "pull_request", "installation", "repository"],
        public_in_marketplace=False,
        # private_key_pem_path="/path/to/private-key.pem"
    )
    gh_app_resource = DeveloperResource(
        resource_name="github-app",
        resource_type=DeveloperResourceType.GITHUB_APP,
        resource=github_app.model_dump(mode="json"),
    )
    developer.resources = [
        web_app_resource,
        api_resource,
        m2m_resource,
        db_resource,
        gh_app_resource,
    ]
    # Write the developer state to a file
    write_developer_state(developer)

    return developer


def create_developer_resource_configs(developer: Developer) -> dict:
    resource_configs = {}
    web_app_domain = next(
        domain
        for domain in developer.reserved_domains
        if domain.domain_type == DomainType.WEBAPP
    )
    for resource in developer.resources:
        match resource.resource_type:
            case DeveloperResourceType.WEB_APP:
                webapp_resource = WebAppResourceConfig(
                    vite_config={
                        "server": {
                            "port": 3000,
                            "allowedHosts": [web_app_domain.domain],
                        }
                    },
                    env={
                        "VITE_NODE_ENV": "development",
                        "VITE_API_AUDIENCE": developer.auth0_api["identifier"],
                        "VITE_API_URL": developer.auth0_api["identifier"],
                        "VITE_AUTH0_BASE_URL": web_app_domain.domain_url,
                        "VITE_AUTH0_CLIENT_ID": developer.auth0_webapp["client_id"],
                        "VITE_AUTH0_DOMAIN": "auth.dev.driverai.com",
                    },
                )
                resource_configs[webapp_resource.resource_name] = (
                    webapp_resource.model_dump(mode="json")
                )
            case DeveloperResourceType.API:
                api_resource = ApiResourceConfig(
                    env={
                        "DATABASE_URL": "change this",
                        "AUTH0_DOMAIN": "auth.dev.driverai.com",
                        "AUTH0_CLIENT_ID": developer.auth0_webapp["client_id"],
                        "AUTH0_AUDIENCE": developer.auth0_api["identifier"],
                        "AUTH0_MGMT_API_CLIENT_ID": settings.AUTH0_MGMT_API_CLIENT_ID,
                        "AUTH0_MGMT_API_CLIENT_SECRET": settings.AUTH0_MGMT_API_CLIENT_SECRET,
                        "AUTH0_MGMT_API_AUDIENCE": settings.AUTH0_MGMT_API_AUDIENCE,
                        "DROPZONE_BUCKET_NAME": developer.s3_bucket_name,
                        "BACKEND_CORS_ORIGINS": web_app_domain.domain_url,
                        "USE_LEGACY_DROPZONE": "False",
                    }
                )
                resource_configs[api_resource.resource_name] = api_resource.model_dump(
                    mode="json"
                )
            case DeveloperResourceType.GITHUB_APP:
                resource_configs[resource.resource_name] = resource.resource
            case DeveloperResourceType.M2M:
                # resource_configs[resource.resource_name] = resource.resource
                pass
            case DeveloperResourceType.DB:
                pass
    return resource_configs


def teardown_developer_resources(developer: Developer) -> bool:
    success = True

    # Delete Auth0 resources
    if developer.auth0_webapp and not delete_auth0_app(
        developer.auth0_webapp["client_id"]
    ):
        success = False

    if developer.auth0_m2m and not delete_auth0_app(developer.auth0_m2m["client_id"]):
        success = False

    if developer.auth0_api and not delete_auth0_api(developer.auth0_api["id"]):
        success = False

    # Delete ngrok reserved domains
    for domain in developer.reserved_domains:
        if (
            domain.metadata
            and "id" in domain.metadata
            and not delete_reserved_domain(
                settings.NGROK_API_KEY, domain.metadata["id"]
            )
        ):
            success = False

    # Delete ngrok TCP address
    if (
        developer.reserved_tcp_address
        and developer.reserved_tcp_address.metadata
        and "id" in developer.reserved_tcp_address.metadata
        and not delete_reserved_tcp_address(
            settings.NGROK_API_KEY, developer.reserved_tcp_address.metadata["id"]
        )
    ):
        success = False

    # Delete state file
    try:
        filename = f"{developer.full_name.lower().replace(' ', '_')}_state.json"
        file_path = Path("state") / filename
        if file_path.exists():
            file_path.unlink()
            print(f"✅ Deleted state file: {file_path}")
    except Exception as e:
        print(f"❌ Error deleting state file: {e!s}")
        success = False

    # Delete config directory
    try:
        config_dir = Path("state/out")
        if config_dir.exists():
            import shutil

            shutil.rmtree(config_dir)
            print(f"✅ Deleted config directory: {config_dir}")
    except Exception as e:
        print(f"❌ Error deleting config directory: {e!s}")
        success = False

    # Delete gh.html file
    try:
        gh_html_path = Path("static") / "gh.html"
        if gh_html_path.exists():
            gh_html_path.unlink()
            print(f"✅ Deleted GitHub app setup guide: {gh_html_path}")
    except Exception as e:
        print(f"❌ Error deleting GitHub app setup guide: {e!s}")
        success = False

    return success
