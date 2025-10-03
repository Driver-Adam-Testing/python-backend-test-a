# Azure DevOps Bulk Repository Management Scripts

This directory contains scripts for bulk creation and management of Azure DevOps repositories, primarily used for testing rate limiting and integration scenarios.

## Prerequisites

1. **Azure DevOps Personal Access Token (PAT)**
   - Go to Azure DevOps → User Settings → Personal Access Tokens
   - Create a new token with **Code (Read & Write)** permissions
   - Save the token securely (you won't be able to see it again)

2. **Python Dependencies**
   - Ensure you have `poetry` installed
   - Run `poetry install` in the parent directory if not already done

3. **Azure DevOps Organization and Project**
   - You need an existing Azure DevOps organization
   - You need an existing project within that organization

## Files

### `bulk_create_repos.py`
Main Python script that handles all repository operations:
- Create multiple repositories (sequential or parallel)
- Delete repositories (individually or in bulk)
- List all repositories in a project
- Verify token and project access
- Handle rate limiting gracefully

### `create_repos.sh`
Bash wrapper script for convenient execution with defaults and common operations.

## Usage

### Quick Start

1. **Edit credentials in `create_repos.sh`**:
   ```bash
   PAT="your-personal-access-token"
   ORGANIZATION="your-org-name"
   PROJECT="your-project-name"
   ```

2. **Verify your setup**:
   ```bash
   ./create_repos.sh --verify
   ```

3. **Create repositories**:
   ```bash
   # Create 10 repos sequentially
   ./create_repos.sh --count 10

   # Create 20 repos in parallel
   ./create_repos.sh --count 20 --parallel
   ```

### Direct Python Script Usage

```bash
# Verify token and project
python bulk_create_repos.py \
  --pat "YOUR_PAT" \
  --organization "your-org" \
  --project "YourProject" \
  --verify-token

# Create 10 repositories sequentially
python bulk_create_repos.py \
  --pat "YOUR_PAT" \
  --organization "your-org" \
  --project "YourProject" \
  --count 10 \
  --prefix "test-repo" \
  --delay 1.0

# Create repositories in parallel (more aggressive)
python bulk_create_repos.py \
  --pat "YOUR_PAT" \
  --organization "your-org" \
  --project "YourProject" \
  --count 50 \
  --prefix "test-repo" \
  --parallel \
  --workers 3

# List all repositories
python bulk_create_repos.py \
  --pat "YOUR_PAT" \
  --organization "your-org" \
  --project "YourProject" \
  --list

# Delete all test repositories
python bulk_create_repos.py \
  --pat "YOUR_PAT" \
  --organization "your-org" \
  --project "YourProject" \
  --delete-all \
  --include test-repo
```

## Command Line Options

### Authentication
- `--pat`: Azure DevOps Personal Access Token (required)
- `--organization`: Azure DevOps organization name (required)
- `--project`: Project name where repos will be created (required)

### Creation Options
- `--count`: Number of repositories to create (default: 10)
- `--prefix`: Repository name prefix (default: "test-repo")
- `--parallel`: Create repositories in parallel mode
- `--workers`: Number of parallel workers (default: 3)
- `--delay`: Delay between requests in sequential mode (default: 1.0 seconds)

### Management Options
- `--cleanup`: Delete repositories instead of creating them
- `--delete-all`: Delete ALL repositories in the project (except default)
- `--list`: List all repositories in the project
- `--verify-token`: Verify token and project access only

### Filtering Options (for deletion)
- `--include`: Include only repositories containing these patterns
- `--exclude`: Exclude repositories containing these patterns
- `--force`: Skip confirmation prompts

## Rate Limiting Considerations

Azure DevOps has stricter rate limits compared to other Git providers:
- Default rate limit: ~60 requests per minute
- The script automatically handles rate limiting with:
  - Exponential backoff
  - Retry-After header parsing
  - Conservative delays between requests

### Recommendations:
- **Sequential mode**: Use for production or when stability is important
  - Default delay of 1.0 second between requests
  - Less likely to trigger rate limits

- **Parallel mode**: Use for testing rate limit behavior
  - Default of 3 workers (conservative for Azure DevOps)
  - More likely to trigger rate limits
  - Good for testing rate limit handling

## Features

1. **Repository Creation**
   - Creates repositories with initial README.md
   - Adds descriptive content and timestamps
   - Handles both sequential and parallel creation
   - Automatic rate limit handling

2. **Repository Management**
   - List all repositories with details
   - Bulk deletion with pattern matching
   - Skip default project repository on deletion
   - Confirmation prompts for safety

3. **Error Handling**
   - Comprehensive error messages
   - Rate limit detection and retry
   - Token validation
   - Project verification

4. **Monitoring**
   - Request counting
   - Rate limit tracking
   - Success/failure summary
   - Detailed operation logs

## Troubleshooting

### Common Issues

1. **Authentication Failed**
   - Verify your PAT is valid and not expired
   - Ensure PAT has "Code (Read & Write)" permissions
   - Check organization and project names are correct

2. **Rate Limiting**
   - Reduce worker count in parallel mode
   - Increase delay in sequential mode
   - Wait for rate limit reset (shown in output)

3. **Project Not Found**
   - Verify project name spelling
   - Ensure PAT has access to the project
   - Check project exists in the organization

### Error Messages

- `HTTP 401`: Authentication failed - check PAT
- `HTTP 403`: Access denied - check permissions
- `HTTP 404`: Resource not found - check org/project names
- `HTTP 429`: Rate limited - wait or reduce request rate

## Security Notes

- Never commit PAT tokens to source control
- Use environment variables for tokens in production
- Rotate PATs regularly
- Use minimal required permissions

## Testing Scenarios

### Rate Limit Testing
```bash
# Aggressive parallel creation to trigger rate limits
python bulk_create_repos.py \
  --pat "YOUR_PAT" \
  --organization "your-org" \
  --project "YourProject" \
  --count 100 \
  --parallel \
  --workers 10
```

### Integration Testing
```bash
# Create a set of test repos
./create_repos.sh --count 5 --prefix "integration-test"

# Run your integration tests...

# Clean up afterwards
./create_repos.sh --delete-all --include "integration-test" --force
```

## Comparison with Other Providers

| Feature | Azure DevOps | Bitbucket | GitHub |
|---------|-------------|-----------|---------|
| Rate Limit | 60/min | 1000/hour | 5000/hour |
| Auth Method | PAT/OAuth | Access Token | PAT/OAuth |
| Parallel Workers | 3 (recommended) | 5 | 10 |
| Delay (sequential) | 1.0s | 0.1s | 0.1s |

## Contributing

When modifying these scripts:
1. Test with small counts first
2. Verify rate limit handling works
3. Update documentation for new features
4. Follow existing error handling patterns
