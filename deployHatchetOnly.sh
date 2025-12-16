#!/bin/bash
set -euo pipefail

echo "deploying backend..."

#If there's a setEnv.sh script in the / directory, copy it and run it before starting
echo "Checking for setEnv script"
if [ -f "../build/setEnv.sh" ] ; then
    echo "Copy and run script setEnv.sh from deployment repo"
    cp "../build/setEnv.sh" .
    source setEnv.sh
elif [ -f "setEnv.sh" ] ; then
  source setEnv.sh
  echo "Using local setEnv.sh"
else
    echo "There is no script setEnv.sh"
fi

#Push backend contianers
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT.dkr.ecr.$AWS_REGION.amazonaws.com

HATCHET_WORKER_IMAGE_NAME=hatchet-worker
HATCHET_WORKER_TAG=latest
HATCHET_WORKER_REPO_URI=$AWS_ACCOUNT.dkr.ecr.$AWS_REGION.amazonaws.com/$HATCHET_WORKER_IMAGE_NAME:$HATCHET_WORKER_TAG

DOCKER_DEFAULT_PLATFORM=linux/amd64 docker build --build-arg GIT_COMMIT=$(git rev-parse HEAD) --build-arg GIT_BRANCH=$(git rev-parse --abbrev-ref HEAD) -t $HATCHET_WORKER_REPO_URI -f content_services/Dockerfile .
echo $HATCHET_WORKER_REPO_URI

docker push "$HATCHET_WORKER_REPO_URI"


CLUSTER_NAME=$(aws ecs list-clusters --query "clusterArns[?contains(@, 'V2BaseInfrastructureStack-BaseInfrastructureCoreInfrastructureCluster')]" --output text)

SERVICE_NAME=$(aws ecs list-services --cluster $CLUSTER_NAME --query "serviceArns[?contains(@, 'DriverApiStack-ApiBackendBackendApiService')]" --output text)

HATCHET_WORKER_SERVICE_NAME=$(aws ecs list-services --cluster $CLUSTER_NAME --query "serviceArns[?contains(@, 'DriverApiStack-HatchetWorkerHatchetWorkerSvc')]" --output text)

echo "Forcing hatchet worker redeploy..."

aws --no-cli-pager ecs update-service --cluster $CLUSTER_NAME --service $HATCHET_WORKER_SERVICE_NAME --force-new-deployment

echo "Waiting up to 5 minutes for ECS service to stabilize..."
set +e
timeout 300 aws ecs wait services-stable --cluster $CLUSTER_NAME --services $HATCHET_WORKER_SERVICE_NAME
status=$?
set -e

if [[ $status -eq 0 ]]; then
    echo "✅ Service became stable."
elif [[ $status -eq 124 ]]; then
  echo "⏰ Timed out waiting for service to become stable."
else
  echo "❌ Waiter failed with exit code ${status}. Fetching logs anyway…"
fi
