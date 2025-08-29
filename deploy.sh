#!/bin/bash

#docker section
# If there's a setEnv.sh script in the / directory, run it before starting
echo "Checking for setEnv script"
if [ -f "../setEnv.sh" ] ; then
    echo "Copy script setEnv.sh"
    cp ../setEnv.sh .
else
    echo "There is no script setEnv.sh"
fi

aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT.dkr.ecr.$AWS_REGION.amazonaws.com
docker build --build-arg GIT_COMMIT=$(git rev-parse HEAD) --build-arg GIT_BRANCH=$(git rev-parse --abbrev-ref HEAD) -t $AWS_ACCOUNT.dkr.ecr.$AWS_REGION.amazonaws.com/python-backend:latest .
docker push $AWS_ACCOUNT.dkr.ecr.$AWS_REGION.amazonaws.com/python-backend:latest

npm install -g aws-cdk@latest
pip install aws-cdk-lib
pip install aws-cdk.aws-lambda-python-alpha
npx cdk deploy --require-approval never