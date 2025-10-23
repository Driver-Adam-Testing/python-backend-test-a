"""Service for RBAC Member Search business logic."""

import logging

from database.models import OrgMembership, Team, User
from sqlmodel import Session, func, or_, select

from app.schemas.rbac_search_schema import (
    MemberSearchItem,
    MemberSearchResponse,
)

logger = logging.getLogger(__name__)


def search_users_in_organization(
    session: Session,
    organization_id: str,
    query: str,
    limit: int,
) -> list[User]:
    """
    Search for users in an organization.

    Args:
        session: Database session
        organization_id: Organization ID
        query: Search query
        limit: Maximum number of results

    Returns:
        List of matching users
    """
    search_pattern = f"%{query}%"
    user_query = (
        select(User)
        .join(OrgMembership, User.id == OrgMembership.user_id)
        .where(
            OrgMembership.org_id == organization_id,
            or_(
                User.name.ilike(search_pattern),
                User.email.ilike(search_pattern),
            ),
        )
        .order_by(User.name)
        .limit(limit)
    )

    return list(session.exec(user_query).all())


def search_teams_in_organization(
    session: Session,
    organization_id: str,
    query: str,
    limit: int,
) -> list[Team]:
    """
    Search for teams in an organization.

    Args:
        session: Database session
        organization_id: Organization ID
        query: Search query
        limit: Maximum number of results

    Returns:
        List of matching teams
    """
    search_pattern = f"%{query}%"
    team_query = (
        select(Team)
        .where(
            Team.organization_id == organization_id,
            Team.name.ilike(search_pattern),
        )
        .order_by(Team.name)
        .limit(limit)
    )

    return list(session.exec(team_query).all())


def count_users_in_organization(
    session: Session,
    organization_id: str,
    query: str,
) -> int:
    """
    Count users matching search query in an organization.

    Args:
        session: Database session
        organization_id: Organization ID
        query: Search query

    Returns:
        Count of matching users
    """
    search_pattern = f"%{query}%"
    count_query = (
        select(func.count())
        .select_from(User)
        .join(OrgMembership, User.id == OrgMembership.user_id)
        .where(
            OrgMembership.org_id == organization_id,
            or_(
                User.name.ilike(search_pattern),
                User.email.ilike(search_pattern),
            ),
        )
    )

    return session.exec(count_query).one()


def count_teams_in_organization(
    session: Session,
    organization_id: str,
    query: str,
) -> int:
    """
    Count teams matching search query in an organization.

    Args:
        session: Database session
        organization_id: Organization ID
        query: Search query

    Returns:
        Count of matching teams
    """
    search_pattern = f"%{query}%"
    count_query = (
        select(func.count())
        .select_from(Team)
        .where(
            Team.organization_id == organization_id,
            Team.name.ilike(search_pattern),
        )
    )

    return session.exec(count_query).one()


class RBACSearchService:
    """Service for RBAC member search operations."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def search_members(
        self,
        organization_id: str,
        query: str,
        limit: int = 30,
        offset: int = 0,
    ) -> MemberSearchResponse:
        """
        Search for members (users and teams) in an organization.

        This endpoint searches both users (by name/email) and teams (by name)
        and returns combined results, useful for adding members to sources.

        Args:
            organization_id: Organization ID
            query: Search query (case-insensitive)
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            MemberSearchResponse with combined user and team results
        """
        logger.info(
            f"Searching members for organization {organization_id} "
            f"with query '{query}' (limit={limit}, offset={offset})"
        )

        # Calculate how many results to fetch from each source
        # We'll fetch more than needed and then apply offset/limit on combined results
        fetch_limit = limit + offset + 50  # Buffer to ensure we have enough results

        # Search users
        users = search_users_in_organization(
            session=self.session,
            organization_id=organization_id,
            query=query,
            limit=fetch_limit,
        )

        # Search teams
        teams = search_teams_in_organization(
            session=self.session,
            organization_id=organization_id,
            query=query,
            limit=fetch_limit,
        )

        # Convert to search items
        user_items = [
            MemberSearchItem(
                member_id=user.id,
                kind="user",
                name=user.name or "",
                email=user.email or "",
                picture="",  # TODO: Fetch from Auth0 or add to User model
            )
            for user in users
        ]

        team_items = [
            MemberSearchItem(
                member_id=str(team.id),
                kind="team",
                name=team.name,
                email=None,
                picture=None,
            )
            for team in teams
        ]

        # Combine and sort by name (case-insensitive)
        all_items = sorted(
            user_items + team_items,
            key=lambda x: x.name.lower(),
        )

        # Get total count
        user_count = count_users_in_organization(
            session=self.session,
            organization_id=organization_id,
            query=query,
        )

        team_count = count_teams_in_organization(
            session=self.session,
            organization_id=organization_id,
            query=query,
        )

        total = user_count + team_count

        # Apply pagination to combined results
        paginated_items = all_items[offset : offset + limit]

        logger.info(
            f"Found {len(paginated_items)} members "
            f"({user_count} users, {team_count} teams, total: {total})"
        )

        return MemberSearchResponse(
            items=paginated_items,
            total=total,
        )
