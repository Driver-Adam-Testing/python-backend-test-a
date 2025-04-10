#!/usr/bin/env python3
import os

import aws_cdk as cdk

from cdk.developer_stacks.developer_test_in_dev_stack import DeveloperTestInDevStack

app = cdk.App()

deployment_environment = os.getenv("DEPLOYMENT_ENVIRONMENT")
DeveloperTestInDevStack(
    app,
    "EricTempTestInDevStack",
    env=cdk.Environment(account="550082761109", region="us-east-1"),
)
app.synth()
