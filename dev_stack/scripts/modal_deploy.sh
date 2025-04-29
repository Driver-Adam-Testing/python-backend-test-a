#!/bin/bash
#set -e
set -euo pipefail
export MODAL_TOKEN_ID="ak-q4cyt5kfPmyRJKhppJgUWy"
export MODAL_TOKEN_SECRET="as-kpe860h745ygh1W3kPHg1E"
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
#poetry install --no-root
# Run modal deploy using poetry's Python environment
#poetry run modal deploy --env="$environment" src/main.py
cd ../../
#echo $PWD
#echo $CWD

cd ./content_services/agent
poetry install --no-root
# Run modal deploy using poetry's Python environment
poetry run modal deploy --env="$environment" src/main.py
#
cd ../../
#
cd ./content_services/pdf_preprocessing
poetry install --no-root
## Run modal deploy using poetry's Python environment
poetry run modal deploy --env="$environment" src/main.py
#
cd ../../
#
cd ../content_services/autodocs
poetry install --no-root
## Run modal deploy using poetry's Python environment
poetry run modal deploy --env="$environment" src/main.py
