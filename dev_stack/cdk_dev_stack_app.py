#!/usr/bin/env python3
import json
import os

import aws_cdk as cdk

from cdk.dev_stack import DevStack, DevStackParams

app = cdk.App()

if "DEV_NAME" not in os.environ:
    raise ValueError("DEV_NAME must be set in the environment")

if "DEPLOYMENT_ENVIRONMENT" not in os.environ:
    raise ValueError("DEPLOYMENT_ENVIRONMENT must be set in the environment")

if "DATABASE_URL" not in os.environ:
    raise ValueError("DATABASE_URL must be set in the environment")

dev_name = os.environ["DEV_NAME"].replace("-", "").replace(" ", "").strip()
dev_stack_name = f"{dev_name}TempTestInDevStack"


print(f"Deploying {dev_stack_name} CDK stack")

with open("./state/out/cdk-stack-config.json") as f:
    cdk_stack_config = json.load(f)

print(cdk_stack_config)

for k, v in cdk_stack_config["env"].items():
    # print(f"{k}: {v}")
    os.environ[k] = v

DevStack(
    app,
    dev_stack_name,
    params=DevStackParams(
        cdk_prefix=dev_name,
        environment=os.environ["DEPLOYMENT_ENVIRONMENT"],
        database_url=os.environ["DATABASE_URL"],
    ),
    env=cdk.Environment(account="550082761109", region="us-east-1"),
)
app.synth()
