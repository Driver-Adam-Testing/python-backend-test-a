from aws_cdk import Stack
from constructs import Construct

from cdk.constructs.backend import Backend, BackendParams
from cdk.constructs.code_onboarding_lambda import (
    CodeOnboardingLambda,
    CodeOnboardingLambdaParams,
)
from cdk.constructs.document_onboarding_lambda import (
    DocumentOnboardingLambda,
    DocumentOnboardingLambdaParams,
)
from cdk.constructs.inspector import Inspector, InspectorParams
from cdk.constructs.metrics_lambda import MetricsLambda, MetricsLambdaParams


class ProductionStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs: any) -> None:
        super().__init__(scope, construct_id, **kwargs)

        cors_origins = "https://app.driverai.com"

        self.metrics_lambda = MetricsLambda(
            self,
            "MetricsLambda",
            MetricsLambdaParams(
                environment="production",
                cloudwatch_alarm_arn="arn:aws:sns:us-east-1:896724907114:CloudwatchAlarms",
            ),
        )
        self.backend = Backend(
            self,
            "ApiBackend",
            BackendParams(
                environment="production",
                cors_origins=cors_origins,
                allowed_ips=[],  # All IPs currently allowed
                use_legacy_dropzone=True,
                metrics_bus=self.metrics_lambda.metrics_bus,
            ),
        )
        self.onboarding_lambda = CodeOnboardingLambda(
            self,
            "CodeOnboardingLambda",
            CodeOnboardingLambdaParams(
                environment="production",
                api_url="https://api.us1.driverai.com/api/v1",
                auth0_url="https://auth.driverai.com",
                dropzone_bucket=self.backend.dropzone_bucket,
                use_legacy_dropzone=True,
            ),
        )
        self.document_onboarding_lambda = DocumentOnboardingLambda(
            self,
            "DocumentOnboardingLambda",
            DocumentOnboardingLambdaParams(
                environment="production",
                api_url="https://api.us1.driverai.com/api/v1",
                auth0_url="https://auth.driverai.com",
                dropzone_bucket=self.backend.dropzone_bucket,
                use_legacy_dropzone=True,
            ),
        )
        self.inspector = Inspector(
            self, "Inspector", InspectorParams(environment="production")
        )
