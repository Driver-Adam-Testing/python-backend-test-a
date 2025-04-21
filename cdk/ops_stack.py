import os

from aws_cdk import (
    Stack,
)
from constructs import Construct

from cdk.constructs.asset_onboarding_lambda import (
    AssetOnboardingLambda,
    AssetOnboardingLambdaParams,
)
from cdk.constructs.backend import Backend, BackendParams
from cdk.constructs.inspector import Inspector, InspectorParams
from cdk.constructs.metrics_lambda import MetricsLambda, MetricsLambdaParams


class OpsStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs: any) -> None:
        super().__init__(scope, construct_id, **kwargs)
        print(kwargs)
        cors_origins = "https://app.dev.driverai.com,https://labs.dev.driverai.com,https://app2.dev.driverai.com,http://localhost:3000,https://app.beta.driverai.com"

        self.backend = Backend(
            self,
            "ApiBackend",
            BackendParams(
                environment="ops",
                cors_origins=cors_origins,
                allowed_ips=["98.142.217.111/32"],
                use_legacy_dropzone=False,
            ),
        )
        self.onboarding_lambda = AssetOnboardingLambda(
            self,
            "AssetOnboardingLambda",
            AssetOnboardingLambdaParams(
                environment="ops",
                api_url="https://api.ops.driverai.com/api/v1",
                auth0_url="https://auth.dev.driverai.com",
                dropzone_bucket=self.backend.dropzone_bucket,
                use_legacy_dropzone=False,
            ),
        )
        self.inspector = Inspector(
            self, "Inspector", InspectorParams(environment="ops")
        )

        self.metrics_lambda = MetricsLambda(
            self,
            "MetricsLambda",
            MetricsLambdaParams(
                environment=os.getenv("ENVIRONMENT", "ops"),
                database_url=os.getenv("DATABASE_URL"),
            ),
        )
