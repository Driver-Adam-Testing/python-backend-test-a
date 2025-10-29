"""Repository functions for Organization Membership data access."""

from database.models_enums import OrgRole
from database.models import OrgMembership, User
from sqlmodel import Session, select, col


def check_user_in_organization(
    session: Session,
    user_id: str,
    organization_id: str,
) -> bool:
    """
    Check if a user is a member of an organization.

    Args:
        session: Database session
        user_id: User ID (Auth0 ID)
        organization_id: Organization ID

    Returns:
        True if user is a member of the organization, False otherwise
    """
    query = select(OrgMembership).where(
        OrgMembership.user_id == user_id,
        OrgMembership.org_id == organization_id,
    )
    membership = session.exec(query).first()
    return membership is not None


def get_org_membership(
    session: Session,
    user_id: str,
    organization_id: str,
) -> OrgMembership | None:
    """
    Get organization membership for a user.

    Args:
        session: Database session
        user_id: User ID (Auth0 ID)
        organization_id: Organization ID

    Returns:
        OrgMembership or None if not found
    """
    query = select(OrgMembership).where(
        OrgMembership.user_id == user_id,
        OrgMembership.org_id == organization_id,
    )
    return session.exec(query).first()

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


def list_organization_members(
    session: Session,
    organization_id: str,
    page: int = 0,
    per_page: int = 100,
) -> tuple[list[dict[str, str | None]], int]:
    """
    List all members of an organization with their user details and roles.

    Args:
        session: Database session
        organization_id: Organization ID
        page: Page number (0-indexed)
        per_page: Number of results per page

    Returns:
        Tuple of (members_list, total_count) where:
        - members_list: List of dictionaries with user_id, email, name, and role
        - total_count: Total number of members in the organization
    """
    # Get total count
    count_query = (
        select(OrgMembership)
        .where(OrgMembership.org_id == organization_id)
    )
    total_count = len(session.exec(count_query).all())

    # Get paginated results
    query = (
        select(User.id, User.email, User.name, OrgMembership.role)
        .join(OrgMembership, User.id == OrgMembership.user_id)
        .where(OrgMembership.org_id == organization_id)
        .order_by(col(User.name).nullslast())
        .offset(page * per_page)
        .limit(per_page)
    )

    results = session.exec(query).all()

    members = [
        {
            "user_id": row.id,
            "email": row.email,
            "name": row.name,
            "role": row.role.value,
        }
        for row in results
    ]

    return members, total_count