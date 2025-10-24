def build_modal_deploy_script(token_id: str, token_secret: str) -> str:
    script = f"""
#!/bin/bash

# set -euo pipefail
set -eo pipefail

# Check if an environment argument is provided
if [ -z "$1" ]; then
    echo "Please provide an environment argument."
    exit 1
fi

# Get the environment argument from the command line
environment="$1"
echo "Deploying to environment: $environment"

modal token set --token-id {token_id} --token-secret {token_secret} --profile=driver-ai
modal profile activate driver-ai

# Navigate to the inspector directory
cd ../content_services/inspector
poetry install --no-root

poetry run modal deploy --env="$environment" src/main.py

cd ../../

cd ./content_services/agent
poetry install --no-root
poetry run modal deploy --env="$environment" src/main.py

cd ../../

cd ./content_services/pdf_preprocessing
poetry install --no-root
poetry run modal deploy --env="$environment" src/main.py

cd ../../

cd ./content_services/autodocs
poetry install --no-root
poetry run modal deploy --env="$environment" src/main.py

cd ../../

cd ./content_services/auth0_sync
poetry install --no-root
poetry run modal deploy --env="$environment" src/modal_main.py

"""

    return script
