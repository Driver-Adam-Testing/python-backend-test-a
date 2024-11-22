#!/usr/bin/env python3
import os

import aws_cdk as cdk

from cdk.development_stack import DevelopmentStack
from cdk.ops_stack import OpsStack
from cdk.production_stack import ProductionStack
from cdk.staging_stack import StagingStack
from cdk.test_in_dev_stack import TestInDevStack

app = cdk.App()

deployment_environment = os.getenv("DEPLOYMENT_ENVIRONMENT")

if deployment_environment == "local":
    DevelopmentStack(
        app,
        "DriverApiStack",
        env=cdk.Environment(
            account=os.getenv("CDK_DEFAULT_ACCOUNT"),
            region=os.getenv("CDK_DEFAULT_REGION"),
        ),
    )
elif deployment_environment == "ops":
    OpsStack(
        app,
        "DriverApiStack",
        env=cdk.Environment(account="058264523856", region="us-east-1"),
    )
elif deployment_environment == "test-in-dev":
    TestInDevStack(
        app,
        "TempTestInDevStack",
        env=cdk.Environment(account="550082761109", region="us-east-1"),
    )
elif deployment_environment == "development":
    DevelopmentStack(
        app,
        "DriverApiStack",
        env=cdk.Environment(account="550082761109", region="us-east-1"),
    )
elif deployment_environment == "staging":
    StagingStack(
        app,
        "DriverApiStack",
        env=cdk.Environment(account="794038236739", region="us-east-1"),
    )
elif deployment_environment == "production":
    ProductionStack(
        app,
        "DriverApiStack",
        env=cdk.Environment(account="896724907114", region="us-east-1"),
    )

app.synth()
