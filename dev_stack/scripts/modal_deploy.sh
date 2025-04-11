#!/bin/bash
#set -e
set -euo pipefail

# Check if an environment argument is provided
if [ -z "$1" ]; then
    echo "Please provide an environment argument."
    exit 1
fi

# Get the environment argument from the command line
environment="dev-eric"

# Navigate to the inspector directory
cd ../content_services/inspector
source .venv/bin/activate  # On Unix/macOS
# Run modal deploy using poetry's Python environment
poetry run modal deploy --env="dev-eric" src/main.py
