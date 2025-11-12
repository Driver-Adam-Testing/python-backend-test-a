# Authorization Testing & Hardening Plan

**Goal:** Make forgetting authorization nearly impossible and comprehensively test authorization correctness.

---

## Part 1: Prevention - Make Missing Authorization Hard

### Strategy 1: Static Analysis (HIGH PRIORITY) ⭐

**Create a custom pytest plugin or pre-commit hook that scans all endpoints.**

#### Implementation: `backend/tests/security/test_authorization_coverage.py`

```python
"""
Test that verifies EVERY endpoint has authorization.
Fails the build if any endpoint is missing authorization checks.
"""
import inspect
from typing import get_type_hints
from fastapi import APIRouter
from app.api import studio_router, unprotected_router
from app.api.auth import UserToken, ApiKeyToken

# Endpoints that are intentionally unprotected
ALLOWED_UNPROTECTED = {
    "/healthcheck",
    "/git-provider/github/webhook",
    "/git-provider/github/callback",
    "/git-provider/app/webhook",
    "/onboarding",
    "/subscription",
    "/signup",
    "/sandbox",  # dev only
}

def extract_all_routes(router: APIRouter, prefix: str = "") -> list[dict]:
    """Recursively extract all routes from a router."""
    routes = []
    for route in router.routes:
        if hasattr(route, 'path'):
            full_path = prefix + route.path
            routes.append({
                'path': full_path,
                'methods': route.methods,
                'endpoint': route.endpoint,
                'name': route.name,
            })
        if hasattr(route, 'routes'):  # Nested router
            routes.extend(extract_all_routes(route, prefix + route.path))
    return routes

def has_user_token_dependency(endpoint_func) -> bool:
    """Check if endpoint has UserToken or ApiKeyToken in signature."""
    sig = inspect.signature(endpoint_func)
    type_hints = get_type_hints(endpoint_func)

    for param_name, param in sig.parameters.items():
        # Check if the parameter is UserToken or ApiKeyToken
        param_type = type_hints.get(param_name)
        if param_type in (UserToken, ApiKeyToken):
            return True

        # Also check the annotation directly
        if hasattr(param.annotation, '__origin__'):
            return True

    return False

def calls_authorization_function(endpoint_func) -> bool:
    """Check if endpoint source code calls enforce_* functions."""
    import inspect
    try:
        source = inspect.getsource(endpoint_func)
        auth_patterns = [
            'enforce_asset_action',
            'enforce_org_action',
            'enforce_team_action',
            'enforce_org_membership',
            'enforce_super_admin',
            'enforce_any_source_admin',
            'enforce_any_team_admin',
            'check_asset_action',  # GraphQL
            'check_org_action',    # GraphQL
        ]
        return any(pattern in source for pattern in auth_patterns)
    except (OSError, TypeError):
        return False

def is_path_allowed_unprotected(path: str) -> bool:
    """Check if path is in the allowed unprotected list."""
    return any(path.startswith(allowed) for allowed in ALLOWED_UNPROTECTED)

def test_all_protected_endpoints_have_authorization():
    """
    CRITICAL SECURITY TEST

    Verifies that every protected endpoint either:
    1. Has UserToken/ApiKeyToken dependency (authentication), AND
    2. Calls an enforce_* or check_* function (authorization)

    OR is explicitly in the ALLOWED_UNPROTECTED list.
    """
    from app.api.studio_router import studio_router

    routes = extract_all_routes(studio_router, prefix="/studio/v1")

    violations = []

    for route in routes:
        path = route['path']
        endpoint = route['endpoint']

        # Skip if explicitly allowed to be unprotected
        if is_path_allowed_unprotected(path):
            continue

        # Check 1: Must have UserToken
        has_auth = has_user_token_dependency(endpoint)

        # Check 2: Must call authorization function
        has_authz = calls_authorization_function(endpoint)

        if not has_auth:
            violations.append({
                'path': path,
                'methods': route['methods'],
                'issue': 'Missing authentication (no UserToken/ApiKeyToken)',
            })
        elif not has_authz:
            violations.append({
                'path': path,
                'methods': route['methods'],
                'issue': 'Missing authorization check (no enforce_*/check_* call)',
            })

    if violations:
        error_msg = "\n\n🚨 SECURITY VIOLATION: Endpoints missing authorization:\n\n"
        for v in violations:
            error_msg += f"  {v['methods']} {v['path']}\n"
            error_msg += f"    Issue: {v['issue']}\n\n"
        error_msg += "Add authorization checks or add to ALLOWED_UNPROTECTED list.\n"

        assert False, error_msg

def test_unprotected_router_is_safe():
    """Verify unprotected router only contains expected safe endpoints."""
    from app.api.unprotected_router import unprotected_router

    routes = extract_all_routes(unprotected_router, prefix="/studio/v1")

    for route in routes:
        path = route['path']
        assert is_path_allowed_unprotected(path), \
            f"Unexpected unprotected endpoint: {path}. Review security implications."
```

**Why this works:**
- ✅ Runs on every CI build
- ✅ Catches new endpoints automatically
- ✅ Forces explicit opt-in for unprotected endpoints
- ✅ Can't be bypassed accidentally
- ⚠️ Can be bypassed intentionally (add to ALLOWED_UNPROTECTED)

**Limitations:**
- Source code inspection is fragile (refactoring could break detection)
- Doesn't verify authorization is *correct*, only *present*

---

### Strategy 2: FastAPI Authorization Dependencies (MEDIUM PRIORITY)

**Use FastAPI's dependency injection to enforce authorization declaratively.**

#### Implementation: Composable Authorization Dependencies

```python
# backend/app/api/authorization_dependencies.py
"""
FastAPI dependencies for declarative authorization.

These dependencies work with FastAPI's Depends() system to enforce
authorization at the route level, making it hard to forget.
"""
from typing import Annotated
from uuid import UUID
from fastapi import Depends, Path
from app.api.auth import UserToken
from app.api.session import CurrentSession
from app.authorization.fastapi import enforce_asset_action, enforce_org_action, enforce_team_action


def make_asset_authorizer(action_key: str):
    """
    Factory that creates a dependency to authorize asset actions.

    Usage:
        CanManageAsset = Annotated[UUID, Depends(make_asset_authorizer("asset.manage"))]

        @router.put("/assets/{asset_id}")
        def update_asset(asset_id: CanManageAsset, ...):
            # asset_id is guaranteed authorized for "asset.manage"
    """
    def authorize_asset(
        asset_id: UUID = Path(...),
        session: CurrentSession = Depends(),
        user: UserToken = Depends()
    ) -> UUID:
        enforce_asset_action(session, user, asset_id, action_key)
        return asset_id

    return authorize_asset


def make_org_authorizer(action_key: str):
    """
    Factory that creates a dependency to authorize org actions.

    Usage:
        RequireUsersManage = Depends(make_org_authorizer("users.manage"))

        @router.get("/organization/users", dependencies=[RequireUsersManage])
        def list_users(...):
            # Endpoint is protected by users.manage permission
    """
    def authorize_org(
        session: CurrentSession = Depends(),
        user: UserToken = Depends()
    ) -> None:
        enforce_org_action(session, user, action_key)

    return authorize_org


def make_team_authorizer(action_key: str):
    """
    Factory that creates a dependency to authorize team actions.

    Usage:
        CanManageTeam = Annotated[UUID, Depends(make_team_authorizer("team.manage"))]

        @router.put("/teams/{team_id}")
        def update_team(team_id: CanManageTeam, ...):
            # team_id is guaranteed authorized for "team.manage"
    """
    def authorize_team(
        team_id: UUID = Path(...),
        session: CurrentSession = Depends(),
        user: UserToken = Depends()
    ) -> UUID:
        enforce_team_action(session, user, team_id, action_key)
        return team_id

    return authorize_team


# Pre-defined common authorization dependencies
CanManageAsset = Annotated[UUID, Depends(make_asset_authorizer("asset.manage"))]
CanDeleteAsset = Annotated[UUID, Depends(make_asset_authorizer("asset.delete"))]
CanUseAsSource = Annotated[UUID, Depends(make_asset_authorizer("asset.use_as_source"))]

RequireUsersManage = Depends(make_org_authorizer("users.manage"))
RequireUsersView = Depends(make_org_authorizer("users.view"))
RequireTeamAdmin = Depends(make_org_authorizer("team.admin"))
RequireTeamView = Depends(make_org_authorizer("team.view"))

CanManageTeam = Annotated[UUID, Depends(make_team_authorizer("team.manage"))]
CanViewTeam = Annotated[UUID, Depends(make_team_authorizer("team.view"))]
```

**Usage in endpoints (declarative authorization):**

```python
from app.api.authorization_dependencies import CanManageAsset, RequireUsersView

# Asset endpoint - authorization in path parameter type
@router.put("/primary_assets/{primary_asset_id}")
def update_primary_asset(
    primary_asset_id: CanManageAsset,  # ⭐ Authorization happens here
    session: CurrentSession,
    user: UserToken,
    payload: PrimaryAssetUpdate,
) -> PrimaryAsset:
    # If we reach here, authorization already passed
    # primary_asset_id is guaranteed to be authorized for "asset.manage"

    asset = session.exec(
        select(PrimaryAsset)
        .where(PrimaryAsset.id == primary_asset_id)
        .where(PrimaryAsset.organization_id == user.organization_id)
    ).one_or_none()

    asset.display_name = payload.display_name
    session.commit()
    return asset

# Org endpoint - authorization in dependencies list
@router.get("/organization/users", dependencies=[RequireUsersView])  # ⭐ Authorization here
def list_users(
    session: CurrentSession,
    user: UserToken,
) -> ListMembersResponse:
    # If we reach here, user has "users.view" permission
    organizations_service = OrganizationsService(session)
    return organizations_service.list_members(user)
```

**Why this works:**
- ✅ Works with FastAPI's dependency injection model
- ✅ Authorization declared at route level (visible in OpenAPI docs)
- ✅ Reusable dependencies reduce boilerplate
- ✅ Type annotations make authorization clear
- ✅ FastAPI validates dependencies before calling endpoint
- ✅ Can't accidentally skip authorization (it's in the signature)
- ❌ Requires refactoring existing endpoints
- ❌ Slightly more complex for batch operations

**Advanced: Multiple assets authorization:**

```python
# For endpoints that accept multiple asset IDs
from pydantic import BaseModel

class AddUserSourcesRequest(BaseModel):
    sources: list[dict]  # [{"source_id": "...", "role": "..."}]

@router.post("/admin/users/{user_id}/sources")
def add_user_sources(
    session: CurrentSession,
    user: UserToken,
    request: AddUserSourcesRequest,
) -> None:
    # Create dependency that checks ALL sources
    for source in request.sources:
        # This still needs explicit checking
        enforce_asset_action(session, user, UUID(source["source_id"]), "asset.manage")

    # ... rest of implementation
```

**Benefits over current approach:**
1. **Declarative** - Authorization requirements visible in function signature
2. **DRY** - Reuse `CanManageAsset` across many endpoints
3. **Self-documenting** - Type hints show what's required
4. **FastAPI native** - Uses Depends() like other FastAPI features
5. **OpenAPI integration** - Shows up in auto-generated docs

**Migration path:**
1. Create authorization dependencies alongside existing `enforce_*` calls
2. Gradually migrate endpoints to use dependencies
3. Eventually deprecate direct `enforce_*` calls in business logic

---

### Strategy 3: Middleware Logging (LOW PRIORITY)

**Log which endpoints are called without authorization checks.**

```python
# backend/app/middleware/authorization_audit_middleware.py
"""
Middleware that logs requests to help identify missing authorization.
"""
import logging
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("authorization_audit")

class AuthorizationAuditMiddleware(BaseHTTPMiddleware):
    """
    Logs requests and whether authorization was performed.

    This is NOT a security control, just visibility.
    """

    async def dispatch(self, request: Request, call_next):
        # Track if authorization was called
        request.state.authorization_checked = False

        response = await call_next(request)

        # Check if this was a protected endpoint
        if not request.url.path.startswith(("/healthcheck", "/docs")):
            if not request.state.authorization_checked:
                logger.warning(
                    f"Request to {request.method} {request.url.path} "
                    f"did not perform authorization check"
                )

        return response

# Modify enforce_* functions to set the flag
def enforce_asset_action_with_tracking(db, user, asset_id, action_key, request: Request = None):
    if request:
        request.state.authorization_checked = True
    return enforce_asset_action(db, user, asset_id, action_key)
```

**Why this works:**
- ✅ Runtime visibility
- ✅ Helps during development
- ❌ Doesn't prevent issues
- ❌ Can be noisy
- ❌ Easy to ignore

---

## Part 2: Testing Authorization Logic Correctness

### Strategy 4: Role-Action Matrix Tests (HIGH PRIORITY) ⭐

**Systematically test every role × action combination.**

```python
# backend/tests/security/test_authorization_matrix.py
"""
Comprehensive tests for authorization logic correctness.

Tests the authorization decision matrix:
- Super admins can do everything
- Org admins can manage org
- Asset admins can manage their assets
- Asset members have limited access
- Non-members have no access
"""
import pytest
from uuid import uuid4
from database.models_enums import OrgRole, PrimaryAssetRole, TeamRole
from app.authorization.core import AuthContext, authorize_asset_action, authorize_org_action

# Test fixtures for different user types
@pytest.fixture
def super_admin_user(db):
    """User who is org super admin."""
    org_id = "test-org"
    user_id = uuid4()

    # Create org membership with super admin role
    from database.models import OrgMembership
    membership = OrgMembership(
        org_id=org_id,
        user_id=user_id,
        role=OrgRole.org_super_admin
    )
    db.add(membership)
    db.commit()

    return AuthContext(db=db, user_id=user_id, organization_id=org_id)

@pytest.fixture
def org_admin_user(db):
    """User who is org admin but not super admin."""
    org_id = "test-org"
    user_id = uuid4()

    from database.models import OrgMembership
    membership = OrgMembership(
        org_id=org_id,
        user_id=user_id,
        role=OrgRole.org_admin
    )
    db.add(membership)
    db.commit()

    return AuthContext(db=db, user_id=user_id, organization_id=org_id)

@pytest.fixture
def org_member_user(db):
    """Regular org member."""
    org_id = "test-org"
    user_id = uuid4()

    from database.models import OrgMembership
    membership = OrgMembership(
        org_id=org_id,
        user_id=user_id,
        role=OrgRole.org_member
    )
    db.add(membership)
    db.commit()

    return AuthContext(db=db, user_id=user_id, organization_id=org_id)

@pytest.fixture
def asset_admin_user(db, test_asset):
    """User who is admin of a specific asset."""
    org_id = "test-org"
    user_id = uuid4()

    from database.models import OrgMembership, PrimaryAssetRoleGrant
    membership = OrgMembership(
        org_id=org_id,
        user_id=user_id,
        role=OrgRole.org_member
    )
    db.add(membership)

    grant = PrimaryAssetRoleGrant(
        organization_id=org_id,
        primary_asset_id=test_asset.id,
        user_id=user_id,
        role=PrimaryAssetRole.asset_admin,
        principal_kind="user"
    )
    db.add(grant)
    db.commit()

    return AuthContext(db=db, user_id=user_id, organization_id=org_id)

@pytest.fixture
def asset_member_user(db, test_asset):
    """User who is member of a specific asset."""
    org_id = "test-org"
    user_id = uuid4()

    from database.models import OrgMembership, PrimaryAssetRoleGrant
    membership = OrgMembership(
        org_id=org_id,
        user_id=user_id,
        role=OrgRole.org_member
    )
    db.add(membership)

    grant = PrimaryAssetRoleGrant(
        organization_id=org_id,
        primary_asset_id=test_asset.id,
        user_id=user_id,
        role=PrimaryAssetRole.asset_member,
        principal_kind="user"
    )
    db.add(grant)
    db.commit()

    return AuthContext(db=db, user_id=user_id, organization_id=org_id)

@pytest.fixture
def non_member_user(db):
    """User who is NOT a member of the org."""
    user_id = uuid4()
    return AuthContext(db=db, user_id=user_id, organization_id="different-org")

@pytest.fixture
def test_asset(db):
    """A test primary asset."""
    from database.models import PrimaryAsset
    from database.models_enums import PrimaryAssetKind, PrimaryAssetProvider

    asset = PrimaryAsset(
        organization_id="test-org",
        display_name="Test Asset",
        kind=PrimaryAssetKind.CODEBASE,
        provider=PrimaryAssetProvider.GITHUB
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset

# ============================================================================
# ASSET ACTION TESTS
# ============================================================================

class TestAssetManageAction:
    """Test who can perform 'asset.manage' action."""

    def test_super_admin_can_manage_any_asset(self, super_admin_user, test_asset):
        decision = authorize_asset_action(super_admin_user, test_asset.id, "asset.manage")
        assert decision.allowed
        assert "org_super_admin" in decision.reasons

    def test_asset_admin_can_manage_their_asset(self, asset_admin_user, test_asset):
        decision = authorize_asset_action(asset_admin_user, test_asset.id, "asset.manage")
        assert decision.allowed
        assert decision.role == PrimaryAssetRole.asset_admin.value

    def test_asset_member_cannot_manage_asset(self, asset_member_user, test_asset):
        decision = authorize_asset_action(asset_member_user, test_asset.id, "asset.manage")
        assert not decision.allowed
        assert "role_denied" in decision.reasons

    def test_org_member_without_grant_cannot_manage(self, org_member_user, test_asset):
        decision = authorize_asset_action(org_member_user, test_asset.id, "asset.manage")
        assert not decision.allowed

    def test_non_member_cannot_manage_asset(self, non_member_user, test_asset):
        decision = authorize_asset_action(non_member_user, test_asset.id, "asset.manage")
        assert not decision.allowed

class TestAssetUseAsSourceAction:
    """Test who can use asset as source (read-only operation)."""

    def test_super_admin_can_use_as_source(self, super_admin_user, test_asset):
        decision = authorize_asset_action(super_admin_user, test_asset.id, "asset.use_as_source")
        assert decision.allowed

    def test_asset_admin_can_use_as_source(self, asset_admin_user, test_asset):
        decision = authorize_asset_action(asset_admin_user, test_asset.id, "asset.use_as_source")
        assert decision.allowed

    def test_asset_member_can_use_as_source(self, asset_member_user, test_asset):
        decision = authorize_asset_action(asset_member_user, test_asset.id, "asset.use_as_source")
        assert decision.allowed  # Members CAN use as source

    def test_non_member_cannot_use_as_source(self, non_member_user, test_asset):
        decision = authorize_asset_action(non_member_user, test_asset.id, "asset.use_as_source")
        assert not decision.allowed

# ============================================================================
# ORG ACTION TESTS
# ============================================================================

class TestUsersManageAction:
    """Test who can manage org users."""

    def test_super_admin_can_manage_users(self, super_admin_user):
        decision = authorize_org_action(super_admin_user, "users.manage")
        assert decision.allowed

    def test_org_admin_can_manage_users(self, org_admin_user):
        decision = authorize_org_action(org_admin_user, "users.manage")
        assert decision.allowed

    def test_org_member_cannot_manage_users(self, org_member_user):
        decision = authorize_org_action(org_member_user, "users.manage")
        assert not decision.allowed

    def test_non_member_cannot_manage_users(self, non_member_user):
        decision = authorize_org_action(non_member_user, "users.manage")
        assert not decision.allowed

class TestTeamViewAction:
    """Test who can view teams."""

    def test_super_admin_can_view_teams(self, super_admin_user):
        decision = authorize_org_action(super_admin_user, "team.view")
        assert decision.allowed

    def test_org_member_can_view_teams(self, org_member_user):
        decision = authorize_org_action(org_member_user, "team.view")
        assert decision.allowed  # All members can view teams

    def test_non_member_cannot_view_teams(self, non_member_user):
        decision = authorize_org_action(non_member_user, "team.view")
        assert not decision.allowed

# ============================================================================
# CROSS-ORG ACCESS TESTS (Critical Security Boundary)
# ============================================================================

class TestCrossOrgAccess:
    """Test that org boundaries are strictly enforced."""

    def test_cannot_access_asset_from_different_org(self, db):
        """User in org-a cannot access assets in org-b."""
        from database.models import PrimaryAsset, OrgMembership
        from database.models_enums import PrimaryAssetKind, PrimaryAssetProvider

        # Create asset in org-b
        asset_org_b = PrimaryAsset(
            organization_id="org-b",
            display_name="Org B Asset",
            kind=PrimaryAssetKind.CODEBASE,
            provider=PrimaryAssetProvider.GITHUB
        )
        db.add(asset_org_b)

        # Create user in org-a
        user_id = uuid4()
        membership = OrgMembership(
            org_id="org-a",
            user_id=user_id,
            role=OrgRole.org_super_admin  # Even super admin of different org!
        )
        db.add(membership)
        db.commit()

        ctx = AuthContext(db=db, user_id=user_id, organization_id="org-a")
        decision = authorize_asset_action(ctx, asset_org_b.id, "asset.use_as_source")

        assert not decision.allowed
        assert "asset_not_found_or_wrong_org" in decision.reasons

    def test_asset_must_belong_to_users_org(self, db, super_admin_user, test_asset):
        """Even if asset exists, it must be in user's org."""
        # Change context to different org
        wrong_org_ctx = AuthContext(
            db=db,
            user_id=super_admin_user.user_id,
            organization_id="wrong-org"
        )

        decision = authorize_asset_action(wrong_org_ctx, test_asset.id, "asset.manage")
        assert not decision.allowed
```

**Why this works:**
- ✅ Tests actual authorization logic
- ✅ Comprehensive coverage of role combinations
- ✅ Tests the most critical security boundary (cross-org)
- ✅ Catches logic bugs in authorization code
- ✅ Self-documenting (shows intended behavior)

---

### Strategy 5: Integration Tests for Endpoints (HIGH PRIORITY) ⭐

**Test actual HTTP endpoints with different user contexts.**

```python
# backend/tests/security/test_endpoint_authorization.py
"""
Integration tests that verify endpoints enforce authorization correctly.

These tests make actual HTTP requests and verify:
1. Unauthorized users get 403
2. Users from wrong org get 403/404
3. Users with insufficient permissions get 403
4. Authorized users succeed
"""
import pytest
from fastapi.testclient import TestClient
from uuid import uuid4

@pytest.fixture
def client(db):
    """Test client with database."""
    from app.main import app
    return TestClient(app)

@pytest.fixture
def org_a_admin_token(db):
    """JWT token for org-a admin."""
    # Create user and org membership
    # Return JWT token
    pass

@pytest.fixture
def org_b_admin_token(db):
    """JWT token for org-b admin."""
    pass

@pytest.fixture
def org_a_member_token(db):
    """JWT token for org-a regular member."""
    pass

@pytest.fixture
def asset_in_org_a(db):
    """Test asset in org-a."""
    pass

class TestPrimaryAssetEndpoints:
    """Test authorization on primary asset endpoints."""

    def test_list_primary_assets_returns_only_own_org_assets(
        self, client, org_a_admin_token, asset_in_org_a, asset_in_org_b
    ):
        """List endpoint must filter by org."""
        response = client.get(
            "/studio/v1/node/primary_assets",
            headers={"Authorization": f"Bearer {org_a_admin_token}"}
        )
        assert response.status_code == 200

        assets = response.json()["results"]
        org_ids = {asset["organization_id"] for asset in assets}

        # Should ONLY see org-a assets
        assert org_ids == {"org-a"}
        assert asset_in_org_a.id in {asset["id"] for asset in assets}
        assert asset_in_org_b.id not in {asset["id"] for asset in assets}

    def test_update_asset_requires_admin_role(
        self, client, org_a_member_token, asset_in_org_a
    ):
        """Member cannot update asset without admin grant."""
        response = client.put(
            f"/studio/v1/node/primary_assets/{asset_in_org_a.id}",
            headers={"Authorization": f"Bearer {org_a_member_token}"},
            json={"display_name": "Hacked Name"}
        )
        assert response.status_code == 403
        assert "insufficient_permissions" in response.json()["detail"]["error"]

    def test_cannot_update_asset_from_different_org(
        self, client, org_b_admin_token, asset_in_org_a
    ):
        """Admin of org-b cannot modify asset in org-a."""
        response = client.put(
            f"/studio/v1/node/primary_assets/{asset_in_org_a.id}",
            headers={"Authorization": f"Bearer {org_b_admin_token}"},
            json={"display_name": "Hacked Name"}
        )
        assert response.status_code in (403, 404)  # Not found or forbidden

    def test_delete_asset_requires_admin_role(
        self, client, org_a_admin_token, asset_in_org_a
    ):
        """Only asset admin can delete."""
        # First verify admin CAN delete
        response = client.delete(
            f"/studio/v1/node/primary_assets/{asset_in_org_a.id}",
            headers={"Authorization": f"Bearer {org_a_admin_token}"}
        )
        assert response.status_code == 200

class TestOrganizationEndpoints:
    """Test authorization on org management endpoints."""

    def test_list_org_members_requires_permission(
        self, client, org_a_member_token
    ):
        """Regular member cannot view org members list."""
        response = client.get(
            "/studio/v1/organization/users",
            headers={"Authorization": f"Bearer {org_a_member_token}"}
        )
        assert response.status_code == 403

    def test_admin_can_list_org_members(
        self, client, org_a_admin_token
    ):
        """Admin can view org members."""
        response = client.get(
            "/studio/v1/organization/users",
            headers={"Authorization": f"Bearer {org_a_admin_token}"}
        )
        assert response.status_code == 200

    def test_cannot_delete_member_from_different_org(
        self, client, org_b_admin_token, user_in_org_a
    ):
        """Org-b admin cannot delete user from org-a."""
        response = client.delete(
            f"/studio/v1/organization/users/{user_in_org_a.id}",
            headers={"Authorization": f"Bearer {org_b_admin_token}"}
        )
        assert response.status_code in (403, 404)

class TestChatEndpoint:
    """Test authorization on chat endpoint (uses multiple sources)."""

    def test_chat_checks_all_source_permissions(
        self, client, org_a_member_token, source_with_access, source_without_access
    ):
        """Chat must verify access to ALL sources provided."""
        response = client.post(
            "/studio/v1/chat",
            headers={"Authorization": f"Bearer {org_a_member_token}"},
            json={
                "user_prompt": "test",
                "source_node_ids": [
                    str(source_with_access.id),
                    str(source_without_access.id)  # Don't have access to this one
                ]
            }
        )
        assert response.status_code == 403

# ============================================================================
# NEGATIVE TESTS - Attempt to bypass authorization
# ============================================================================

class TestAuthorizationBypassAttempts:
    """Test common authorization bypass techniques."""

    def test_cannot_bypass_by_omitting_token(self, client, asset_in_org_a):
        """Request without token fails."""
        response = client.get(f"/studio/v1/node/primary_assets/{asset_in_org_a.id}")
        assert response.status_code == 401

    def test_cannot_bypass_by_using_invalid_token(self, client, asset_in_org_a):
        """Invalid token fails."""
        response = client.get(
            f"/studio/v1/node/primary_assets/{asset_in_org_a.id}",
            headers={"Authorization": "Bearer invalid-token"}
        )
        assert response.status_code == 401

    def test_cannot_access_by_guessing_ids(
        self, client, org_a_member_token
    ):
        """Cannot access resources by guessing UUIDs."""
        fake_id = uuid4()
        response = client.get(
            f"/studio/v1/node/primary_assets/{fake_id}",
            headers={"Authorization": f"Bearer {org_a_member_token}"}
        )
        assert response.status_code in (403, 404)

    def test_list_endpoints_dont_leak_cross_org_count(
        self, client, org_a_admin_token
    ):
        """Total count in list responses should only count accessible resources."""
        response = client.get(
            "/studio/v1/node/primary_assets",
            headers={"Authorization": f"Bearer {org_a_admin_token}"}
        )
        assert response.status_code == 200

        data = response.json()
        # Verify count matches results length (no phantom inaccessible resources)
        assert len(data["results"]) <= data["total_count"]
```

**Why this works:**
- ✅ Tests real HTTP requests
- ✅ Tests actual authentication + authorization flow
- ✅ Tests cross-org boundaries at HTTP level
- ✅ Tests common bypass attempts
- ✅ Catches issues with query filters
- ✅ Verifies 403/404 error responses

---

### Strategy 6: Property-Based Testing (MEDIUM PRIORITY)

**Use hypothesis to generate test cases for invariants.**

```python
# backend/tests/security/test_authorization_properties.py
"""
Property-based tests for authorization invariants.

These test universal properties that should ALWAYS be true.
"""
import pytest
from hypothesis import given, strategies as st
from uuid import UUID

# ============================================================================
# INVARIANTS (Properties that should ALWAYS hold)
# ============================================================================

@given(
    user_org_id=st.text(min_size=1),
    asset_org_id=st.text(min_size=1),
    action=st.sampled_from(["asset.manage", "asset.delete", "asset.use_as_source"])
)
def test_property_users_cannot_access_assets_from_different_org(
    db, user_org_id, asset_org_id, action
):
    """
    INVARIANT: Users can NEVER access assets from a different org.

    This should hold for ANY user_org, asset_org, and action combination.
    """
    if user_org_id == asset_org_id:
        return  # Same org, skip

    from database.models import PrimaryAsset, OrgMembership
    from database.models_enums import OrgRole, PrimaryAssetKind, PrimaryAssetProvider
    from app.authorization.core import AuthContext, authorize_asset_action

    # Create asset in asset_org_id
    asset = PrimaryAsset(
        organization_id=asset_org_id,
        display_name="Test",
        kind=PrimaryAssetKind.CODEBASE,
        provider=PrimaryAssetProvider.GITHUB
    )
    db.add(asset)

    # Create super admin in user_org_id
    from uuid import uuid4
    user_id = uuid4()
    membership = OrgMembership(
        org_id=user_org_id,
        user_id=user_id,
        role=OrgRole.org_super_admin  # Even super admin!
    )
    db.add(membership)
    db.commit()

    # Attempt authorization
    ctx = AuthContext(db=db, user_id=user_id, organization_id=user_org_id)
    decision = authorize_asset_action(ctx, asset.id, action)

    # Should ALWAYS fail
    assert not decision.allowed, \
        f"Cross-org access allowed: user_org={user_org_id}, asset_org={asset_org_id}"

@given(
    role=st.sampled_from(["asset_admin", "asset_member", "no_access"]),
    action=st.sampled_from(["asset.manage", "asset.delete"])
)
def test_property_only_admins_can_modify_assets(db, role, action):
    """
    INVARIANT: Only asset_admin can perform write operations.

    asset_member and users without access should NEVER succeed.
    """
    # Test that only asset_admin succeeds
    # Others should fail
    pass
```

**Why this works:**
- ✅ Tests many edge cases automatically
- ✅ Finds unexpected failures
- ✅ Documents invariants clearly
- ❌ Complex to set up
- ❌ Can be slow

---

## Part 3: Testing Authorization Presence

### Strategy 7: Automated Route Discovery Test (HIGH PRIORITY) ⭐

**Already covered in Strategy 1** - the `test_all_protected_endpoints_have_authorization` test.

---

### Strategy 8: Penetration Testing Checklist (LOW PRIORITY)

**Manual security testing guide for new features.**

```markdown
# Authorization Security Checklist

When adding a new endpoint, verify:

## Authentication
- [ ] Endpoint requires UserToken or ApiKeyToken dependency
- [ ] Invalid/missing token returns 401
- [ ] Expired token returns 401

## Authorization - Org Boundary
- [ ] Endpoint checks user.organization_id matches resource
- [ ] User from different org gets 403/404
- [ ] Query filters include org_id check

## Authorization - Resource Access
- [ ] Endpoint calls appropriate enforce_* function
- [ ] Correct action key used
- [ ] Asset ID validation (belongs to org)
- [ ] Batch operations check ALL resources

## Authorization - Role Permissions
- [ ] Correct minimum role required
- [ ] Lower roles get 403
- [ ] Super admin bypass works

## List Endpoints
- [ ] Uses query filter (primary_asset_grant_filter, etc)
- [ ] Total count only includes accessible resources
- [ ] Pagination doesn't leak IDs

## Error Handling
- [ ] 404 for non-existent resources (not 403)
- [ ] 403 for unauthorized but existing resources
- [ ] Error messages don't leak sensitive info

## Test Coverage
- [ ] Integration test with authorized user (200)
- [ ] Integration test with unauthorized user (403)
- [ ] Integration test with wrong org user (403/404)
- [ ] Unit test for authorization logic
```

---

## Implementation Priority

### Phase 1: Critical Prevention (Week 1)
1. ✅ **Implement Strategy 1** - Static analysis test
2. ✅ **Implement Strategy 4** - Role-action matrix tests
3. ✅ **Implement Strategy 5** - Endpoint integration tests

**Goal:** Catch missing authorization immediately in CI.

### Phase 2: Comprehensive Coverage (Week 2-3)
4. ✅ Add more integration test coverage for all endpoints
5. ✅ Implement property-based tests for critical invariants
6. ✅ Add test coverage reporting for authorization tests

### Phase 3: Long-term Hardening (Month 2)
7. ⏸️ Consider Strategy 2 - Type-safe authorization (major refactor)
8. ⏸️ Add Strategy 3 - Logging middleware (if needed)
9. ⏸️ Automated penetration testing

---

## Metrics & Monitoring

### Test Metrics to Track
- Number of endpoints with authorization tests
- Authorization test coverage %
- Number of violations caught by static analysis
- Time to detect authorization issues

### Runtime Metrics to Add
- Failed authorization attempts (by endpoint)
- Cross-org access attempts
- 403 error rate by user/endpoint

---

## Example CI/CD Integration

```yaml
# .github/workflows/security.yml
name: Security Tests

on: [push, pull_request]

jobs:
  authorization-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2

      - name: Install dependencies
        run: |
          pip install -e backend
          pip install pytest hypothesis

      - name: Run authorization coverage test
        run: |
          pytest backend/tests/security/test_authorization_coverage.py -v

      - name: Run authorization matrix tests
        run: |
          pytest backend/tests/security/test_authorization_matrix.py -v

      - name: Run endpoint authorization tests
        run: |
          pytest backend/tests/security/test_endpoint_authorization.py -v

      # Fail the build if any authorization test fails
      - name: Check results
        if: failure()
        run: |
          echo "❌ Authorization tests failed! Review security implications."
          exit 1
```

---

## Summary

**Making authorization hard to forget:**
1. ⭐ Static analysis that fails CI if authorization missing
2. Type-safe authorization context (requires refactor)
3. Logging middleware for visibility

**Testing authorization correctness:**
1. ⭐ Role-action matrix tests (unit tests for authz logic)
2. ⭐ Endpoint integration tests (test actual HTTP requests)
3. Property-based tests (test invariants)

**Testing authorization presence:**
1. ⭐ Automated route discovery test
2. Penetration testing checklist

**Critical path: Implement strategies 1, 4, and 5 first** - these give you:
- Prevention (can't add endpoint without authz)
- Logic testing (authz decisions are correct)
- Integration testing (endpoints enforce correctly)

This creates a defense-in-depth system where:
- Static analysis catches missing authorization at build time
- Unit tests verify authorization logic is correct
- Integration tests verify endpoints work end-to-end
- Property tests verify universal invariants hold
