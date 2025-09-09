import logging

from fastapi import APIRouter, Header, HTTPException

from app.api.auth import OrgManagerPermission, UserToken
from app.api.session import CurrentSession
from app.schemas.auth0_schema import (
    CreateInvitationInput,
    ModifyUserRolesInput,
    ModifyUserRolesResponse,
)
from app.services.auth0_service import Auth0Service
from app.services.onboarding_checklist_service import OnboardingChecklistService

router = APIRouter()

logger = logging.getLogger(__name__)


@router.get("/roles", status_code=200, dependencies=[OrgManagerPermission])
def list_roles(  # noqa: ANN201 disable to proxy Auth0 any typed responses
    user: UserToken,
    page: int = 0,
    per_page: int = 100,
):
    logging.info(f"Listing members of organization = {user.organization_id}")
    try:
        auth0_service = Auth0Service()
        return auth0_service.list_roles(page=page, per_page=per_page)
    except Exception as e:
        logger.error(f"An error occurred listing roles: {e}")
        raise HTTPException(500, "Unable to list roles.")


@router.get("/users", status_code=200, dependencies=[OrgManagerPermission])
def list_members(  # noqa: ANN201 disable to proxy Auth0 any typed responses
    user: UserToken,
    page: int = 0,
    per_page: int = 100,
):
    logging.info(f"Listing members of organization = {user.organization_id}")
    try:
        auth0_service = Auth0Service()
        return auth0_service.list_members(user, page=page, per_page=per_page)
    except PermissionError:
        raise HTTPException(403, "Insufficient permissions.")
    except Exception as e:
        logger.error(f"An error occurred listing members of an organization: {e}")
        raise HTTPException(500, "Unable to list organization members.")


@router.delete("/users/{user_id}", status_code=204, dependencies=[OrgManagerPermission])
def delete_member(user: UserToken, user_id: str):  # noqa: ANN201 disable to proxy Auth0 any typed responses
    logging.info(f"DELETING {user_id} from {user.organization_id}")
    try:
        auth0_service = Auth0Service()
        return auth0_service.delete_user_from_organization(user, user_id)
    except PermissionError:
        raise HTTPException(403, "Insufficient permissions.")
    except Exception as e:
        logger.error(f"An error occurred removing a member from an organization: {e}")
        raise HTTPException(500, "Unable to remove organization members.")


@router.put(
    "/users/{modified_user_id}/roles",
    status_code=200,
    dependencies=[OrgManagerPermission],
)
def change_user_roles(
    user: UserToken, modified_user_id: str, new_roles: ModifyUserRolesInput
) -> ModifyUserRolesResponse:
    logging.info(f"Modifying roles for {modified_user_id} in {user.organization_id}")
    try:
        auth0_service = Auth0Service()
        return auth0_service.modify_user_roles(
            user=user, modified_user_id=modified_user_id, roles=new_roles.roles
        )
    except PermissionError:
        raise HTTPException(403, "Insufficient permissions.")
    except Exception as e:
        logger.error(f"An error occurred modifying member roles: {e}")
        raise HTTPException(500, "Unable to modify member roles.")


@router.get("/invitations", status_code=200, dependencies=[OrgManagerPermission])
def list_invitations(  # noqa: ANN201 disable to proxy Auth0 any typed responses
    user: UserToken,
    page: int = 0,
    per_page: int = 100,
):
    logging.info(f"Listing members of organization = {user.organization_id}")
    try:
        auth0_service = Auth0Service()
        return auth0_service.list_invitations(user, page=page, per_page=per_page)
    except PermissionError:
        raise HTTPException(403, "Insufficient permissions.")
    except Exception as e:
        logger.error(
            f"An error occurred listing invitations to an organization: {e}",
            exc_info=True,
        )
        raise HTTPException(500, "Unable to list organization invitations.")


@router.post("/invitations", status_code=201, dependencies=[OrgManagerPermission])
def create_invitation(  # noqa: ANN201 disable to proxy Auth0 any typed responses
    user: UserToken,
    invitations: CreateInvitationInput,
    authorization: str | None = Header(None),
    session: CurrentSession = None,
):
    logging.info(f"Listing members of organization = {user.organization_id}")
    access_token = authorization.replace("Bearer ", "")
    try:
        auth0_service = Auth0Service()
        result = auth0_service.create_invitation(
            user, access_token=access_token, invitations=invitations
        )

        # Best-effort update of onboarding checklist
        try:
            OnboardingChecklistService(
                session=session,
                organization_id=user.organization_id,
                user_id=user.user_id,
            ).mark_invite_teammate_completed()
        except Exception as e:  # pragma: no cover - non-critical path
            logger.error(
                f"Failed to update onboarding checklist for invitations: {e}",
                exc_info=True,
            )

        return result
    except PermissionError:
        raise HTTPException(403, "Insufficient permissions.")
    except Exception as e:
        logger.error(f"An error occurred creating invitations to an organization: {e}")
        raise HTTPException(500, "Unable to create org invitation(s).")


@router.delete(
    "/invitations/{invitation_id}", status_code=204, dependencies=[OrgManagerPermission]
)
def revoke_invitation(  # noqa: ANN201 disable to proxy Auth0 any typed responses
    user: UserToken, invitation_id: str
):
    logging.info(f"REVOKING invitation {invitation_id} from {user.organization_id}")
    try:
        auth0_service = Auth0Service()
        return auth0_service.delete_invitation(user, invitation_id=invitation_id)
    except PermissionError:
        raise HTTPException(403, "Insufficient permissions.")
    except Exception as e:
        logger.error(f"An error occurred revoking an invitation: {e}")
        raise HTTPException(500, "Unable to revoke invitation.")
