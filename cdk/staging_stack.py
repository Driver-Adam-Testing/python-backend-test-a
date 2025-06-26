from aws_cdk import Stack
from constructs import Construct

from cdk.constructs.asset_onboarding_lambda import (
    AssetOnboardingLambda,
    AssetOnboardingLambdaParams,
)
from cdk.constructs.backend import Backend, BackendParams
from cdk.constructs.inspector import Inspector, InspectorParams
from cdk.constructs.metrics_lambda import MetricsLambda, MetricsLambdaParams


class StagingStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs: any) -> None:
        super().__init__(scope, construct_id, **kwargs)

        cors_origins = "https://app.staging.driverai.com"

        self.metrics_lambda = MetricsLambda(
            self,
            "MetricsLambda",
            MetricsLambdaParams(
                environment="staging",
                cloudwatch_alarm_arn="arn:aws:sns:us-east-1:794038236739:CloudwatchAlarms.fifo",
            ),
        )
        self.backend = Backend(
            self,
            "ApiBackend",
            BackendParams(
                environment="staging",
                cors_origins=cors_origins,
                allowed_ips=[],  # All IPs currently allowed
                use_legacy_dropzone=True,
                metrics_bus=self.metrics_lambda.metrics_bus,
            ),
        )

        self.onboarding_lambda = AssetOnboardingLambda(
            self,
            "AssetOnboardingLambda",
            AssetOnboardingLambdaParams(
                environment="staging",
                api_url="https://api.staging.driverai.com/studio/v1",
                auth0_url="https://auth.staging.driverai.com",
                auth0_audience="https://api.staging.driverai.com/api/v1",
                dropzone_bucket=self.backend.dropzone_bucket,
                use_legacy_dropzone=True,
            ),
        )
        self.inspector = Inspector(
            self, "Inspector", InspectorParams(environment="staging")
        )
