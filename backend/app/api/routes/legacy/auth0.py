import time

from auth0.authentication import GetToken
from auth0.exceptions import Auth0Error
from auth0.management import Auth0

from app.core.config import settings
from app.core.logger import logger

_auth0_management = None
_last_refresh_time = 0


def refresh_auth0_management_api(force_refresh=False):
    global _auth0_management, _last_refresh_time
    current_time = time.time()
    if not force_refresh and current_time - _last_refresh_time < 3600:
        return

    if not (
        settings.AUTH0_DOMAIN
        and settings.AUTH0_MGMT_API_CLIENT_ID
        and settings.AUTH0_MGMT_API_CLIENT_SECRET
    ):
        logger.error("Auth0 environment variables are not set.")
        raise ValueError("Auth0 configuration error.")

    get_token = GetToken(
        settings.AUTH0_DOMAIN,
        settings.AUTH0_MGMT_API_CLIENT_ID,
        client_secret=settings.AUTH0_MGMT_API_CLIENT_SECRET,
    )
    token = get_token.client_credentials(settings.AUTH0_MGMT_API_AUDIENCE)
    mgmt_api_token = token["access_token"]
    _auth0_management = Auth0(settings.AUTH0_DOMAIN, mgmt_api_token)
    _last_refresh_time = current_time


def get_auth0_management_api() -> Auth0:
    global _auth0_management
    if _auth0_management is None or (time.time() - _last_refresh_time) >= 3600:
        refresh_auth0_management_api()
    return _auth0_management


def get_users():
    try:
        return get_auth0_management_api().users.list()
    except Auth0Error as error:
        logger.error(f"Error fetching users: {error}")
        refresh_auth0_management_api(force_refresh=True)
        raise


def get_organizations():
    try:
        return get_auth0_management_api().organizations.all()
    except Auth0Error as error:
        logger.error(f"Failed to get Auth0 organizations: {error}")
        refresh_auth0_management_api(force_refresh=True)
        raise


def get_organization_by_name(org_name: str):
    try:
        return get_auth0_management_api().organizations.get_by_name(org_name)
    except Auth0Error as error:
        logger.error(f"Failed to get Auth0 organization: {error}")
        refresh_auth0_management_api(force_refresh=True)
        raise


def get_organization_by_id(org_id: str):
    try:
        return get_auth0_management_api().organizations.get_organization(org_id)
    except Auth0Error as error:
        logger.error(f"Failed to get Auth0 organization: {error}")
        refresh_auth0_management_api(force_refresh=True)
        raise


def create_organization(org_name: str, display_name: str, org_id: str):
    try:
        existing_org = get_organization_by_name(org_name)
        if existing_org:
            logger.info(f"Organization {org_name} already exists")
            return existing_org
        return get_auth0_management_api().organizations.create(
            {
                "name": org_name,
                "display_name": display_name,
                "metadata": {"driver_org_id": org_id},
            }
        )
    except Auth0Error as error:
        logger.error(f"Failed to create Auth0 organization: {error}")
        refresh_auth0_management_api(force_refresh=True)
        raise


def delete_organization(org_id: str):
    try:
        get_auth0_management_api().organizations.delete(org_id)
        logger.info(f"Organization deleted: {org_id}")
        return True
    except Auth0Error as error:
        logger.error(f"Failed to delete Auth0 organization: {error}")
        refresh_auth0_management_api(force_refresh=True)
        raise
