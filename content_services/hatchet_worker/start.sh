#! /usr/bin/env sh
set -e

# If there's a setEnv.sh script in the / directory, run it before starting
echo "Checking for setEnv script."
if [ -f '/setEnv.sh' ] ; then
    echo "Running script /setEnv.sh"
    sh /setEnv.sh
    echo "$(cat /setEnv.sh)"
else
    echo "There is no script /setEnv.sh"
fi

echo "Hatchet Worker running off branch ${GIT_BRANCH} commit ${GIT_COMMIT}"
export HATCHET_CLIENT_TLS_STRATEGY=none

poetry run python src/worker.py