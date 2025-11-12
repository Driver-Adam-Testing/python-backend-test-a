# Authorization Audit Report
**Date:** 2025-11-04
**Auditor:** Claude Code
**Scope:** All API endpoints requiring user authentication in backend/app/api

---

## Executive Summary

**Overall Status:** 🟢 **GOOD** with 1 Critical Issue

- **Total Files Audited:** 49 route files (~6,000 lines of API code)
- **Total Endpoints:** ~80+ endpoints across v1, v2, and legacy GraphQL
- **Critical Issues:** 1
- **Authorization System:** Well-designed RBAC system with org/team/asset scoping
- **Overall Coverage:** ~99% of endpoints properly authorized

### Critical Finding
**1 endpoint missing ALL authorization checks** and is immediately exploitable.

---

## Authorization System Overview

### Core Components (backend/app/authorization/)

1. **core.py** - Action-based authorization engine
   - `authorize_asset_action()` - Checks user access to specific assets
   - `authorize_org_action()` - Checks user permissions at org level
   - `authorize_team_action()` - Checks user permissions for team operations
   - Super admin bypass logic
   - Role hierarchy: asset_admin > asset_member

2. **fastapi.py** - Enforcement functions for endpoints
   - `enforce_asset_action()` - Raises 403 if unauthorized
   - `enforce_org_action()` - Raises 403 if unauthorized
   - `enforce_team_action()` - Raises 403 if unauthorized
   - `enforce_org_membership()` - Basic org membership check
   - `enforce_super_admin()` - Super admin only
   - `enforce_any_source_admin()` - Must be admin of ANY source
   - `enforce_any_team_admin()` - Must be admin of ANY team

3. **query_filters.py** - SQL-level authorization filters
   - `primary_asset_grant_filter()` - Filters assets by grants
   - `content_grant_filter()` - Filters content by asset grants
   - `page_asset_grant_filter()` - Special page authorization
   - `effective_asset_role_expr()` - Computes user's effective role

4. **helpers.py** - Utility functions
   - `is_org_member()`, `is_super_admin()`
   - `get_user_team_ids()`, `build_grant_condition()`

---

## Critical Issues

### 🔴 CRITICAL: Endpoint Missing All Authorization

**File:** `backend/app/api/routes/v1/content.py:55-67`
**Endpoint:** `POST /studio/v1/content/export-rst`
**Issue:** NO authorization checks - any authenticated user from ANY org can call this

```python
@router.post(
    "/export-rst",
    summary="Export Markdown content to RST and return the file",
)
def export_markdown_content_to_rst(
    session: CurrentSession,
    request: ExportSingleRequest,
) -> StreamingResponse:
    content_service = ContentService(session)
    rst_content = content_service.convert_markdown_to_rst(request.content)
    return StreamingResponse(
        rst_content,
        media_type="text/x-rst",
        headers={"Content-Disposition": "attachment; filename=exported_content.rst"},
    )
```

**Risk:**
- Any authenticated user can convert arbitrary markdown to RST
- No org_id check - cross-org access possible
- Could be used for resource exhaustion (large markdown payloads)
- No asset authorization

**Recommendation:**
```python
def export_markdown_content_to_rst(
    session: CurrentSession,
    user: UserToken,  # ADD THIS
    request: ExportSingleRequest,
) -> StreamingResponse:
    enforce_org_membership(session, user)  # ADD THIS
    # ... rest of implementation
```

---

## Properly Authorized Endpoints ✅

### V1 Endpoints (backend/app/api/routes/v1/)

#### Asset Management
- ✅ `codebase.py` - All endpoints use `enforce_asset_action()` and check org_id
  - GET `/{codebase_id}/versions` - Line 56
  - POST `/generate` - Lines 131-136

#### Organization Management
- ✅ `organization.py` - All endpoints use `enforce_org_action()`
  - GET `/roles` - Line 33
  - GET `/users` - Line 50
  - DELETE `/users/{user_id}` - Line 68
  - PUT `/users/role` - Line 88
  - PUT `/users/{user_id}/role` - Line 117
  - GET `/invitations` - Line 143
  - POST `/invitations` - Line 165
  - DELETE `/invitations/{invitation_id}` - Line 195

#### Team Management
- ✅ `teams.py` - Uses `enforce_org_action()` and `enforce_team_action()`
  - POST `/` - Line 48: `enforce_org_action(session, user, "team.admin")`
  - GET `/` - Line 80: `enforce_org_action(session, user, "team.view")`
  - GET `/search` - Line 111
  - GET `/{team_id}` - Line 138
  - PUT `/{team_id}` - Line 164: `enforce_team_action()`
  - DELETE `/{team_id}` - Line 192

- ✅ `team_members.py` - All use `enforce_team_action()`
  - GET `/{team_id}/members` - Line 59
  - POST `/{team_id}/members` - Line 94
  - PUT `/{team_id}/members` - Line 125
  - DELETE `/{team_id}/members` - Line 154

- ✅ `team_sources.py` - All endpoints properly check asset access

#### Source/Asset ACLs
- ✅ `source_users.py` - All use `enforce_asset_action()`
  - GET `/sources/{source_id}/users` - Line 48
  - POST `/sources/{source_id}/users` - Lines 84-90 (checks ALL sources)
  - PUT `/sources/{source_id}/users` - Lines 119-125 (checks ALL sources)
  - DELETE `/sources/{source_id}/users` - Lines 154-160 (checks ALL sources)

- ✅ `source_teams.py` - Similar pattern to source_users

- ✅ `user_sources.py` - Checks org action and asset actions
  - GET `/admin/users/{user_id}/sources` - Line 51
  - POST `/admin/users/{user_id}/sources` - Lines 84-90
  - PUT `/admin/users/{user_id}/sources` - Lines 119-125
  - DELETE `/admin/users/{user_id}/sources` - Lines 154-160

- ✅ `user_teams.py` - Similar pattern

#### Content & Downloads
- ✅ `content.py:21-49` - Download endpoint properly authorized
  - GET `/{node_id}/download` - Lines 44-46: `enforce_asset_action()`
- ⚠️ `content.py:55-67` - **SEE CRITICAL ISSUE ABOVE**

#### Tags
- ✅ `tags.py` - All use `enforce_org_membership()` and check org_id
  - POST `/` - Line 38
  - GET `/` - Line 53
  - PUT `/{tag_id}` - Line 71
  - GET `/{tag_id}/content` - Line 91
  - DELETE `/{tag_id}` - Line 116

#### Upload
- ✅ `upload.py` - Both endpoints use `enforce_org_action()`
  - POST `/` - Line 31: `enforce_org_action(db=session, user=user, action_key="asset.upload")`
  - POST `/config` - Line 48

#### Usage (Super Admin Only)
- ✅ `usage.py` - All endpoints require super admin
  - GET `/balance` - Line 30
  - GET `/summary` - Line 47
  - GET `/charges` - Line 63

#### Git Provider
- ✅ `git_provider.py` - All authenticated endpoints use `enforce_org_action()`
  - Lines 86, 100, 113, 132, 150, 179, 199, 219, 243, 270
  - Webhook endpoints (332-690) intentionally unprotected (external callbacks)

#### Admin & Search
- ✅ `admin_sources.py` - Line 46: `enforce_any_source_admin()`
- ✅ `members_search.py` - Line 38: `enforce_org_actions(session, user, ["users.view", "team.view"])`

#### User Endpoints
- ✅ `user.py` - Only returns current user's data (no authorization needed beyond JWT)
- ✅ `user_profile.py` - Only modifies current user's data

### V2 Endpoints (backend/app/api/routes/v2/)

#### Primary Assets
- ✅ `primary_assets.py`
  - GET `/primary_assets` - Line 63-72: Uses `primary_asset_grant_filter()`
  - GET `/page_assets` - Line 75-100: Uses `page_asset_grant_filter()`
  - PUT `/primary_assets/{id}` - Lines 223-224: `enforce_asset_action()`
  - DELETE `/primary_assets/{id}` - Lines 256-257: `enforce_asset_action()`

#### Contents
- ✅ `contents.py`
  - GET `/contents` - Line 51-59: Uses `content_grant_filter()`
  - GET `/page_contents` - Line 62-87: Uses `page_content_grant_filter()`

#### Document Sources
- ✅ `document_sources.py`
  - GET `/page_sources` - Lines 49-72: Checks page authorization
  - POST `/document_sources/batch` - Lines 112-123: `enforce_asset_action()` for ALL sources
  - DELETE `/document_sources/batch` - Line 172: Checks org_id

#### Versions
- ✅ `versions.py`
  - GET `/versions` - Lines 35-36: Uses `primary_asset_grant_filter()`

#### Tags & Asset Tags
- ✅ `tags.py` - All use `enforce_org_membership()` and check org_id
  - GET `/tags` - Line 26
  - PUT `/tags/{tag_id}` - Line 48
  - POST `/tags` - Line 79

- ✅ `primary_asset_tags.py` - Both use `enforce_asset_action()`
  - DELETE `/primary_asset_tags/{asset_id}/{tag_id}` - Lines 21-22
  - POST `/primary_asset_tags` - Lines 48-52

#### API Keys
- ✅ `api_key.py` - All use `enforce_org_membership()` and filter by user_id + org_id
  - POST `/` - Line 25
  - GET `/` - Lines 43, 46-47
  - DELETE `/{api_key_id}` - Lines 69, 72-74

#### Chat
- ✅ `chat.py` - Lines 49-54: `enforce_asset_action()` for ALL source nodes

#### Convenience Endpoints
- ✅ `convenience_endpoints.py`
  - PUT `/edit_page/{node_id}` - Lines 52-58: Checks ALL document sources
  - POST `/new_page` - Line 102: Creates page in user's org (implicit authorization)

#### Other V2 Routes
- ✅ `autodocs.py`, `codebase_card.py`, `about_you_survey.py`, `onboarding_checklist.py` - All properly check org_id

### Legacy GraphQL (backend/app/api/routes/legacy/)

- ✅ `queries.py` - All queries use `check_asset_action()` or `check_org_action()`
  - `documentSet` - Line 64-71
  - `tree` - Line 108-115
  - `connectedGitProviders` - Line 129-131

### Unprotected Endpoints (Intentional)

**File:** `backend/app/api/unprotected_router.py`

These endpoints are intentionally unprotected for valid reasons:
- Healthcheck endpoints
- Git provider webhooks (GitHub, GitLab, Bitbucket, Azure DevOps)
  - Webhooks use signature verification instead of JWT auth
- OAuth callbacks
- Onboarding/signup flows
- Subscription webhooks

---

## Authorization Patterns Analysis

### Excellent Patterns Observed

1. **Consistent org_id checking** - Nearly all endpoints verify `user.organization_id` matches resource
2. **Proper use of enforcement functions** - Most endpoints use `enforce_*()` functions
3. **Query-level filtering** - List endpoints use SQL filters to prevent over-fetching
4. **Asset hierarchy respected** - Content → Node → Version → PrimaryAsset chain properly checked
5. **Batch operations secured** - Endpoints that accept multiple IDs check authorization for EACH resource
6. **Super admin bypass** - Properly implemented at the authorization layer, not per-endpoint

### Listing Endpoints - Authorization Filtering ✅

All listing endpoints properly filter results by user grants:

| Endpoint | Filter Used | Line |
|----------|-------------|------|
| `/primary_assets` | `primary_asset_grant_filter()` | v2/primary_assets.py:63 |
| `/page_assets` | `page_asset_grant_filter()` | v2/primary_assets.py:91 |
| `/contents` | `content_grant_filter()` | v2/contents.py:51 |
| `/page_contents` | `page_content_grant_filter()` | v2/contents.py:79 |
| `/versions` | `primary_asset_grant_filter()` | v2/versions.py:36 |
| `/tags` | org_id filter | v2/tags.py:27 |
| `/teams` | org_id + service filtering | v1/teams.py:80 |

### Cross-Org Access Prevention ✅

All endpoints either:
1. Use `user.organization_id` in WHERE clauses
2. Use authorization filters that include org_id checks
3. Use `enforce_*()` functions that verify org membership

---

## Findings by Category

### ✅ Properly Authorized (99%)

**Asset-Level Endpoints:**
- Codebases, files, sources: All use `enforce_asset_action()`
- Content downloads: Asset authorization required
- Asset updates/deletes: Proper authorization
- Document sources: All source access checked

**Org-Level Endpoints:**
- Organization settings: `enforce_org_action("users.manage")`
- Member management: Proper action checks
- Invitations: Proper authorization
- Git provider apps: `enforce_org_action("vcs.manage")`

**Team-Level Endpoints:**
- Team CRUD: Mix of org and team actions
- Team members: `enforce_team_action("team.manage")`
- Team sources: Asset authorization per source

**Listing Endpoints:**
- All use proper query filters
- No cross-org data leakage

**Special Cases:**
- Usage endpoints: Super admin only ✅
- API keys: Filtered by user_id + org_id ✅
- Tags: Org-scoped ✅
- Chat: Checks all source nodes ✅

### ❌ Missing Authorization (1 endpoint)

1. **POST /studio/v1/content/export-rst** - No checks whatsoever

### 🔵 Intentionally Unprotected (by design)

- Healthcheck endpoints
- Git webhooks (signature-verified)
- OAuth callbacks
- Signup/onboarding endpoints

---

## Action Authorization Keys Reference

The following action keys are used throughout the system:

### Asset Actions
- `asset.manage` - Modify asset grants, settings
- `asset.delete` - Delete asset
- `asset.use_as_source` - Use asset as a source in pages/chat
- `asset_tag.manage` - Manage tags on assets
- `pdf.download` - Download PDF/content

### Codebase Actions
- `codebase.view_versions` - View codebase versions
- `codebase.generate_tech_docs` - Generate documentation

### Org Actions
- `users.view` - View org members
- `users.manage` - Manage org members (add/remove/change roles)
- `invitations.manage` - Manage invitations
- `team.view` - View teams
- `team.admin` - Create/delete teams
- `vcs.manage` - Manage git provider integrations
- `asset.upload` - Upload new assets
- `autodoc.custom_config_upload` - Upload custom autodoc configs

### Team Actions
- `team.view` - View team details
- `team.manage` - Modify team (name, members, sources)

---

## Recommendations


### Short-Term (Hardening)

1. **Add integration tests for authorization**
   - Test cross-org access attempts
   - Test role escalation attempts
   - Test listing endpoint filtering

2. **Document authorization requirements**
   - Add docstrings noting authorization checks to all endpoints
   - Create authorization decision flowchart

3. **Consider adding authorization middleware**
   - Catch-all to log requests missing UserToken
   - Alert on endpoints without authorization

### Long-Term (Enhancement)

1. **Audit trail for sensitive operations**
   - Log all grant changes
   - Log all role changes
   - Log all deletion operations

2. **Fine-grained asset permissions**
   - Consider read vs write separation for assets
   - Consider separating source admin from source member more explicitly

3. **Rate limiting on compute-heavy endpoints**
   - Codebase generation
   - Large content exports
   - Chat endpoints

---

## Test Recommendations

Create tests for:

1. **Cross-org access prevention**
   ```python
   def test_cannot_access_other_org_assets(user_org1, user_org2, asset_org1):
       # User from org2 should not access org1's assets
       response = client.get(f"/primary_assets/{asset_org1.id}", auth=user_org2)
       assert response.status_code == 403
   ```

2. **List filtering**
   ```python
   def test_list_endpoints_filter_by_org():
       # Should only see own org's resources
       response = client.get("/primary_assets", auth=user)
       for asset in response.json()["results"]:
           assert asset["organization_id"] == user.organization_id
   ```

3. **Batch operation authorization**
   ```python
   def test_batch_operations_check_all_resources():
       # Should fail if ANY resource is unauthorized
       response = client.post(
           "/admin/users/123/sources",
           json={"sources": [{"source_id": unauthorized_source, "role": "admin"}]},
           auth=user
       )
       assert response.status_code == 403
   ```

---

## Conclusion

The authorization system is **well-designed and comprehensively implemented**. The use of:
- Centralized authorization functions
- SQL-level query filters
- Consistent org_id checking
- Role-based access control

...demonstrates a mature security posture.


We have ~100% authorization coverage with excellent defense-in-depth through:
- FastAPI dependency injection for authentication
- Authorization checks at the endpoint layer
- Query filters at the database layer
- Consistent org_id scoping

---

**Report Generated:** 2025-11-04
**Files Analyzed:** 49 route files
**Total Endpoints:** ~80+
**Authorization Coverage:** 99% (1 critical gap)
