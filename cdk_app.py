#!/usr/bin/env python3
import os

import aws_cdk as cdk

from cdk.backend_stack import BackendStack
from cdk.settings import settings

app = cdk.App()

print("AWS Env " + settings.DEPLOYMENT_ENVIRONMENT + " " + settings.AWS_ACCOUNT + " " + settings.AWS_REGION)
BackendStack(
    app,
    "DriverApiStack",
    env=cdk.Environment(account=settings.AWS_ACCOUNT, region=settings.AWS_REGION),
)

app.synth()


