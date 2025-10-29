"""Test data factories for integration tests."""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from database.models import (
    OrgMembership,
    PrimaryAsset,
    PrimaryAssetRoleGrant,
    Team,
    TeamMembership,
    User,
)
from database.models_enums import (
    OrgRole,
    PrimaryAssetKind,
    PrimaryAssetProvider,
    PrimaryAssetRole,
    PrincipalKind,
    TeamRole,
)
from sqlmodel import Session


class TeamFactory:
    """Factory for creating test teams."""

    @staticmethod
    def create(
        session: Session,
        name: str | None = None,
        organization_id: str = "test-org-id",
        **kwargs: Any,
    ) -> Team:
        """Create a team in the database."""
        defaults = {
            "id": uuid4(),
            "name": name or f"Test Team {uuid4().hex[:8]}",
            "organization_id": organization_id,
        }
        team = Team(**(defaults | kwargs))
        session.add(team)
        session.commit()
        session.refresh(team)
        return team


class Auth0UserFactory:
    """Factory for creating test users."""

    @staticmethod
    def create(
        session: Session,
        user_id: str | None = None,
        email: str | None = None,
        name: str | None = None,
        organization_id: str = "test-org-id",
        org_role: OrgRole = OrgRole.member,
        **kwargs: Any,
    ) -> User:
        """Create a user in the database and add them to the organization."""
        user_id = user_id or f"auth0|{uuid4().hex[:16]}"
        defaults = {
            "id": user_id,  # User model uses 'id' not 'user_id'
            "email": email or f"user-{uuid4().hex[:8]}@test.com",
            "name": name or f"Test User {uuid4().hex[:8]}",
            "created_at": datetime.now(UTC),
            "auth0_updated_at": datetime.now(UTC),
        }
        user = User(**(defaults | kwargs))
        session.add(user)
        session.commit()
        session.refresh(user)

        # Create org membership
        org_membership = OrgMembership(
            id=uuid4(),
            org_id=organization_id,
            user_id=user.id,
            role=org_role,
        )
        session.add(org_membership)
        session.commit()

        return user


class TeamMembershipFactory:
    """Factory for creating test team memberships."""

    @staticmethod
    def create(
        session: Session,
        team_id: UUID,
        user_id: str,
        role: TeamRole = TeamRole.member,
        organization_id: str = "test-org-id",  # Kept for API compatibility but not used
        **kwargs: Any,
    ) -> TeamMembership:
        """Create a team membership in the database.

        Note: organization_id parameter is kept for backward compatibility but is not
        used since TeamMembership model doesn't have that field.
        """
        defaults = {
            "id": uuid4(),
            "team_id": team_id,
            "user_id": user_id,
            "role": role,
        }
        membership = TeamMembership(**(defaults | kwargs))
        session.add(membership)
        session.commit()
        session.refresh(membership)
        return membership


class PrimaryAssetFactory:
    """Factory for creating test primary assets (sources)."""

    @staticmethod
    def create(
        session: Session,
        display_name: str | None = None,
        kind: PrimaryAssetKind = PrimaryAssetKind.CODEBASE,
        provider: PrimaryAssetProvider = PrimaryAssetProvider.USER,
        organization_id: str = "test-org-id",
        **kwargs: Any,
    ) -> PrimaryAsset:
        """Create a primary asset in the database."""
        defaults = {
            "id": uuid4(),
            "display_name": display_name or f"Test Source {uuid4().hex[:8]}",
            "kind": kind,
            "provider": provider,
            "organization_id": organization_id,
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
        }
        asset = PrimaryAsset(**(defaults | kwargs))
        session.add(asset)
        session.commit()
        session.refresh(asset)
        return asset


class PrimaryAssetRoleGrantFactory:
    """Factory for creating test access grants."""

    @staticmethod
    def create(
        session: Session,
        primary_asset_id: UUID,
        principal_kind: PrincipalKind,
        role: PrimaryAssetRole = PrimaryAssetRole.viewer,
        organization_id: str = "test-org-id",
        user_id: str | None = None,
        team_id: UUID | None = None,
        **kwargs: Any,
    ) -> PrimaryAssetRoleGrant:
        """Create an access grant in the database."""
        defaults = {
            "id": uuid4(),
            "primary_asset_id": primary_asset_id,
            "principal_kind": principal_kind,
            "role": role,
            "organization_id": organization_id,
            "user_id": user_id,
            "team_id": team_id,
            "created_at": datetime.now(UTC),
        }
        grant = PrimaryAssetRoleGrant(**(defaults | kwargs))
        session.add(grant)
        session.commit()
        session.refresh(grant)
        return grant
