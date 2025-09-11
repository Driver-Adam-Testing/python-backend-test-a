# Auth0 Organization and User Sync

This directory contains scripts to synchronize Auth0 organizations and users with the local database.

## Prerequisites

1. Ensure the database migrations are up to date:
```bash
cd /path/to/python-backend
poetry run alembic -c driver_db/database/alembic.ini upgrade head
```

2. Ensure you have the following environment variables set:
- `AUTH0_DOMAIN`
- `AUTH0_MGMT_API_DOMAIN`
- `AUTH0_MGMT_API_CLIENT_ID`
- `AUTH0_MGMT_API_CLIENT_SECRET`
- Database connection variables

## Scripts

### 1. Full Sync Script (`sync_auth0_orgs_and_users.py`)

This script performs a complete sync of all Auth0 organizations and users to the local database.

#### Usage:

```bash
# Option 1: From the python-backend/backend directory:
cd backend
poetry run python scripts/sync_auth0_orgs_and_users.py --dry-run
poetry run python scripts/sync_auth0_orgs_and_users.py --verbose
poetry run python scripts/sync_auth0_orgs_and_users.py

# Option 2: From the python-backend directory (also works):
poetry run python backend/scripts/sync_auth0_orgs_and_users.py --dry-run --verbose
```

#### What it does:
1. Fetches all organizations from Auth0
2. Fetches all users from Auth0
3. Fetches organization memberships for each user
4. Creates or updates organizations in the database
5. Creates or updates users in the database
6. Creates organization membership records
7. Sets `synced_at` timestamp for tracking

#### Output:
The script provides a summary showing:
- Organizations created/updated/skipped
- Users created/updated/skipped
- Memberships created/skipped
- Any errors encountered

### 2. Incremental Sync Module (`auth0_incremental_sync.py`)

This module provides functions for syncing individual entities, useful for webhook-based updates.

#### Functions:

```python
from auth0_incremental_sync import (
    sync_single_user,
    sync_single_organization,
    sync_user_membership,
    sync_user_with_organizations,
    handle_auth0_webhook
)

# Sync a single organization
sync_single_organization("org_xxxxx")

# Sync a single user
sync_single_user("auth0|xxxxx")

# Add/remove user membership
sync_user_membership("auth0|xxxxx", "org_xxxxx", action="add")
sync_user_membership("auth0|xxxxx", "org_xxxxx", action="remove")

# Sync user with all their organizations
sync_user_with_organizations("auth0|xxxxx")

# Handle Auth0 webhook events
handle_auth0_webhook("user.created", webhook_payload)
```

#### Webhook Events Supported:
- `user.created` - Creates new user
- `user.updated` - Updates existing user
- `organization.created` - Creates new organization
- `organization.updated` - Updates existing organization
- `organization.member_added` - Adds user to organization
- `organization.member_removed` - Removes user from organization

## Database Tables

The sync scripts work with three tables:

### `organizations`
- `id` (PK): Auth0 organization ID (e.g., "org_xxxxx")
- `name`: Organization name (unique slug)
- `display_name`: Display name
- `org_metadata`: JSONB metadata from Auth0
- `created_at`, `updated_at`: Timestamps
- `synced_at`: Last sync timestamp

### `users`
- `id` (PK): Auth0 user ID (e.g., "auth0|xxxxx")
- `email`: User email
- `name`: User name
- `created_at`, `updated_at`: Timestamps
- `synced_at`: Last sync timestamp

### `org_memberships`
- `id` (PK): UUID
- `org_id` (FK): Organization ID
- `user_id` (FK): User ID
- Unique constraint on (org_id, user_id)

## Scheduling

For production use, consider:

1. **Initial Migration**: Run the full sync script once to populate the database
2. **Regular Syncs**: Schedule the full sync script to run periodically (e.g., daily) as a backup
3. **Real-time Updates**: Use Auth0 webhooks with the incremental sync module for real-time updates

Example cron job for daily sync:
```bash
# Run from backend directory
0 2 * * * cd /path/to/python-backend/backend && poetry run python scripts/sync_auth0_orgs_and_users.py >> /var/log/auth0_sync.log 2>&1
```

## Error Handling

Both scripts include comprehensive error handling:
- Individual entity failures don't stop the entire sync
- Errors are logged and included in the summary
- Scripts return non-zero exit codes if errors occurred
- Database transactions are properly rolled back on failure

## Performance Considerations

- The full sync script uses pagination (100 items per page) to handle large datasets
- Database operations are batched in a single transaction per sync
- Incremental sync functions can reuse database sessions for efficiency
- Consider adding database indexes if sync performance becomes an issue

## Monitoring

Monitor the following:
- `synced_at` timestamps to ensure regular syncs
- Error logs for failed syncs
- Discrepancies between Auth0 and database counts
- Webhook delivery failures (if using webhooks)

## Troubleshooting

1. **Authentication Errors**: Check Auth0 management API credentials
2. **Database Connection Errors**: Verify database connection settings
3. **Missing Organizations/Users**: Run full sync to catch up
4. **Duplicate Key Errors**: Check for data integrity issues
5. **Rate Limiting**: Auth0 has rate limits; implement exponential backoff if needed

## Security Notes

- Store Auth0 credentials securely (use environment variables or secrets manager)
- Limit management API scopes to only what's needed:
  - `read:organizations`
  - `read:organization_members`
  - `read:users`
- Audit sync operations regularly
- Consider encrypting sensitive data in the database
