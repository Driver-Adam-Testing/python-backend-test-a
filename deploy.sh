#!/usr/bin/env bash
npm install -g aws-cdk@latest
pip install aws-cdk-lib
pip install aws-cdk.aws-lambda-python-alpha
npx cdk deploy --require-approval never