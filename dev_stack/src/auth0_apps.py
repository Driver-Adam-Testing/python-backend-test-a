import httpx
from auth0.authentication import GetToken
from auth0.management import Auth0
from config import settings
from models import Auth0SpaCreateAppRequest

domain = settings.AUTH0_DOMAIN
mgmt_client_id = settings.AUTH0_MGMT_API_CLIENT_ID
mgmt_client_secret = settings.AUTH0_MGMT_API_CLIENT_SECRET
mgmt_api_audience = settings.AUTH0_MGMT_API_AUDIENCE
get_token = GetToken(domain, mgmt_client_id, mgmt_client_secret)
token = get_token.client_credentials(mgmt_api_audience)

auth0_client = Auth0(domain, token["access_token"])


def create_spa_web_app(create_app: Auth0SpaCreateAppRequest) -> dict:
    spa_app = auth0_client.clients.create(create_app.model_dump())
    connection_name = "google-oauth2"
    connection = next(
        conn
        for conn in auth0_client.connections.all()
        if conn["name"] == connection_name
    )
    connection_id = connection["id"]
    url = f"https://{settings.AUTH0_DOMAIN}/api/v2/connections/{connection_id}/clients"

    payload = [{"client_id": spa_app["client_id"], "status": False}]
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token['access_token']}",
    }
    # response = httpx.post(url, headers=headers, json=payload)
    try:
        with httpx.Client() as client:
            response = client.patch(url, headers=headers, json=payload)
            print(response)
            response.raise_for_status()  # Raises an exception if the HTTP response status is not successful.
            print("✅ Disabled google-oauth2 connection")
    except httpx.HTTPStatusError as e:
        print(f"❌ Error {e.response.status_code}: {e.response.text}")

    return spa_app
    # return {}


def create_api_app(name: str, identifier: str) -> dict:
    api_payload = {
        "name": name,
        "identifier": identifier,
        "signing_alg": "RS256",
        "token_lifetime": 86400,
        "skip_consent_for_verifiable_first_party_clients": True,
        "allow_offline_access": True,
        "enforce_policies": True,  # Enable RBAC
        "token_dialect": "access_token_authz",
        "scopes": [
            {
                "value": "organization:management",
                "description": "Ability to add, remove and manage members of the organization.",
            },
            {
                "value": "content:readonly",
                "description": "Ability to view all content within the organization",
            },
            {
                "value": "content:editor",
                "description": "Ability to edit all content within the organization.",
            },
            {"value": "usage_credit:management", "description": "Issue usage credits"},
            {"value": "subscription:management", "description": "Manage subscriptions"},
            {
                "value": "git_provider:management",
                "description": "Git provider app management",
            },
        ],
    }

    api = auth0_client.resource_servers.create(api_payload)
    print(f"✅ Created API: {api['name']} (ID: {api['id']})")
    # The API identifier from your API configuration
    api_identifier = identifier  # This is the identifier you used when creating the API
    # List of permissions to assign (these should match the scopes defined in your API)
    admin_permissions = [
        "organization:management",
        "content:readonly",
        "content:editor",
    ]
    admin_role_name = "Admin"
    # Assign permissions to the role for the API
    assign_role_permissions_to_api(admin_role_name, api_identifier, admin_permissions)
    print(
        f"✅ Assigned permissions to role '{admin_role_name}' for API '{api_identifier}'"
    )
    return api


def create_m2m_app(name: str, identifier: str) -> dict:
    # 1. Create the M2M client
    m2m_app = auth0_client.clients.create(
        {
            "name": name,
            "app_type": "non_interactive",
            "grant_types": ["client_credentials"],
            "oidc_conformant": True,
        }
    )
    print(f"✅ Created M2M App: {m2m_app['client_id']}")

    # 2. Authorize it to call the eric-backend API
    scopes = [
        "organization:management",
        "content:readonly",
        "content:editor",
        "usage_credit:management",
        "subscription:management",
        "git_provider:management",
    ]

    auth0_client.client_grants.create(
        {"client_id": m2m_app["client_id"], "audience": identifier, "scope": scopes}
    )

    print(f"✅ Authorized M2M app to call API: {identifier}")
    return m2m_app


def delete_auth0_app(client_id: str) -> bool:
    try:
        auth0_client.clients.delete(client_id)
        print(f"✅ Successfully deleted Auth0 application: {client_id}")
        return True
    except Exception as e:
        print(f"❌ Error deleting Auth0 application: {e!s}")
        return False


def delete_auth0_api(api_id: str) -> bool:
    try:
        auth0_client.resource_servers.delete(api_id)
        print(f"✅ Successfully deleted Auth0 API: {api_id}")
        return True
    except Exception as e:
        print(f"❌ Error deleting Auth0 API: {e!s}")
        return False


def get_role_by_name(role_name: str) -> dict | None:
    try:
        roles = auth0_client.roles.list()
        for role in roles.get("roles", []):
            if role["name"] == role_name:
                return role
        return None
    except Exception as e:
        print(f"❌ Error finding role: {e!s}")
        return None


def assign_role_permissions_to_api(
    role_name: str, api_identifier: str, permissions: list[str]
) -> bool:
    try:
        # Get the existing role
        role = get_role_by_name(role_name)
        if not role:
            print(f"❌ Role not found: {role_name}")
            return False

        # Create permission objects for the API
        permission_objects = [
            {
                "resource_server_identifier": api_identifier,
                "permission_name": permission,
            }
            for permission in permissions
        ]

        # Add permissions to the role
        auth0_client.roles.add_permissions(role["id"], permission_objects)
        print(
            f"✅ Successfully assigned permissions to role '{role_name}' for API '{api_identifier}'"
        )
        return True
    except Exception as e:
        print(f"❌ Error assigning permissions: {e!s}")
        return False
