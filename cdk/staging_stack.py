from aws_cdk import Stack
from constructs import Construct

from cdk.constructs.backend import Backend, BackendParams
from cdk.constructs.code_onboarding_lambda import (
    CodeOnboardingLambda,
    CodeOnboardingLambdaParams,
)
from cdk.constructs.inspector import Inspector, InspectorParams


class StagingStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        cors_origins = "https://app.staging.driverai.com"

        self.backend = Backend(
            self,
            "ApiBackend",
            BackendParams(
                environment="staging",
                cors_origins=cors_origins,
                allowed_ips=[],  # All IPs currently allowed
                use_legacy_dropzone=False,
            ),
        )

        self.onboarding_lambda = CodeOnboardingLambda(
            self,
            "CodeOnboardingLambda",
            CodeOnboardingLambdaParams(
                environment="staging",
                api_url="https://api.staging.driverai.com/api/v1",
                auth0_url="https://auth.staging.driverai.com",
                dropzone_bucket=self.backend.dropzone_bucket,
                use_legacy_dropzone=False,
            ),
        )
        self.inspector = Inspector(
            self, "Inspector", InspectorParams(environment="staging")
        )
