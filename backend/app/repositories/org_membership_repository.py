"""Repository functions for Organization Membership data access."""

from database.models import OrgMembership, User
from database.models_enums import OrgRole
from sqlmodel import Session, col, select


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
        Dictionary mapping user_id to role value (e.g., {"auth0|user1": "org_super_admin"})
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
    limit: int = 100,
    offset: int = 0,
    search: str | None = None,
    roles: list[OrgRole] | None = None,
) -> tuple[
    list[dict[str, str | None]], int
]:  # TODO: gross return type. use proper types
    base_conditions = [OrgMembership.org_id == organization_id]

    if search:
        search_term = f"%{search}%"
        base_conditions.append(
            (col(User.name).ilike(search_term)) | (col(User.email).ilike(search_term))
        )

    if roles:
        base_conditions.append(OrgMembership.role.in_(roles))

    count_query = (
        select(OrgMembership)
        .join(User, User.id == OrgMembership.user_id)
        .where(*base_conditions)
    )
    total_count = len(session.exec(count_query).all())

    query = (
        select(User.id, User.email, User.name, OrgMembership.role)
        .join(OrgMembership, User.id == OrgMembership.user_id)
        .where(*base_conditions)
        .order_by(col(User.name).nullslast())
        .offset(offset)
        .limit(limit)
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


def bulk_update_organization_roles(
    session: Session,
    organization_id: str,
    role_updates: list[tuple[str, OrgRole]],
) -> list[OrgMembership]:
    """
    Update multiple users' organization roles in a single transaction.

    All updates are applied atomically - either all succeed or all fail.
    This ensures data consistency when updating multiple roles at once.

    Args:
        session: Database session
        organization_id: Organization ID
        role_updates: List of (user_id, new_role) tuples to update

    Returns:
        List of updated OrgMembership objects

    Raises:
        ValueError: If any user is not a member of the organization
    """
    if not role_updates:
        return []

    # Extract user IDs
    user_ids = [user_id for user_id, _ in role_updates]

    # Fetch all memberships in a single query
    query = select(OrgMembership).where(
        OrgMembership.org_id == organization_id,
        OrgMembership.user_id.in_(user_ids),
    )
    memberships = session.exec(query).all()

    # Create a mapping of user_id to membership
    membership_map = {m.user_id: m for m in memberships}

    # Validate all users exist in the organization
    missing_users = [uid for uid in user_ids if uid not in membership_map]
    if missing_users:
        raise ValueError(f"Users not found in organization: {', '.join(missing_users)}")

    # Update all roles
    updated_memberships = []
    for user_id, new_role in role_updates:
        membership = membership_map[user_id]
        membership.role = new_role
        session.add(membership)
        updated_memberships.append(membership)

    # Commit all changes at once
    session.commit()

    # Refresh all updated memberships
    for membership in updated_memberships:
        session.refresh(membership)

    return updated_memberships
