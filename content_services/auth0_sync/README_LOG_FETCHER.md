# Auth0 Log Fetcher for Testing

This tool fetches historical Auth0 logs and formats them for testing the event processor.

## Overview

The Auth0 log fetcher retrieves real historical logs from the Auth0 Management API and transforms them into the EventBridge event format expected by the event processor. This allows you to test the event processor with real-world events.

## Prerequisites

1. Auth0 credentials configured in your `.env` file:
   - `AUTH0_MGMT_API_DOMAIN`
   - `AUTH0_MGMT_API_CLIENT_ID`
   - `AUTH0_MGMT_API_CLIENT_SECRET`

2. Your Auth0 Management API application must have the `read:logs` scope.

## Usage

### Basic Usage

Fetch the last 7 days of logs (default 100 events):

```bash
cd content_services/auth0_sync
python -m src.event_processor.fetch_auth0_logs
```

This creates `auth0_test_events.json` in the current directory.

### Specify Output File

```bash
python -m src.event_processor.fetch_auth0_logs -o my_events.json
```

### Fetch More Logs

```bash
python -m src.event_processor.fetch_auth0_logs -n 500
```

### Filter by Event Types

Fetch only user signup and login events:

```bash
python -m src.event_processor.fetch_auth0_logs -t s ss
```

Fetch organization membership events:

```bash
python -m src.event_processor.fetch_auth0_logs -t organization_member_added organization_member_deleted
```

Common event types:
- `s` - Successful login
- `ss` - Successful signup
- `sdu` - Successful user deletion
- `organization_member_added` - Member added to organization
- `organization_member_deleted` - Member removed from organization
- `sapi` - Management API operation

### Specify Date Range

Fetch logs from the last 30 days:

```bash
python -m src.event_processor.fetch_auth0_logs -d 30
```

Fetch logs from a specific date:

```bash
python -m src.event_processor.fetch_auth0_logs --from-date 2025-01-01
```

### Verbose Logging

```bash
python -m src.event_processor.fetch_auth0_logs -v
```

### Combined Example

Fetch 200 user-related events from the last 14 days with verbose output:

```bash
python -m src.event_processor.fetch_auth0_logs \
  -n 200 \
  -d 14 \
  -t s ss sdu \
  -o user_events.json \
  -v
```

## Testing Events

Once you've fetched events, test them with the event processor:

```bash
python -m src.event_processor.test_auth0_events auth0_test_events.json
```

## Output Format

The tool outputs a JSON file containing an array of wrapped events:

```json
[
  {
    "message": "{\"id\": \"...\", \"detail\": {...}}"
  },
  ...
]
```

This format is compatible with the existing `test_auth0_events.py` script.

## Workflow

1. **Fetch historical logs**:
   ```bash
   python -m src.event_processor.fetch_auth0_logs -t s ss sdu organization_member_added -n 100
   ```

2. **Review the fetched events**:
   The tool prints a summary of event types fetched.

3. **Test with the event processor**:
   ```bash
   python -m src.event_processor.test_auth0_events auth0_test_events.json
   ```

4. **Iterate**: Adjust filters and re-fetch as needed.

## Troubleshooting

### Authentication Errors

If you see authentication errors, verify:
- Your `.env` file has the correct Auth0 credentials
- Your Auth0 Management API application has the `read:logs` scope
- The credentials are not expired

### No Logs Returned

If no logs are returned:
- Check the date range (use `-v` for verbose logging)
- Verify event types are correct (Auth0 uses short codes like `s`, `ss`, not full names)
- Try without event type filters to see all available logs

### Rate Limiting

Auth0 has rate limits on the Management API. If you hit rate limits:
- Reduce the number of logs fetched with `-n`
- Add delays between requests (future enhancement)
- Use more specific event type filters

## Event Type Reference

Common Auth0 event types:

**Authentication Events:**
- `s` - Successful login
- `f` - Failed login
- `ss` - Successful signup
- `fs` - Failed signup

**User Management:**
- `sdu` - Successful user deletion
- `fdu` - Failed user deletion
- `sce` - Successful change email
- `scp` - Successful change password

**Organization Events:**
- `organization_member_added` - Member added
- `organization_member_deleted` - Member removed

**API Events:**
- `sapi` - Successful API operation
- `fapi` - Failed API operation

For a complete list, see [Auth0 Log Event Type Codes](https://auth0.com/docs/logs/log-event-type-codes).