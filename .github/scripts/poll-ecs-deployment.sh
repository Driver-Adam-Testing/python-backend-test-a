#!/bin/bash

set -euo pipefail

CLUSTER_NAME="$1"
SERVICE_NAME="$2"
TIMEOUT_SECONDS="${3:-600}"
POLL_INTERVAL="${4:-10}"
LOCAL_PROFILE="$5" 

echo "⏳ Monitoring ECS service '$SERVICE_NAME' in cluster '$CLUSTER_NAME' for successful deployment..."
echo "⏱️  Timeout: $TIMEOUT_SECONDS seconds"

start_time=$(date +%s)

while true; do
  DEPLOYMENTS_JSON=$(aws ecs describe-services \
    --cluster "$CLUSTER_NAME" \
    --services "$SERVICE_NAME" \
    --query "services[0].deployments" \
    --output json $LOCAL_PROFILE)

  PRIMARY_STATUS=$(echo "$DEPLOYMENTS_JSON")

  # echo $PRIMARY_STATUS

  if [[ -z "$PRIMARY_STATUS" ]]; then
    echo "❌ No PRIMARY deployment found. The service may have rolled back."
    exit 1
  fi

  # if echo "$PRIMARY_STATUS" | grep -q '"rolloutState": "COMPLETED"'; then
  #   echo "✅ Deployment completed successfully!"
  #   exit 0
  # fi

  if echo "$PRIMARY_STATUS" | grep -q '"rolloutState": "FAILED"'; then
    echo "❌ Deployment failed! ECS reported a rollout failure."
    exit 1
  fi

  # Step 2: Check for DEPROVISIONING tasks
  TASK_ARNS=$(aws ecs list-tasks \
    --cluster "$CLUSTER_NAME" \
    --service-name "$SERVICE_NAME" \
    --desired-status 
    --query "taskArns" \
    --output text $LOCAL_PROFILE)
  
  echo $TASK_ARNS

  if [[ -n "$TASK_ARNS" ]]; then
    TASK_JSON=$(aws ecs describe-tasks \
      --cluster "$CLUSTER_NAME" \
      --tasks $TASK_ARNS \
      --query "tasks[*].{TaskArn:taskArn,Status:lastStatus}" \
      --output json $LOCAL_PROFILE)

    # echo $TASK_JSON

    if echo "$TASK_JSON" | grep -q '"Status": "DEPROVISIONING"'; then
      echo "❌ One or more tasks entered DEPROVISIONING status."
      echo "🔍 Task details:"
      echo "$TASK_JSON"
      exit 1
    fi
  fi

  current_time=$(date +%s)
  elapsed=$((current_time - start_time))

  if [ "$elapsed" -ge "$TIMEOUT_SECONDS" ]; then
    echo "⏱️  Timed out after $TIMEOUT_SECONDS seconds waiting for deployment to complete."
    exit 1
  fi

  echo "🔄 Still waiting... elapsed: ${elapsed}s"
  sleep "$POLL_INTERVAL"
done