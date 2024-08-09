#! /usr/bin/env bash

#poetry shell
# source .venv/bin/activate

# which python
# Let the DB start
python driver_db/temp_db.py

# # Run migrations
(cd driver_db/database && alembic upgrade head)

# Create initial data in DB
#python /app/app/initial_data.py


# deactivate