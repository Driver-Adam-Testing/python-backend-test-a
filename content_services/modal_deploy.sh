#!/bin/bash
set -e

# Check if an environment argument is provided
if [ -z "$1" ]; then
    echo "Please provide an environment argument."
    exit 1
fi

# Get the environment argument from the command line
environment=$1

# Navigate to the inspector directory
cd inspector
# Perform modal deploy on src/main.py with the environment argument
modal deploy --env=$environment src/main.py
# Navigate back to the original directory
cd ..
# Navigate to the onboarding directory
cd onboarding
# Perform modal deploy on src/main.py with the environment argument
modal deploy --env=$environment src/main.py
# Navigate back to the original directory
cd ..
# Navigate to the pdf_preprocessing directory
cd pdf_preprocessing
# Perform modal deploy on src/main.py with the environment argument
modal deploy --env=$environment src/main.py
cd ..
# Navigate to the embedding directory
cd embedding
# Perform modal deploy on src/main.py with the environment argument
modal deploy --env=$environment src/main.py
cd ..
# Navigate to the auth0_sync directory
cd auth0_sync
# Perform modal deploy on src/auth0_sync_modal.py with the environment argument
modal deploy --env=$environment src/auth0_sync_modal.py
