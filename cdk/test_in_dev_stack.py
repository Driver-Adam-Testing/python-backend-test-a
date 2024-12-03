import os

from aws_cdk import Stack
from constructs import Construct

from cdk.constructs.metrics_lambda import MetricsLambda, MetricsLambdaParams


# This stack is intended to be used to manually deploy *additional* infrastructure
# next to resources in dev for testing. It may or may not continue to be useful,
# but the resources below can be replaced with just the additional pieces required.
# Assume it will be deleted after use.
class TestInDevStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs: any) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.metrics_lambda = MetricsLambda(
            self,
            "MetricsLambda",
            MetricsLambdaParams(
                environment=os.getenv("ENVIRONMENT", "development"),
                database_url=os.getenv("DATABASE_URL"),
            ),
        )
