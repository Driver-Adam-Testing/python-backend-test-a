#!/usr/bin/env bash

set -e
set -x

mypy app
mypy driver_db
ruff app
ruff format app --check
