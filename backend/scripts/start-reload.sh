#! /usr/bin/env sh
set -e

# If there's a setEnv.sh script in the / directory, run it before starting
echo "Checking for setEnv script"
if [ -f 'setEnv.sh' ] ; then
    echo "Running script setEnv.sh"
    sh setEnv.sh
else
    echo "There is no script setEnv.sh"
fi

if [ -f /app/app/main.py ]; then
    DEFAULT_MODULE_NAME=app.main
elif [ -f /app/main.py ]; then
    DEFAULT_MODULE_NAME=main
fi
MODULE_NAME=${MODULE_NAME:-$DEFAULT_MODULE_NAME}
VARIABLE_NAME=${VARIABLE_NAME:-app}
export APP_MODULE=${APP_MODULE:-"$MODULE_NAME:$VARIABLE_NAME"}

HOST=${HOST:-0.0.0.0}
PORT=${PORT:-80}
LOG_LEVEL=${LOG_LEVEL:-info}

# If there's a prestart.sh script in the /app directory or other path specified, run it before starting
PRE_START_PATH=${PRE_START_PATH:-/app/prestart.sh}
echo "uvicorn: Checking for script in $PRE_START_PATH"
if [ -f $PRE_START_PATH ] ; then
    echo "uvicorn: Running script $PRE_START_PATH"
    . "$PRE_START_PATH"
else
    echo "uvicorn: There is no script $PRE_START_PATH"
fi

# If you want to test multiple workers, reload needs to be disabled
# exec uvicorn --host $HOST --port $PORT --log-level $LOG_LEVEL --workers 10 "$APP_MODULE"

exec uvicorn --reload --host $HOST --port $PORT --log-level $LOG_LEVEL --reload-dir /packages --reload-dir /driver_db "$APP_MODULE"
