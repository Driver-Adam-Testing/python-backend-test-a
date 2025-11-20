import logging

import httpx

from shared.auth0.auth0_service import Auth0Service

logger = logging.getLogger(__name__)


class AsyncAuth0Service(Auth0Service):
    """Async version of Auth0Service for non-blocking operations."""

    def __init__(
        self,
        auth0_mgmt_domain: str,
        auth0_mgmt_client_id: str,
        auth0_mgmt_client_secret: str,
        auth0_domain: str,
        auth0_client_id: str,
    ) -> None:
        super().__init__(
            auth0_mgmt_domain=auth0_mgmt_domain,
            auth0_mgmt_client_id=auth0_mgmt_client_id,
            auth0_mgmt_client_secret=auth0_mgmt_client_secret,
            auth0_domain=auth0_domain,
            auth0_client_id=auth0_client_id,
        )

    async def list_user_organizations_async(self, user_id: str) -> dict:
        """
        Returns the same format as the sync version.
        """
        try:
            mgmt_token = self.get_mgmt_api_token()

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://{self.auth0_mgmt_domain}/api/v2/users/{user_id}/organizations",
                    headers={"Authorization": f"Bearer {mgmt_token}"},
                    params={"per_page": 100},
                )
                response.raise_for_status()

                organizations = response.json()
                return {"organizations": organizations}

        except Exception as e:
            logger.error(f"Something went wrong listing organizations for {user_id}")
            raise e

    async def list_user_organization_roles_async(
        self, org_id: str, user_id: str
    ) -> list[dict]:
        """
        Returns the same format as the sync version.
        """
        try:
            mgmt_token = self.get_mgmt_api_token()

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://{self.auth0_mgmt_domain}/api/v2/organizations/{org_id}/members/{user_id}/roles",
                    headers={"Authorization": f"Bearer {mgmt_token}"},
                    params={"per_page": 100},
                )
                response.raise_for_status()

                roles = response.json()
                return roles

        except Exception as e:
            logger.error(f"Something went wrong listing organizations for {user_id}")
            raise e
