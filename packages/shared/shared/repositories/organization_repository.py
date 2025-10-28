"""Repository for organization membership and role operations."""

from database.models import OrgMembership
from database.models_enums import OrgRole
from sqlmodel import Session, select


def list_organization_roles() -> list[dict[str, str]]:
    """
    List all available organization roles.

    Returns:
        List of dictionaries with 'id' and 'name' keys for each role
    """
    roles = []
    for role in OrgRole:
        role_name = role.value.replace("_", " ").title()
        roles.append({"id": role.value, "name": role_name})
    return roles


def get_organization_member_roles(
    session: Session,
    organization_id: str,
) -> dict[str, str]:
    """
    Get role mappings for all users in an organization.

    Args:
        session: Database session
        organization_id: Organization ID

    Returns:
        Dictionary mapping user_id to role value (e.g., {"auth0|user1": "super_admin"})
    """
    query = select(OrgMembership).where(OrgMembership.org_id == organization_id)
    memberships = session.exec(query).all()

    return {membership.user_id: membership.role.value for membership in memberships}


def get_user_organization_role(
    session: Session,
    user_id: str,
    organization_id: str,
) -> str | None:
    """
    Get the organization role for a specific user.

    Args:
        session: Database session
        user_id: User ID (Auth0 user ID)
        organization_id: Organization ID

    Returns:
        Role value string or None if not found
    """
    query = select(OrgMembership).where(
        OrgMembership.user_id == user_id,
        OrgMembership.org_id == organization_id,
    )
    membership = session.exec(query).first()

    return membership.role.value if membership else None
