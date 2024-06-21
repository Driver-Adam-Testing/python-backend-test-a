#!/bin/bash

# Get list of tracked files
tracked_files=$(git ls-files | grep '\.py$')

# If no tracked files, exit
if [ -z "$tracked_files" ]; then
  echo "No tracked Python files to check"
  exit 0
fi

# Run mypy on the tracked files, ignoring import-untyped errors
mypy --ignore-missing-imports $tracked_files
