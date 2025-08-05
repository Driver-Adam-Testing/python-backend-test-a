from aws_cdk import Stack
from constructs import Construct

from cdk.constructs.asset_onboarding_lambda import (
    AssetOnboardingLambda,
    AssetOnboardingLambdaParams,
)
from cdk.constructs.backend import Backend, BackendParams
from cdk.constructs.inspector import Inspector, InspectorParams
from cdk.constructs.metrics_lambda import MetricsLambda, MetricsLambdaParams


class PMSStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs: any) -> None:
        super().__init__(scope, construct_id, **kwargs)

        cors_origins = "https://app.pms.driverai.com"

        self.metrics_lambda = MetricsLambda(
            self,
            "MetricsLambda",
            MetricsLambdaParams(
                environment="pms",
                cloudwatch_alarm_arn="arn:aws:sns:us-east-1:537622164442:CloudwatchAlarms",
            ),
        )
        self.backend = Backend(
            self,
            "ApiBackend",
            BackendParams(
                environment="pms",
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
                environment="pms",
                api_url="https://api.pms.driverai.com/studio/v1",
                auth0_url="https://auth.pms.driverai.com",
                auth0_audience="https://api.pms.driverai.com/api/v1",
                dropzone_bucket=self.backend.dropzone_bucket,
                use_legacy_dropzone=True,
            ),
        )
        self.inspector = Inspector(
            self, "Inspector", InspectorParams(environment="pms")
        )
