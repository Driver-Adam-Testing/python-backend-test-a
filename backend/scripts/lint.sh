#!/usr/bin/env bash

set -e
set -x

mypy app
(cd packages/driver_db && mypy .)
ruff app
ruff format app --check
