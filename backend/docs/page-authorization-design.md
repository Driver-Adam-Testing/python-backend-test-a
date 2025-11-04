# Page Authorization Design Proposal

## Problem Statement

Currently, the `/contents`, `/primary_assets`, `/versions`, and other endpoints return content and assets including PAGE-type assets. However, PAGE assets have fundamentally different authorization rules than other asset types:

- **Regular Assets (CODEBASE, FILE)**: User needs a grant to the asset itself
- **PAGE Assets**: User needs grants to ALL source assets referenced by the page (via `DocumentSource` table)

Mixing these authorization schemes in the same query is insecure and leads to potential data leaks.

## Current State

### Model Hierarchy
```
Content → Node → Version → PrimaryAsset
                              ↓
                         PrimaryAssetKind: [CODEBASE, FILE, PAGE, PAGE_TEMPLATE]
```

### Current Authorization
- `content_grant_filter()`: Checks if user has grant to associated PrimaryAsset
- `primary_asset_grant_filter()`: Checks if user has grant to PrimaryAsset
- **Problem**: These don't handle PAGE-specific authorization (checking ALL sources)

### Affected Endpoints
1. `GET /contents` - Returns DerivedContent with PrimaryAsset joins
2. `GET /primary_assets` - Returns PrimaryAsset list
3. `GET /versions` - Returns Version list with PrimaryAsset joins
4. `GET /codebase_card` - Returns PrimaryAsset metadata (already defaults to CODEBASE/FILE)
5. `GET /document_sources` - Manages page↔source links (no change needed)
6. `PUT /edit_page/{node_id}` - Already implements source-based auth correctly

## Proposed Solution

### Core Principle

**No mixed queries. Endpoints handle either pages OR non-pages, never both.**

### Design Rules

1. **Default Behavior**: All endpoints exclude PAGE assets by default
2. **Explicit PAGE Queries**: When `kind=PAGE` is requested, apply source-based authorization
3. **Reject Mixed Queries**: `kind=PAGE,CODEBASE` returns 400 Bad Request
4. **Fail-Safe**: If query type is ambiguous, default to excluding pages

### Authorization Modes

```python
class QueryType(str, Enum):
    PAGES = "pages"        # Requires ALL sources authorized
    NON_PAGES = "non_pages" # Requires asset grant
```

## Implementation Details

### 1. Query Type Determination

```python
# app/authorization/query_filters.py

def determine_query_type(filters: dict) -> QueryContext:
    """
    Determine if query is for pages or non-pages.

    Rules:
    - kind=PAGE or kind=PAGE_TEMPLATE → PAGES
    - kind=CODEBASE or kind=FILE → NON_PAGES
    - No kind filter → NON_PAGES (safe default)
    - kind=PAGE,CODEBASE → HTTPException 400 (reject)
    """
    kind_filter = filters.get('kind', '')
    if not kind_filter:
        return QueryContext(QueryType.NON_PAGES, filters)

    kinds = [k.strip().upper() for k in kind_filter.split(',')]
    page_kinds = {'PAGE', 'PAGE_TEMPLATE'}

    has_pages = any(k in page_kinds for k in kinds)
    has_non_pages = any(k not in page_kinds for k in kinds)

    # Reject mixed queries
    if has_pages and has_non_pages:
        raise HTTPException(
            status_code=400,
            detail="Cannot query pages and non-pages in the same request."
        )

    return QueryContext(
        QueryType.PAGES if has_pages else QueryType.NON_PAGES,
        filters
    )
```

### 2. Authorization Filter Application

```python
def apply_authorization_for_query_type(
    db: Session,
    user_id: str,
    organization_id: str,
    query_context: QueryContext,
) -> Any:
    """Apply appropriate authorization based on query type."""

    if is_super_admin(db, user_id, organization_id):
        return True

    if query_context.query_type == QueryType.NON_PAGES:
        # Standard: exclude pages + require asset grants
        return and_(
            _exclude_pages(),
            primary_asset_grant_filter(db, user_id, organization_id)
        )
    else:  # QueryType.PAGES
        # Pages: include only pages + require ALL source grants
        return and_(
            _only_pages(),
            _all_sources_authorized(db, user_id, organization_id)
        )
```

### 3. Source-Based Authorization Logic

For a page to be accessible, user must have grants to ALL sources:

```python
def _all_sources_authorized(db: Session, user_id: str, organization_id: str) -> Any:
    """
    Check that user has grants to ALL sources for this page.

    SQL Logic: No unauthorized sources exist for this page.
    """
    team_ids = get_user_team_ids(db, user_id, organization_id)
    is_member = is_org_member(db, user_id, organization_id)
    grant_condition = build_grant_condition(user_id, team_ids, is_member)

    SourceNode = aliased(Node)
    SourceVersion = aliased(Version)

    # Subquery: Check if any unauthorized source exists
    unauthorized_source_exists = (
        select(DocumentSource)
        .join(Node, DocumentSource.page_node_id == Node.id)
        .join(Version, Node.version_id == Version.id)
        .where(Version.primary_asset_id == PrimaryAsset.id)  # Outer query link
        .join(SourceNode, DocumentSource.source_node_id == SourceNode.id)
        .join(SourceVersion, SourceNode.version_id == SourceVersion.id)
        .where(
            # This source has NO grant
            ~select(PrimaryAssetRoleGrant)
            .where(
                PrimaryAssetRoleGrant.primary_asset_id == SourceVersion.primary_asset_id,
                PrimaryAssetRoleGrant.organization_id == organization_id,
                grant_condition
            )
            .exists()
        )
        .exists()
    )

    # Page is authorized if NO unauthorized sources exist
    return ~unauthorized_source_exists
```

### 4. Helper Functions

```python
def _exclude_pages() -> Any:
    """Exclude PAGE and PAGE_TEMPLATE from results"""
    return PrimaryAsset.kind.notin_([
        PrimaryAssetKind.PAGE,
        PrimaryAssetKind.PAGE_TEMPLATE
    ])

def _only_pages() -> Any:
    """Include ONLY PAGE and PAGE_TEMPLATE"""
    return PrimaryAsset.kind.in_([
        PrimaryAssetKind.PAGE,
        PrimaryAssetKind.PAGE_TEMPLATE
    ])
```

### 5. Content-Specific Authorization

For `/contents` endpoint which queries `DerivedContent`:

```python
def content_authorization_filter(
    db: Session,
    user_id: str,
    organization_id: str,
    query_context: QueryContext
) -> Any:
    """Authorization filter for DerivedContent queries"""

    if is_super_admin(db, user_id, organization_id):
        return True

    if query_context.query_type == QueryType.NON_PAGES:
        # Traverse Content → Node → Version → PrimaryAsset
        return and_(
            DerivedContent.node.has(
                Node.version.has(
                    Version.primary_asset.has(_exclude_pages())
                )
            ),
            content_grant_filter(db, user_id, organization_id)
        )
    else:  # PAGES
        # Check page sources are all authorized
        return and_(
            DerivedContent.node.has(
                Node.version.has(
                    Version.primary_asset.has(
                        and_(
                            _only_pages(),
                            _all_sources_authorized(db, user_id, organization_id)
                        )
                    )
                )
            )
        )
```

## API Changes

### Endpoint Behavior Changes

#### `GET /primary_assets`

**Before:**
- Returns all assets user has grants to, including pages
- Pages were incorrectly authorized (only checked page asset grant, not source grants)

**After:**
```python
# Default: exclude pages
GET /primary_assets?limit=100
→ Returns CODEBASE, FILE assets only

# Explicit page query with source-based auth
GET /primary_assets?kind=PAGE&limit=1000&document_source_ids=<uuid>
→ Returns PAGE assets where user has grants to ALL sources

# Mixed query: rejected
GET /primary_assets?kind=PAGE,CODEBASE
→ 400 Bad Request: "Cannot query pages and non-pages in the same request"
```

#### `GET /contents`

**Before:**
- Returns content from all assets including pages
- Pages were incorrectly authorized

**After:**
```python
# Default: exclude page content
GET /contents?limit=100
→ Returns content from CODEBASE, FILE assets only

# Explicit page content query (if needed)
GET /contents?node_id=<page_node_id>
→ Returns page content if user has grants to ALL sources
→ Requires kind=PAGE filter or implicit page detection
```

#### `GET /versions`

**Before:**
- Returns versions of all assets including pages

**After:**
```python
# Default: exclude page versions
GET /versions?limit=100
→ Returns versions of CODEBASE, FILE assets only

# Page versions (if needed)
GET /versions?kind=PAGE&primary_asset_id=<page_id>
→ Returns page versions if user has grants to ALL sources
```

#### `GET /codebase_card`

**No change needed** - Already defaults to `kinds=[CODEBASE, FILE]` (line 210-213)

### Implementation in Endpoints

```python
# Example: /primary_assets

@router.get("/primary_assets")
def list_primary_assets(
    request: Request,
    session: CurrentSession,
    user: UserToken,
    pagination: Pagination,
) -> ListWithCount[PrimaryAssetDetailRead]:

    filters = dict(request.query_params)

    # Determine query type (raises 400 if mixed)
    query_context = determine_query_type(filters)

    # Apply appropriate authorization
    query = (
        select(PrimaryAsset)
        .where(PrimaryAsset.organization_id == user.organization_id)
        .where(apply_authorization_for_query_type(
            session,
            user.user_id,
            user.organization_id,
            query_context
        ))
    )

    # Continue with normal filtering, sorting, pagination
    query = apply_filters_to_query(query, filters, PrimaryAsset)
    # ... rest of implementation
```

## Testing Strategy

### Unit Tests

```python
# Test query type determination
def test_determine_query_type_no_filter():
    ctx = determine_query_type({})
    assert ctx.query_type == QueryType.NON_PAGES

def test_determine_query_type_page():
    ctx = determine_query_type({'kind': 'PAGE'})
    assert ctx.query_type == QueryType.PAGES

def test_determine_query_type_codebase():
    ctx = determine_query_type({'kind': 'CODEBASE'})
    assert ctx.query_type == QueryType.NON_PAGES

def test_determine_query_type_mixed_rejected():
    with pytest.raises(HTTPException) as exc:
        determine_query_type({'kind': 'PAGE,CODEBASE'})
    assert exc.value.status_code == 400

# Test authorization filters
def test_page_authorization_all_sources_granted(session, user):
    # User has grants to all sources → page visible
    ...

def test_page_authorization_missing_source_grant(session, user):
    # User missing grant to one source → page NOT visible
    ...

def test_non_page_authorization_excludes_pages(session, user):
    # Query for CODEBASE should not return pages
    ...
```

### Integration Tests

```python
def test_list_primary_assets_excludes_pages_by_default(client, auth_headers):
    response = client.get("/v2/primary_assets", headers=auth_headers)
    assets = response.json()['results']
    assert all(a['kind'] not in ['PAGE', 'PAGE_TEMPLATE'] for a in assets)

def test_list_primary_assets_pages_with_source_auth(client, auth_headers):
    response = client.get("/v2/primary_assets?kind=PAGE", headers=auth_headers)
    # Should only return pages where user has ALL source grants
    ...

def test_list_primary_assets_mixed_rejected(client, auth_headers):
    response = client.get("/v2/primary_assets?kind=PAGE,CODEBASE", headers=auth_headers)
    assert response.status_code == 400
```

## Migration Plan

### Phase 1: Implementation (No Breaking Changes)

1. Add new authorization functions to `app/authorization/query_filters.py`:
   - `determine_query_type()`
   - `apply_authorization_for_query_type()`
   - `content_authorization_filter()`
   - `_exclude_pages()`, `_only_pages()`, `_all_sources_authorized()`

2. Update endpoints one by one:
   - `/primary_assets`
   - `/contents`
   - `/versions`
   - `/codebase_card` (verify behavior)

3. Add comprehensive tests

### Phase 2: Validation

1. Deploy to staging
2. Monitor logs for:
   - Any PAGE queries in non-page endpoints
   - Authorization failures
   - Performance issues with source-based auth queries

3. Add database indexes if needed:
   - `document_source.page_node_id`
   - `document_source.source_node_id`

### Phase 3: Documentation

1. Update API docs with new query patterns
2. Document the authorization model
3. Add examples for page queries
4. Create migration guide for frontend

## Edge Cases

### 1. Page with no sources
- **Behavior**: Accessible (no unauthorized sources exist)
- **Rationale**: Empty source list means no authorization failures

### 2. Source deleted but DocumentSource remains
- **Mitigation**: Ensure proper CASCADE deletes in DB schema
- **Check**: Verify `DocumentSource.source_node_id` has `ondelete="CASCADE"`

### 3. Circular page references
- **Not applicable**: Pages reference sources (CODEBASE/FILE), not other pages

### 4. Super admin access
- **Behavior**: Super admins see everything regardless of query type
- **Implementation**: Early return `True` in all authorization filters

### 5. Performance with many sources
- **Concern**: Complex nested subqueries for source authorization
- **Mitigation**:
  - Add indexes on `DocumentSource` join keys
  - Monitor query performance
  - Consider caching source grants if needed

## Security Considerations

### Fail-Safe Defaults
- Default to `QueryType.NON_PAGES` when ambiguous
- Exclude pages by default unless explicitly requested
- Reject mixed queries rather than attempting to handle them

### Authorization Validation
- Always check organization_id match
- Super admin bypass is explicit and logged
- Source-based auth checks ALL sources (no partial access)

### Audit Trail
- Log query type determination for sensitive operations
- Log authorization failures with user_id and asset_id
- Monitor for repeated 400 errors (mixed query attempts)

## Performance Considerations

### Query Complexity
- Source-based authorization adds nested subqueries
- Potentially slower than simple grant checks
- **Mitigation**: Add indexes, monitor slow query log

### Recommended Indexes
```sql
CREATE INDEX idx_document_source_page_node_id ON document_source(page_node_id);
CREATE INDEX idx_document_source_source_node_id ON document_source(source_node_id);
```

### Caching Strategy (Future)
- Consider caching source authorization results per user/page
- Cache invalidation on grant changes
- Use Redis or similar for distributed caching

## Future Enhancements

### 1. Dedicated Page Endpoints
Create specialized endpoints for page operations:
```
GET /pages              # List pages with source-based auth
GET /pages/{id}         # Get specific page
GET /pages/{id}/content # Get page content
GET /pages/by-sources   # Find pages using specific sources
```

### 2. Batch Authorization Checks
Optimize repeated source checks:
```python
def batch_check_source_authorization(db, user_id, page_ids) -> dict[UUID, bool]:
    """Check authorization for multiple pages at once"""
    ...
```

### 3. Authorization Cache
Cache grant check results to reduce DB queries:
```python
@cached(ttl=300)  # 5 minute cache
def check_all_sources_authorized(user_id, page_id) -> bool:
    ...
```

## Open Questions

1. **Should `/contents` support page content queries?**
   - Option A: Yes, with `kind=PAGE` filter
   - Option B: No, use dedicated `/page_content/{node_id}` endpoint
   - **Recommendation**: Start with Option A, migrate to B if needed

2. **Should `/versions` support page versions?**
   - Do we ever need to list page versions?
   - Or are pages always accessed directly by ID?
   - **Action**: Investigate frontend usage patterns

3. **Error message granularity**
   - Should we reveal if page exists but user lacks source access?
   - Or return 404 for both missing pages and unauthorized pages?
   - **Recommendation**: 404 for both (security by obscurity)

## Success Criteria

1. ✅ No page data leaks through non-page endpoints
2. ✅ Explicit page queries work with source-based auth
3. ✅ Mixed queries are rejected with clear error messages
4. ✅ Performance is acceptable (<100ms additional latency for page queries)
5. ✅ All existing non-page functionality continues to work
6. ✅ Comprehensive test coverage (>90% for new authorization code)
7. ✅ Zero security incidents related to page authorization

## References

- TODO comment in `contents.py:56`: "you should only be able to access the content for a page if you are granted access to the page and also have access to all sources!!!!!"
- Existing source-based auth in `convenience_endpoints.py:52-58` (edit_page endpoint)
- Authorization helpers in `app/authorization/query_filters.py`
- Grant checking logic in `app/authorization/core.py`
