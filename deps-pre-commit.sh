#!/bin/bash

# We use the cdk project python intepreter for simplicity. Can easily change later if this becomes unreasonable.
poetry install --no-root
poetry run python update_interdependent_packages.py
