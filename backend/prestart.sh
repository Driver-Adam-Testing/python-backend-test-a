#! /usr/bin/env bash

# Let the DB start
python /app/app/backend_pre_start.py

# Run migrations
(cd /packages/driver_db/database && alembic upgrade head)

# Create initial data in DB
python /app/app/initial_data.py
