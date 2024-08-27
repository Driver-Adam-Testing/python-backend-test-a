from aws_cdk import (
    Stack,
)
from constructs import Construct

from cdk.constructs.backend import Backend, BackendParams
from cdk.constructs.code_onboarding_lambda import (
    CodeOnboardingLambda,
    CodeOnboardingLambdaParams,
)
from cdk.constructs.inspector import Inspector, InspectorParams


class ProductionStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        backend = Backend(
            self,
            "ApiBackend",
            BackendParams(
                environment="production",
                cors_origins="https://app.driverai.com",
                allowed_ips=[],  # All IPs currently allowed
            ),
        )
        onboarding_lambda = CodeOnboardingLambda(
            self,
            "OnboardingLambda",
            CodeOnboardingLambdaParams(
                environment="production",
                api_url="https://api.us1.driverai.com/api/v1",
                auth0_url="https://auth.driverai.com",
                dropzone_bucket_name="production-codebase-dropzone",
            ),
        )
        inspector = Inspector(
            self, "Inspector", InspectorParams(environment="production")
        )
