#!/usr/bin/env python3
import os

import aws_cdk as cdk

from cdk.backend_stack import BackendStack
from cdk.settings import Settings

app = cdk.App()

BackendStack(
    app,
    "DriverApiStack",
    env=cdk.Environment(account=Settings.AWS_ACCOUNT, region=Settings.AWS_REGION),
)

app.synth()


