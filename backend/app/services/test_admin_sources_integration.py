"""
Integration tests for Admin Sources service.

These tests verify visibility calculation and filtering logic.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from database.models_enums import PrimaryAssetRole, PrincipalKind

from app.services.admin_sources_service import AdminSourcesService
from app.test_factories import (
    Auth0UserFactory,
    PrimaryAssetFactory,
    PrimaryAssetRoleGrantFactory,
)

if TYPE_CHECKING:
    from sqlmodel import Session

    from app.auth.models import User


def create_mock_user(organization_id: str, user_id: str = "test-user-id") -> User:
    """Create a mock User object for testing."""
    from app.auth.models import User

    return User(
        org_id=organization_id,
        org_name="Test Organization",
        sub=user_id,
        iss="https://test.auth0.com/",
        aud=["test-audience"],
        iat=1234567890,
        exp=9999999999,
        scope="",
        azp="",
        permissions=[],
        user_email="test@example.com",
        user_full_name="Test User",
    )


@pytest.mark.integration
class TestAdminSourcesVisibility:
    """Test visibility calculation for admin sources."""

    def test_private_source_has_no_org_or_public_grant(
        self, integration_db_session: Session
    ) -> None:
        """
        Test that a source with no org/public grant shows as 'private'.

        1. Create a user and make them admin of a source
        2. Source has no org-level or public grant
        3. Query admin sources
        4. Verify visibility = 'private'
        """
        org_id = "test-org-id"
        user = Auth0UserFactory.create(integration_db_session, organization_id=org_id)
        mock_user = create_mock_user(org_id, user.id)

        source = PrimaryAssetFactory.create(
            integration_db_session,
            display_name="Private Source",
            organization_id=org_id,
        )
        PrimaryAssetRoleGrantFactory.create(
            integration_db_session,
            primary_asset_id=source.id,
            principal_kind=PrincipalKind.user,
            role=PrimaryAssetRole.asset_admin,
            organization_id=org_id,
            user_id=user.id,
        )

        service = AdminSourcesService(integration_db_session)
        response = service.get_admin_sources(
            user=mock_user,
            limit=10,
            offset=0,
        )

        assert response.total_count == 1
        assert len(response.results) == 1
        assert response.results[0].visibility == "private"
        assert response.results[0].display_name == "Private Source"

    def test_internal_source_has_org_grant(
        self, integration_db_session: Session
    ) -> None:
        """
        Test that a source with org-level grant shows as 'internal'.

        Steps:
        1. Create a user and make them admin of a source
        2. Add org-level grant to the source
        3. Query admin sources
        4. Verify visibility = 'internal'
        """
        org_id = "test-org-id"
        user = Auth0UserFactory.create(integration_db_session, organization_id=org_id)
        mock_user = create_mock_user(org_id, user.id)

        # Create source with user as admin
        source = PrimaryAssetFactory.create(
            integration_db_session,
            display_name="Internal Source",
            organization_id=org_id,
        )
        PrimaryAssetRoleGrantFactory.create(
            integration_db_session,
            primary_asset_id=source.id,
            principal_kind=PrincipalKind.user,
            role=PrimaryAssetRole.asset_admin,
            organization_id=org_id,
            user_id=user.id,
        )

        # Add org-level grant
        PrimaryAssetRoleGrantFactory.create(
            integration_db_session,
            primary_asset_id=source.id,
            principal_kind=PrincipalKind.org,
            role=PrimaryAssetRole.asset_member,
            organization_id=org_id,
        )

        service = AdminSourcesService(integration_db_session)
        response = service.get_admin_sources(
            user=mock_user,
            limit=10,
            offset=0,
        )

        assert response.total_count == 1
        assert len(response.results) == 1
        assert response.results[0].visibility == "internal"
        assert response.results[0].display_name == "Internal Source"

    def test_public_source_has_public_grant(
        self, integration_db_session: Session
    ) -> None:
        """
        Test that a source with public grant shows as 'public'.

        1. Create a user and make them admin of a source
        2. Add public grant to the source
        3. Query admin sources
        4. Verify visibility = 'public'
        """
        org_id = "test-org-id"
        user = Auth0UserFactory.create(integration_db_session, organization_id=org_id)
        mock_user = create_mock_user(org_id, user.id)

        # Create source with user as admin
        source = PrimaryAssetFactory.create(
            integration_db_session,
            display_name="Public Source",
            organization_id=org_id,
        )
        PrimaryAssetRoleGrantFactory.create(
            integration_db_session,
            primary_asset_id=source.id,
            principal_kind=PrincipalKind.user,
            role=PrimaryAssetRole.asset_admin,
            organization_id=org_id,
            user_id=user.id,
        )

        # Add public grant
        PrimaryAssetRoleGrantFactory.create(
            integration_db_session,
            primary_asset_id=source.id,
            principal_kind=PrincipalKind.public,
            role=PrimaryAssetRole.asset_member,
            organization_id=org_id,
        )

        # Query admin sources
        service = AdminSourcesService(integration_db_session)
        response = service.get_admin_sources(
            user=mock_user,
            limit=10,
            offset=0,
        )

        assert response.total_count == 1
        assert len(response.results) == 1
        assert response.results[0].visibility == "public"
        assert response.results[0].display_name == "Public Source"

    def test_public_takes_precedence_over_internal(
        self, integration_db_session: Session
    ) -> None:
        """
        Test that public visibility takes precedence when both org and public grants exist.

        1. Create a source with both org and public grants
        2. Query admin sources
        3. Verify visibility = 'public' (not 'internal')
        """
        org_id = "test-org-id"
        user = Auth0UserFactory.create(integration_db_session, organization_id=org_id)
        mock_user = create_mock_user(org_id, user.id)

        # Create source with user as admin
        source = PrimaryAssetFactory.create(
            integration_db_session,
            display_name="Public and Internal Source",
            organization_id=org_id,
        )
        PrimaryAssetRoleGrantFactory.create(
            integration_db_session,
            primary_asset_id=source.id,
            principal_kind=PrincipalKind.user,
            role=PrimaryAssetRole.asset_admin,
            organization_id=org_id,
            user_id=user.id,
        )

        # Add org grant
        PrimaryAssetRoleGrantFactory.create(
            integration_db_session,
            primary_asset_id=source.id,
            principal_kind=PrincipalKind.org,
            role=PrimaryAssetRole.asset_member,
            organization_id=org_id,
        )

        # Add public grant
        PrimaryAssetRoleGrantFactory.create(
            integration_db_session,
            primary_asset_id=source.id,
            principal_kind=PrincipalKind.public,
            role=PrimaryAssetRole.asset_member,
            organization_id=org_id,
        )

        service = AdminSourcesService(integration_db_session)
        response = service.get_admin_sources(
            user=mock_user,
            limit=10,
            offset=0,
        )

        # Verify public takes precedence
        assert response.total_count == 1
        assert len(response.results) == 1
        assert response.results[0].visibility == "public"


@pytest.mark.integration
class TestAdminSourcesVisibilityFilter:
    """Test visibility filtering for admin sources."""

    def test_filter_by_private_visibility(
        self, integration_db_session: Session
    ) -> None:
        """
        Test filtering sources by 'private' visibility.

        1. Create 3 sources: private, internal, public
        2. Query with visibility=['private']
        3. Verify only private source returned
        """
        org_id = "test-org-id"
        user = Auth0UserFactory.create(integration_db_session, organization_id=org_id)
        mock_user = create_mock_user(org_id, user.id)

        # Create private source
        private_source = PrimaryAssetFactory.create(
            integration_db_session,
            display_name="Private Source",
            organization_id=org_id,
        )
        PrimaryAssetRoleGrantFactory.create(
            integration_db_session,
            primary_asset_id=private_source.id,
            principal_kind=PrincipalKind.user,
            role=PrimaryAssetRole.asset_admin,
            organization_id=org_id,
            user_id=user.id,
        )

        # Create internal source
        internal_source = PrimaryAssetFactory.create(
            integration_db_session,
            display_name="Internal Source",
            organization_id=org_id,
        )
        PrimaryAssetRoleGrantFactory.create(
            integration_db_session,
            primary_asset_id=internal_source.id,
            principal_kind=PrincipalKind.user,
            role=PrimaryAssetRole.asset_admin,
            organization_id=org_id,
            user_id=user.id,
        )
        PrimaryAssetRoleGrantFactory.create(
            integration_db_session,
            primary_asset_id=internal_source.id,
            principal_kind=PrincipalKind.org,
            role=PrimaryAssetRole.asset_member,
            organization_id=org_id,
        )

        # Create public source
        public_source = PrimaryAssetFactory.create(
            integration_db_session,
            display_name="Public Source",
            organization_id=org_id,
        )
        PrimaryAssetRoleGrantFactory.create(
            integration_db_session,
            primary_asset_id=public_source.id,
            principal_kind=PrincipalKind.user,
            role=PrimaryAssetRole.asset_admin,
            organization_id=org_id,
            user_id=user.id,
        )
        PrimaryAssetRoleGrantFactory.create(
            integration_db_session,
            primary_asset_id=public_source.id,
            principal_kind=PrincipalKind.public,
            role=PrimaryAssetRole.asset_member,
            organization_id=org_id,
        )

        # Query with visibility filter
        service = AdminSourcesService(integration_db_session)
        response = service.get_admin_sources(
            user=mock_user,
            visibility=["private"],
            limit=10,
            offset=0,
        )

        # Verify only private source returned
        assert response.total_count == 1
        assert len(response.results) == 1
        assert response.results[0].visibility == "private"
        assert response.results[0].display_name == "Private Source"

    def test_filter_by_multiple_visibilities(
        self, integration_db_session: Session
    ) -> None:
        """
        Test filtering by multiple visibility values.

        1. Create 3 sources: private, internal, public
        2. Query with visibility=['private', 'public']
        3. Verify private and public returned, not internal
        """
        org_id = "test-org-id"
        user = Auth0UserFactory.create(integration_db_session, organization_id=org_id)
        mock_user = create_mock_user(org_id, user.id)

        # Create private source
        private_source = PrimaryAssetFactory.create(
            integration_db_session,
            display_name="Private Source",
            organization_id=org_id,
        )
        PrimaryAssetRoleGrantFactory.create(
            integration_db_session,
            primary_asset_id=private_source.id,
            principal_kind=PrincipalKind.user,
            role=PrimaryAssetRole.asset_admin,
            organization_id=org_id,
            user_id=user.id,
        )

        # Create internal source
        internal_source = PrimaryAssetFactory.create(
            integration_db_session,
            display_name="Internal Source",
            organization_id=org_id,
        )
        PrimaryAssetRoleGrantFactory.create(
            integration_db_session,
            primary_asset_id=internal_source.id,
            principal_kind=PrincipalKind.user,
            role=PrimaryAssetRole.asset_admin,
            organization_id=org_id,
            user_id=user.id,
        )
        PrimaryAssetRoleGrantFactory.create(
            integration_db_session,
            primary_asset_id=internal_source.id,
            principal_kind=PrincipalKind.org,
            role=PrimaryAssetRole.asset_member,
            organization_id=org_id,
        )

        # Create public source
        public_source = PrimaryAssetFactory.create(
            integration_db_session,
            display_name="Public Source",
            organization_id=org_id,
        )
        PrimaryAssetRoleGrantFactory.create(
            integration_db_session,
            primary_asset_id=public_source.id,
            principal_kind=PrincipalKind.user,
            role=PrimaryAssetRole.asset_admin,
            organization_id=org_id,
            user_id=user.id,
        )
        PrimaryAssetRoleGrantFactory.create(
            integration_db_session,
            primary_asset_id=public_source.id,
            principal_kind=PrincipalKind.public,
            role=PrimaryAssetRole.asset_member,
            organization_id=org_id,
        )

        # Query with multiple visibility filters
        service = AdminSourcesService(integration_db_session)
        response = service.get_admin_sources(
            user=mock_user,
            visibility=["private", "public"],
            limit=10,
            offset=0,
        )

        # Verify private and public returned
        assert response.total_count == 2
        assert len(response.results) == 2
        visibilities = {r.visibility for r in response.results}
        names = {r.display_name for r in response.results}
        assert visibilities == {"private", "public"}
        assert names == {"Private Source", "Public Source"}

    def test_visibility_filter_with_search(
        self, integration_db_session: Session
    ) -> None:
        """
        Test combining visibility filter with search.

        Steps:
        1. Create private and internal sources with similar names
        2. Query with visibility=['internal'] and search='Test'
        3. Verify only matching internal source returned
        """
        org_id = "test-org-id"
        user = Auth0UserFactory.create(integration_db_session, organization_id=org_id)
        mock_user = create_mock_user(org_id, user.id)

        # Create private source with "Test" in name
        private_source = PrimaryAssetFactory.create(
            integration_db_session,
            display_name="Test Private Source",
            organization_id=org_id,
        )
        PrimaryAssetRoleGrantFactory.create(
            integration_db_session,
            primary_asset_id=private_source.id,
            principal_kind=PrincipalKind.user,
            role=PrimaryAssetRole.asset_admin,
            organization_id=org_id,
            user_id=user.id,
        )

        # Create internal source with "Test" in name
        internal_source = PrimaryAssetFactory.create(
            integration_db_session,
            display_name="Test Internal Source",
            organization_id=org_id,
        )
        PrimaryAssetRoleGrantFactory.create(
            integration_db_session,
            primary_asset_id=internal_source.id,
            principal_kind=PrincipalKind.user,
            role=PrimaryAssetRole.asset_admin,
            organization_id=org_id,
            user_id=user.id,
        )
        PrimaryAssetRoleGrantFactory.create(
            integration_db_session,
            primary_asset_id=internal_source.id,
            principal_kind=PrincipalKind.org,
            role=PrimaryAssetRole.asset_member,
            organization_id=org_id,
        )

        # Create internal source without "Test" in name
        other_internal = PrimaryAssetFactory.create(
            integration_db_session,
            display_name="Other Internal Source",
            organization_id=org_id,
        )
        PrimaryAssetRoleGrantFactory.create(
            integration_db_session,
            primary_asset_id=other_internal.id,
            principal_kind=PrincipalKind.user,
            role=PrimaryAssetRole.asset_admin,
            organization_id=org_id,
            user_id=user.id,
        )
        PrimaryAssetRoleGrantFactory.create(
            integration_db_session,
            primary_asset_id=other_internal.id,
            principal_kind=PrincipalKind.org,
            role=PrimaryAssetRole.asset_member,
            organization_id=org_id,
        )

        # Query with visibility and search filters
        service = AdminSourcesService(integration_db_session)
        response = service.get_admin_sources(
            user=mock_user,
            visibility=["internal"],
            search="Test",
            limit=10,
            offset=0,
        )

        # Verify only "Test Internal Source" returned
        assert response.total_count == 1
        assert len(response.results) == 1
        assert response.results[0].visibility == "internal"
        assert response.results[0].display_name == "Test Internal Source"
