#!/bin/bash

# Azure DevOps Bulk Repository Creation Script
# This script wraps the Python bulk_create_repos.py script with convenient defaults

# Configuration - Replace these with your actual values
PAT=""  # Your Azure DevOps Personal Access Token
ORGANIZATION="driverai"  # Your Azure DevOps organization (e.g., "myorg")
PROJECT="backend"  # Your Azure DevOps project name (e.g., "MyProject")

# Default settings
COUNT=10  # Number of repos to create
PREFIX="backend-test-repo"  # Repository name prefix
MODE="parallel"  # "sequential" or "parallel"
WORKERS=5  # Number of parallel workers (if using parallel mode)
DELAY=1.0  # Delay between requests in sequential mode

# Function to display usage
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -p, --pat PAT              Azure DevOps Personal Access Token"
    echo "  -o, --org ORGANIZATION     Azure DevOps organization"
    echo "  -j, --project PROJECT      Azure DevOps project name"
    echo "  -c, --count COUNT          Number of repositories to create (default: $COUNT)"
    echo "  -x, --prefix PREFIX        Repository name prefix (default: $PREFIX)"
    echo "  --parallel                 Use parallel mode for creation"
    echo "  --cleanup                  Delete repositories instead of creating"
    echo "  --delete-all               Delete ALL repositories in project"
    echo "  --list                     List all repositories"
    echo "  --verify                   Verify token and project only"
    echo "  -h, --help                 Show this help message"
    echo ""
    echo "Examples:"
    echo "  # Verify token and project:"
    echo "  $0 --verify"
    echo ""
    echo "  # Create 20 repositories sequentially:"
    echo "  $0 --count 20"
    echo ""
    echo "  # Create 50 repositories in parallel:"
    echo "  $0 --count 50 --parallel"
    echo ""
    echo "  # List all repositories:"
    echo "  $0 --list"
    echo ""
    echo "  # Delete all test repositories:"
    echo "  $0 --delete-all --include test-repo"
    echo ""
}

# Parse command line arguments
ACTION="create"
PARALLEL_FLAG=""
EXTRA_ARGS=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -p|--pat)
            PAT="$2"
            shift 2
            ;;
        -o|--org)
            ORGANIZATION="$2"
            shift 2
            ;;
        -j|--project)
            PROJECT="$2"
            shift 2
            ;;
        -c|--count)
            COUNT="$2"
            shift 2
            ;;
        -x|--prefix)
            PREFIX="$2"
            shift 2
            ;;
        --parallel)
            PARALLEL_FLAG="--parallel"
            shift
            ;;
        --cleanup)
            ACTION="cleanup"
            shift
            ;;
        --delete-all)
            ACTION="delete-all"
            shift
            ;;
        --list)
            ACTION="list"
            shift
            ;;
        --verify)
            ACTION="verify"
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            EXTRA_ARGS="$EXTRA_ARGS $1"
            shift
            ;;
    esac
done

# Check required parameters
if [ -z "$PAT" ]; then
    echo "Error: Personal Access Token is required"
    echo "Set it in the script or use --pat option"
    exit 1
fi

if [ -z "$ORGANIZATION" ]; then
    echo "Error: Organization is required"
    echo "Set it in the script or use --org option"
    exit 1
fi

if [ -z "$PROJECT" ]; then
    echo "Error: Project is required"
    echo "Set it in the script or use --project option"
    exit 1
fi

# Build the command based on action
case $ACTION in
    verify)
        echo "Verifying Azure DevOps token and project..."
        poetry run python bulk_create_repos.py \
            --pat="$PAT" \
            --organization "$ORGANIZATION" \
            --project "$PROJECT" \
            --verify-token
        ;;

    list)
        echo "Listing repositories in project '$PROJECT'..."
        poetry run python bulk_create_repos.py \
            --pat="$PAT" \
            --organization "$ORGANIZATION" \
            --project "$PROJECT" \
            --list
        ;;

    delete-all)
        echo "Deleting all repositories in project '$PROJECT'..."
        poetry run python bulk_create_repos.py \
            --pat="$PAT" \
            --organization "$ORGANIZATION" \
            --project "$PROJECT" \
            --delete-all \
            $EXTRA_ARGS
        ;;

    cleanup)
        echo "Cleaning up test repositories..."
        poetry run python bulk_create_repos.py \
            --pat="$PAT" \
            --organization "$ORGANIZATION" \
            --project "$PROJECT" \
            --count $COUNT \
            --prefix "$PREFIX" \
            --cleanup \
            $EXTRA_ARGS
        ;;

    create)
        echo "Creating $COUNT repositories in project '$PROJECT'..."
        echo "Organization: $ORGANIZATION"
        echo "Prefix: $PREFIX"
        if [ -n "$PARALLEL_FLAG" ]; then
            echo "Mode: Parallel (workers: $WORKERS)"
        else
            echo "Mode: Sequential (delay: $DELAY)"
        fi

        poetry run python bulk_create_repos.py \
            --pat="$PAT" \
            --organization "$ORGANIZATION" \
            --project "$PROJECT" \
            --count $COUNT \
            --prefix "$PREFIX" \
            --delay $DELAY \
            --workers $WORKERS \
            $PARALLEL_FLAG \
            $EXTRA_ARGS
        ;;
esac


# Example commands (commented out for safety):
# ==========================================

# 1. Verify token and project access:
# poetry run python bulk_create_repos.py \
# --pat='YOUR_PAT_HERE' \
# --organization 'your-org' \
# --project 'YourProject' \
# --verify-token

# 2. Create 10 repositories sequentially (conservative, less likely to hit rate limits):
# poetry run python bulk_create_repos.py \
# --pat='YOUR_PAT_HERE' \
# --organization 'your-org' \
# --project 'YourProject' \
# --count 10 \
# --prefix "test-repo" \
# --delay 1.0

# 3. Create 50 repositories in parallel (aggressive, more likely to trigger rate limits):
# poetry run python bulk_create_repos.py \
# --pat='YOUR_PAT_HERE' \
# --organization 'your-org' \
# --project 'YourProject' \
# --count 50 \
# --prefix "test-repo-parallel" \
# --parallel \
# --workers 3

# 4. List all repositories in the project:
# poetry run python bulk_create_repos.py \
# --pat='YOUR_PAT_HERE' \
# --organization 'your-org' \
# --project 'YourProject' \
# --list

# 5. Delete all test repositories (with pattern matching):
# poetry run python bulk_create_repos.py \
# --pat='YOUR_PAT_HERE' \
# --organization 'your-org' \
# --project 'YourProject' \
# --delete-all \
# --include test-repo

# 6. Clean up specific test repositories:
# poetry run python bulk_create_repos.py \
# --pat='YOUR_PAT_HERE' \
# --organization 'your-org' \
# --project 'YourProject' \
# --count 10 \
# --prefix "test-repo" \
# --cleanup
