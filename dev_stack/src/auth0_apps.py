import httpx
from auth0.authentication import GetToken
from auth0.management import Auth0
from config import settings
from models import Auth0SpaCreateAppRequest

# def create_auth0_client() -> Auth0:
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
        "scopes": [
            {"value": "read:appointments", "description": "Read your appointments"},
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
            {"value": "payment_initiation", "description": "Payment initiation"},
        ],
        # "options": {
        #     "allow_skip_consent": True,
        #     "enable_permissions_in_token": True,
        #     "token_lifetime_for_implicit_grant": 7200
        # }
    }

    api = auth0_client.resource_servers.create(api_payload)
    print(f"✅ Created API: {api['name']} (ID: {api['id']})")
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
        "read:appointments",
        "organization:management",
        "content:readonly",
        "content:editor",
        "usage_credit:management",
        "subscription:management",
        "git_provider:management",
        "payment_initiation",
    ]

    auth0_client.client_grants.create(
        {"client_id": m2m_app["client_id"], "audience": identifier, "scope": scopes}
    )

    print(f"✅ Authorized M2M app to call API: {identifier}")
    return m2m_app


def delete_auth0_app(client_id: str) -> bool:
    """
    Delete an Auth0 application.

    Args:
        client_id: The client ID of the application to delete

    Returns:
        bool: True if deletion was successful, False otherwise
    """
    try:
        auth0_client.clients.delete(client_id)
        print(f"✅ Successfully deleted Auth0 application: {client_id}")
        return True
    except Exception as e:
        print(f"❌ Error deleting Auth0 application: {e!s}")
        return False


def delete_auth0_api(api_id: str) -> bool:
    """
    Delete an Auth0 API.

    Args:
        api_id: The ID of the API to delete

    Returns:
        bool: True if deletion was successful, False otherwise
    """
    try:
        auth0_client.resource_servers.delete(api_id)
        print(f"✅ Successfully deleted Auth0 API: {api_id}")
        return True
    except Exception as e:
        print(f"❌ Error deleting Auth0 API: {e!s}")
        return False


# def main():
#     # Example usage
#     create_app = Auth0SpaCreateAppRequest(
#         name="Eric Cloud Local Web App",
#         callbacks=["https://app-driver.ngrok.io", "http://localhost:3000"],
#         allowed_logout_urls=["https://app-driver.ngrok.io", "http://localhost:3000"],
#         web_origins=["https://app-driver.ngrok.io", "http://localhost:3000"],
#         allowed_origins=["https://app-driver.ngrok.io", "http://localhost:3000"],
#         initiate_login_uri="https://app-driver.ngrok.io"
#     )
#     app = create_spa_web_app(create_app)
#     print(app)
#
#
# if __name__ == "__main__":
#     main()
