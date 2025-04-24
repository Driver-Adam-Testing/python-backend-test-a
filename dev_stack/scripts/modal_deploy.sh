#!/bin/bash
#set -e
set -euo pipefail

# Check if an environment argument is provided
if [ -z "$1" ]; then
    echo "Please provide an environment argument."
    exit 1
fi

# Get the environment argument from the command line
environment="$1"
echo "Deploying to environment: $environment"
# Navigate to the inspector directory
cd ../content_services/inspector
source .venv/bin/activate  # On Unix/macOS
# Run modal deploy using poetry's Python environment
poetry run modal deploy --env="$environment" src/main.py


#cd ../content_services/agent
#source .venv/bin/activate  # On Unix/macOS
## Run modal deploy using poetry's Python environment
#poetry run modal deploy --env="$environment" src/main.py


#cd ../content_services/pdf_preprocessing
#source .venv/bin/activate  # On Unix/macOS
## Run modal deploy using poetry's Python environment
#poetry run modal deploy --env="$environment" src/main.py
