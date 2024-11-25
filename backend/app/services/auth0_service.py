import logging

from auth0.authentication import Database, GetToken, Users
from auth0.management import Auth0
from fastapi.encoders import jsonable_encoder

from app.api.auth import ORG_MANAGER, UserToken
from app.core.config import settings
from app.schemas.auth0_schema import (
    CreateInvitationInput,
    ModifyUserRolesResponse,
)

logger = logging.getLogger(__name__)


class Auth0Service:
    def __init__(
        self: "Auth0Service",
    ) -> None:
        self.auth0_mgmt_domain = settings.AUTH0_MGMT_API_DOMAIN
        self.auth0_mgmt_client_id = settings.AUTH0_MGMT_API_CLIENT_ID
        self.auth0_mgmt_client_secret = settings.AUTH0_MGMT_API_CLIENT_SECRET
        self.auth0_domain = settings.AUTH0_DOMAIN
        self.auth0_client_id = settings.AUTH0_CLIENT_ID

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
                f"User requested password reset for {user.subject} sent to {user_profile.get("email")}"
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
            invitation_results = []
            for invitation in invitations.invitations:
                print(invitation)
                invitation_results.append(
                    management_api.organizations.create_organization_invitation(
                        id=user.organization_id,
                        body=jsonable_encoder(
                            # The Auth0 API lets you set whatever name you want - hide that detail
                            # here in our API and always set it to Driver Support. **invitation
                            # doesn't work on a basemodel
                            {
                                "inviter": {"name": userinfo.get("name")},
                                "invitee": invitation.invitee,
                                "roles": invitation.roles,
                                "client_id": settings.AUTH0_CLIENT_ID,
                            }
                        ),
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
