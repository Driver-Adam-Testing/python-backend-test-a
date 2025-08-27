import logging
import time

from auth0.authentication import Database, GetToken, Users
from auth0.management import Auth0
from fastapi.encoders import jsonable_encoder
import requests

from app.auth.models import User as UserToken
from app.auth.permissions import ORG_MANAGER
from app.core.config import settings
from app.schemas.auth0_schema import (
    CreateInvitationInput,
    ModifyUserRolesResponse,
)

logger = logging.getLogger(__name__)


class Auth0Service:
    _mgmt_token: str | None = None
    _mgmt_token_exp: float = 0.0  # epoch seconds

    def __init__(self) -> None:
        self.auth0_mgmt_domain: str = settings.AUTH0_MGMT_API_DOMAIN
        self.auth0_mgmt_client_id: str = settings.AUTH0_MGMT_API_CLIENT_ID
        self.auth0_mgmt_client_secret: str = settings.AUTH0_MGMT_API_CLIENT_SECRET
        self.auth0_domain: str = settings.AUTH0_DOMAIN
        self.auth0_client_id: str = settings.AUTH0_CLIENT_ID

    def _refresh_management_token(self) -> None:
        get_token = GetToken(
            self.auth0_mgmt_domain,
            client_id=self.auth0_mgmt_client_id,
            client_secret=self.auth0_mgmt_client_secret,
        )
        token = get_token.client_credentials(
            f"https://{self.auth0_mgmt_domain}/api/v2/"
        )
        self._mgmt_token = token["access_token"]
        self._mgmt_token_exp = time.time() + token.get("expires_in", 86_400)

    def _management_client(self) -> Auth0:
        if self._mgmt_token is None or self._mgmt_token_exp - time.time() < 60:
            self._refresh_management_token()

        return Auth0(self.auth0_mgmt_domain, self._mgmt_token)

    def get_mgmt_api_token(self: "Auth0Service") -> str:
        get_token = GetToken(
            self.auth0_mgmt_domain,
            client_id=self.auth0_mgmt_client_id,
            client_secret=self.auth0_mgmt_client_secret,
        )
        token = get_token.client_credentials(
            f"https://{self.auth0_mgmt_domain}/api/v2/"
        )
        return token["access_token"]

    def verify_org_management_permissions(
        self: "Auth0Service", user: UserToken
    ) -> None:
        if ORG_MANAGER not in user.permissions:
            raise PermissionError("Insufficient permissions.")

    def change_self_password(
        self: "Auth0Service", user: UserToken, access_token: str
    ) -> str:
        users = Users(domain=self.auth0_domain)
        try:
            user_profile = users.userinfo(access_token)
            management_domain = self.auth0_mgmt_domain
            db = Database(management_domain, self.auth0_client_id)
            response = db.change_password(
                email=user_profile.get("email"),
                connection="Username-Password-Authentication",
                organization=user.organization_id,
            )
            logger.info(
                f"User requested password reset for {user.subject} sent to {user_profile.get('email')}"
            )
            return response
        except Exception as e:
            logger.error(f"An error occurred getting user's information: {e}")
            raise e

    def list_user_organizations(self: "Auth0Service", user: UserToken) -> any:
        try:
            mgmt_api_token = self.get_mgmt_api_token()
            management_api = Auth0(self.auth0_mgmt_domain, mgmt_api_token)

            return management_api.users.list_organizations(user.user_id, per_page=100)
        except Exception as e:
            logger.error(
                f"Something went wrong listing organizations for {user.user_id}"
            )
            raise e

    def modify_user_roles(
        self: "Auth0Service",
        user: UserToken,
        roles: list[str],
        modified_user_id: str,
    ) -> any:
        self.verify_org_management_permissions(user)
        try:
            mgmt_api_token = self.get_mgmt_api_token()
            management_api = Auth0(self.auth0_mgmt_domain, mgmt_api_token)
            existing_roles = management_api.organizations.all_organization_member_roles(
                id=user.organization_id, user_id=modified_user_id
            )
            existing_role_ids = [r["id"] for r in existing_roles]
            new_role_ids = []
            for added_role in roles:
                if added_role not in existing_role_ids:
                    new_role_ids.append(added_role)
            if len(new_role_ids) > 0:
                management_api.organizations.create_organization_member_roles(
                    id=user.organization_id,
                    user_id=modified_user_id,
                    body=jsonable_encoder({"roles": new_role_ids}),
                )

            removed_role_ids = []
            for existing_role_id in existing_role_ids:
                if existing_role_id not in roles:
                    removed_role_ids.append(existing_role_id)
            if len(removed_role_ids) > 0:
                management_api.organizations.delete_organization_member_roles(
                    id=user.organization_id,
                    user_id=modified_user_id,
                    body=jsonable_encoder({"roles": removed_role_ids}),
                )

            return ModifyUserRolesResponse(
                user_id=modified_user_id,
                added_roles=new_role_ids,
                removed_roles=removed_role_ids,
            )
        except Exception as e:
            logger.error(f"Something went wrong modifying user roles {user.user_id}")
            raise e

    def list_members(
        self: "Auth0Service", user: UserToken, page: int = 0, per_page: int = 100
    ) -> any:
        self.verify_org_management_permissions(user)
        try:
            mgmt_api_token = self.get_mgmt_api_token()
            management_api = Auth0(self.auth0_mgmt_domain, mgmt_api_token)
            return management_api.organizations.all_organization_members(
                id=user.organization_id,
                page=page,
                per_page=per_page,
                # Roles are not returned by default, so we have to do this explicitly
                fields=["user_id", "email", "picture", "name", "roles"],
            )
        except Exception as e:
            logger.error(
                f"Something went wrong listing users for organization {user.organization_display_name} requested by {user.user_id}"
            )
            raise e

    def list_invitations(
        self: "Auth0Service", user: UserToken, page: int = 0, per_page: int = 100
    ) -> any:
        self.verify_org_management_permissions(user)
        try:
            mgmt_api_token = self.get_mgmt_api_token()
            management_api = Auth0(self.auth0_mgmt_domain, mgmt_api_token)
            return management_api.organizations.all_organization_invitations(
                id=user.organization_id, page=page, per_page=per_page
            )
        except Exception as e:
            logger.error(
                f"Something went wrong listing invitations for organization {user.organization_display_name} requested by {user.user_id}"
            )
            raise e

    def list_roles(self: "Auth0Service", page: int = 0, per_page: int = 100) -> any:
        try:
            mgmt_api_token = self.get_mgmt_api_token()
            management_api = Auth0(self.auth0_mgmt_domain, mgmt_api_token)
            return management_api.roles.list(page=page, per_page=per_page)
        except Exception as e:
            logger.error("Something went wrong listing roles")
            raise e

    def get_role_id_by_name(self: "Auth0Service", role_name: str) -> str | None:
        """
        Lookup a role ID by its name (exact match). Returns None if not found.
        """
        try:
            mgmt_api_token = self.get_mgmt_api_token()
            management_api = Auth0(self.auth0_mgmt_domain, mgmt_api_token)
            page = 0
            per_page = 50
            while True:
                roles_page = management_api.roles.list(page=page, per_page=per_page)

                # Normalize SDK response shapes
                items: list = []
                if isinstance(roles_page, list):
                    items = roles_page
                elif isinstance(roles_page, dict):
                    for key in ("roles", "items", "results", "data", "list"):
                        if isinstance(roles_page.get(key), list):
                            items = roles_page.get(key)  # type: ignore[assignment]
                            break
                    if not items:
                        # Some SDKs return {'length': n, 'start': 0, 'limit': 50, 'roles': [...]}
                        # Already handled above; if still empty, nothing to iterate.
                        items = []

                if not items:
                    return None

                for item in items:
                    if isinstance(item, dict):
                        if item.get("name") == role_name:
                            return item.get("id")
                    elif isinstance(item, str):
                        # If the SDK returns IDs as strings, fetch details
                        try:
                            role_obj = management_api.roles.get(item)
                            if role_obj and role_obj.get("name") == role_name:
                                return role_obj.get("id")
                        except Exception:
                            # Ignore and continue searching
                            pass

                if len(items) < per_page:
                    return None
                page += 1
        except Exception:
            logger.error(f"Error looking up role by name '{role_name}'", exc_info=True)
            return None

    def create_invitation(
        self: "Auth0Service",
        user: UserToken,
        access_token: str,
        invitations: CreateInvitationInput,
    ) -> any:
        self.verify_org_management_permissions(user)
        users = Users(domain=self.auth0_domain)
        try:
            userinfo = users.userinfo(access_token)
            mgmt_api_token = self.get_mgmt_api_token()
            management_api = Auth0(self.auth0_mgmt_domain, mgmt_api_token)

            organization_info = management_api.organizations.get_organization(
                user.organization_id
            )

            invitation_results = []
            for invitation in invitations.invitations:
                payload = {
                    "inviter": {"name": userinfo.get("name")},
                    "invitee": invitation.invitee,
                    "roles": invitation.roles,
                    "client_id": settings.AUTH0_CLIENT_ID,
                }
                if (
                    "metadata" in organization_info
                    and "sso_connection_id" in organization_info["metadata"]
                ):
                    payload["connection_id"] = organization_info["metadata"][
                        "sso_connection_id"
                    ]
                invitation_results.append(
                    management_api.organizations.create_organization_invitation(
                        id=user.organization_id,
                        body=jsonable_encoder(payload),
                    )
                )
            return invitation_results
        except Exception as e:
            logger.error(
                f"Something went wrong creating the invitation for organization {user.organization_display_name} requested by {user.user_id}"
            )
            raise e

    def delete_user_from_organization(
        self: "Auth0Service", user: UserToken, user_id_to_remove: str
    ) -> any:
        self.verify_org_management_permissions(user)
        try:
            mgmt_api_token = self.get_mgmt_api_token()
            management_api = Auth0(self.auth0_mgmt_domain, mgmt_api_token)
            return management_api.organizations.delete_organization_members(
                id=user.organization_id,
                body=jsonable_encoder({"members": [user_id_to_remove]}),
            )
        except Exception as e:
            logger.error(
                f"Something went wrong removing the member {user.user_id} from the organization {user.organization_id}"
            )
            raise e

    def delete_invitation(
        self: "Auth0Service", user: UserToken, invitation_id: str
    ) -> any:
        self.verify_org_management_permissions(user)
        try:
            mgmt_api_token = self.get_mgmt_api_token()
            management_api = Auth0(self.auth0_mgmt_domain, mgmt_api_token)
            return management_api.organizations.delete_organization_invitation(
                id=user.organization_id, invitation_id=invitation_id
            )
        except Exception as e:
            logger.error(
                f"Something went wrong revoking invitation id = {invitation_id} from the organization {user.organization_id}"
            )
            raise e

    def get_user_profile(self, user_id: str) -> dict[str, any]:
        """
        Return a single user profile from Auth0 Management API.
        """
        client = self._management_client()
        return client.users.get(user_id)

    def get_organization(self, org_id: str) -> dict[str, any]:
        """
        Return the Auth0 Organization object for *org_id*.

        Requires the Management API scope:  read:organizations
        """
        client = self._management_client()
        return client.organizations.get_organization(org_id)

    # ------------------------------------------------------------------
    #  Public signup helpers (no existing user context)
    # ------------------------------------------------------------------

    def create_organization(self, name: str, display_name: str) -> dict[str, any]:
        """
        Create an Auth0 Organization.

        Requires Management API scope: create:organizations
        """
        client = self._management_client()
        body = jsonable_encoder({
            "name": name,
            "display_name": display_name,
        })
        return client.organizations.create_organization(body)

    def delete_organization(self, org_id: str) -> None:
        """Delete an Auth0 Organization. Best-effort; logs errors."""
        try:
            client = self._management_client()
            delete_method = getattr(client.organizations, "delete_organization", None)
            if callable(delete_method):
                delete_method(org_id)
            else:
                # Some SDKs use `delete(id=...)` signature
                generic_delete = getattr(client.organizations, "delete", None)
                if callable(generic_delete):
                    generic_delete(id=org_id)
                else:
                    raise RuntimeError("auth0-python SDK lacks delete organization method")
        except Exception:
            logger.error(f"Failed to delete organization {org_id}", exc_info=True)

    def invite_email_to_organization(
        self,
        org_id: str,
        email: str,
        roles: list[str] | None = None,
        inviter_name: str | None = None,
        send_invitation_email: bool = True,
    ) -> dict[str, any]:
        """
        Create an organization invitation for an email address.

        Requires Management API scopes: create:organization_invitations
        """
        client = self._management_client()
        # Optionally include SSO connection if present in org metadata
        org = client.organizations.get_organization(org_id)
        payload: dict[str, any] = {
            "inviter": {"name": inviter_name or "System"},
            "invitee": {"email": email},
            "client_id": settings.AUTH0_CLIENT_ID,
        }
        # Suppress Auth0 emailing the invite if requested
        if send_invitation_email is False:
            payload["send_invitation_email"] = False
        if roles:
            payload["roles"] = roles
        if "metadata" in org and isinstance(org["metadata"], dict):
            connection_id = org["metadata"].get("sso_connection_id")
            if connection_id:
                payload["connection_id"] = connection_id

        return client.organizations.create_organization_invitation(
            id=org_id, body=jsonable_encoder(payload)
        )

    # ------------------------------------------------------------------
    #  Organization Connection helpers
    # ------------------------------------------------------------------

    def get_connection_id_by_name(self, name: str) -> str | None:
        """Return a connection ID for a given connection name, or None if not found."""
        try:
            client = self._management_client()
            page = 0
            per_page = 50
            while True:
                connections = client.connections.all(page=page, per_page=per_page)
                if not connections:
                    return None
                for conn in connections:
                    if conn.get("name") == name:
                        return conn.get("id")
                if len(connections) < per_page:
                    return None
                page += 1
        except Exception:
            logger.error("Error listing connections", exc_info=True)
            return None

    def enable_connection_for_organization(self, org_id: str, connection_id: str) -> None:
        """
        Enable a connection on an organization.

        Requires Management API scopes: update:organizations, read:connections
        """
        try:
            # Direct HTTP call to Management API; The auth0-python SDK does not expose this method (yet).
            mgmt_token = self.get_mgmt_api_token()
            url = f"https://{self.auth0_mgmt_domain}/api/v2/organizations/{org_id}/enabled_connections"
            body = {
                "connection_id": connection_id,
                "assign_membership_on_login": False,
            }
            headers = {
                "Authorization": f"Bearer {mgmt_token}",
                "Content-Type": "application/json",
            }
            resp = requests.post(url, json=body, headers=headers, timeout=15)
            if resp.status_code in (200, 201, 409):  # 409 = already enabled
                return
            resp.raise_for_status()
        except Exception:
            logger.error(
                f"Error enabling connection {connection_id} for organization {org_id}",
                exc_info=True,
            )
            raise
