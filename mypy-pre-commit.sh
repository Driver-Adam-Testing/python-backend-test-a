#!/bin/bash

# Get list of staged files
staged_files=$(git diff --cached --name-only --diff-filter=d | grep '\.py$')

# If no staged files, exit
if [ -z "$staged_files" ]; then
  echo "No staged Python files to check"
  exit 0
fi

# Run mypy on the staged files, ignoring import-untyped errors
mypy --ignore-missing-imports $staged_files
