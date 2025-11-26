import logging
from datetime import UTC, datetime

from database.models_enums import OrgRole
from fastapi import APIRouter, Header, HTTPException, Query

from app.api.auth import UserToken
from app.api.session import CurrentSession
from app.authorization.fastapi import enforce_org_action
from app.schemas.auth0_schema import CreateInvitationInput
from app.schemas.organization_schema import (
    BulkSetUserRoleInput,
    BulkSetUserRoleResponse,
    ListMembersResponse,
    OrganizationMember,
    SetUserRoleInput,
    SetUserRoleResponse,
)
from app.services.auth0_factory import create_auth0_service
from app.services.onboarding_checklist_service import OnboardingChecklistService
from app.services.organizations_service import OrganizationsService

router = APIRouter()

logger = logging.getLogger(__name__)


@router.get("/users", status_code=200)
def list_members(
    session: CurrentSession,
    user: UserToken,
    limit: int = Query(
        default=100, ge=1, le=100, description="Maximum number of results"
    ),
    offset: int = Query(default=0, ge=0, description="Number of results to skip"),
    search: str | None = Query(default=None, description="Search by name or email"),
    roles: list[OrgRole] | None = Query(
        default=None, description="Filter by organization roles"
    ),
) -> ListMembersResponse:
    enforce_org_action(session, user, "users.view")
    logger.info(f"Listing members of organization = {user.organization_id}")
    organizations_service = OrganizationsService(session)
    return organizations_service.list_members(
        user, limit=limit, offset=offset, search=search, roles=roles
    )


@router.get("/users/{user_id}", status_code=200)
def get_member(
    session: CurrentSession,
    user: UserToken,
    user_id: str,
) -> OrganizationMember:
    enforce_org_action(session, user, "users.view")
    logger.info(f"Getting member {user_id} from organization = {user.organization_id}")
    organizations_service = OrganizationsService(session)
    return organizations_service.get_member(user, user_id)


@router.delete("/users/{user_id}", status_code=204)
def delete_member(
    session: CurrentSession,
    user: UserToken,
    user_id: str,
) -> None:
    enforce_org_action(session, user, "users.manage")
    logger.info(f"Deleting {user_id} from {user.organization_id}")
    organizations_service = OrganizationsService(session)
    organizations_service.delete_member(user, user_id)


@router.put("/users/role", status_code=200)
def bulk_change_user_roles(
    session: CurrentSession,
    user: UserToken,
    bulk_input: BulkSetUserRoleInput,
) -> BulkSetUserRoleResponse:
    enforce_org_action(session, user, "users.manage")
    logger.info(
        f"Bulk updating {len(bulk_input.members)} user roles in {user.organization_id}"
    )
    try:
        organizations_service = OrganizationsService(session)
        return organizations_service.bulk_update_member_roles(user, bulk_input)
    except ValueError as e:
        logger.error(f"Validation error in bulk role update: {e}")
        raise HTTPException(400, str(e))


@router.put(
    "/users/{modified_user_id}/role",
    status_code=200,
)
def change_user_roles(
    session: CurrentSession,
    user: UserToken,
    modified_user_id: str,
    role_input: SetUserRoleInput,
) -> SetUserRoleResponse:
    enforce_org_action(session, user, "users.manage")
    logger.info(f"Setting role for {modified_user_id} in {user.organization_id}")
    try:
        organizations_service = OrganizationsService(session)
        return organizations_service.update_member_role(
            user, modified_user_id, role_input.role
        )
    except ValueError as e:
        logger.error(f"Validation error setting user role: {e}")
        raise HTTPException(400, str(e))


@router.get("/invitations", status_code=200)
def list_invitations(  # noqa: ANN201 disable to proxy Auth0 any typed responses
    session: CurrentSession,
    user: UserToken,
    page: int = 0,
    per_page: int = 100,
):
    enforce_org_action(session, user, "invitations.manage")
    logger.info(f"Listing invitations for organization = {user.organization_id}")
    auth0_service = create_auth0_service()
    return auth0_service.list_invitations(user, page=page, per_page=per_page)


@router.post("/invitations", status_code=201)
def create_invitation(  # noqa: ANN201 disable to proxy Auth0 any typed responses
    session: CurrentSession,
    user: UserToken,
    invitations: CreateInvitationInput,
    authorization: str | None = Header(None),
):
    enforce_org_action(session, user, "invitations.manage")
    logger.info(f"Creating invitations for organization = {user.organization_id}")
    access_token = authorization.replace("Bearer ", "")
    auth0_service = create_auth0_service()
    result = auth0_service.create_invitation(
        user, access_token=access_token, invitations=invitations
    )

    # Update onboarding checklist
    OnboardingChecklistService.get_or_create_checklist(
        session=session,
        organization_id=user.organization_id,
        user_id=user.user_id,
    ).mark_invite_teammate_completed(datetime.now(UTC))

    return result


@router.delete("/invitations/{invitation_id}", status_code=204)
def revoke_invitation(  # noqa: ANN201 disable to proxy Auth0 any typed responses
    session: CurrentSession,
    user: UserToken,
    invitation_id: str,
):
    enforce_org_action(session, user, "invitations.manage")
    logger.info(f"Revoking invitation {invitation_id} from {user.organization_id}")
    auth0_service = create_auth0_service()
    return auth0_service.delete_invitation(user, invitation_id=invitation_id)
