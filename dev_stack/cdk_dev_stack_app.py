#!/usr/bin/env python3
import json
import os

import aws_cdk as cdk

from cdk.developer_stacks.developer_test_in_dev_stack import DeveloperTestInDevStack

app = cdk.App()

os.environ["DEVELOPER_NAME"] = "Eric"
deployment_environment = os.getenv("DEPLOYMENT_ENVIRONMENT")
developer_stack_name = os.getenv("DEVELOPER_NAME")


with open(f"./state/out/cdk-stack-config.json", "r") as f:
    cdk_stack_config = json.load(f)

print(cdk_stack_config)

for k,v in cdk_stack_config["env"].items():
    print(f"{k}: {v}")
    os.environ[k] = v

DeveloperTestInDevStack(
    app,
    f"{developer_stack_name}TempTestInDevStack",
    env=cdk.Environment(account="550082761109", region="us-east-1"),
)
app.synth()
