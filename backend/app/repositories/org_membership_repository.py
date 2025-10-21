"""Repository functions for Organization Membership data access."""

from database.models import OrgMembership
from sqlmodel import Session, select


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
