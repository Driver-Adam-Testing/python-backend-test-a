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


class DevelopmentStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        cors_origins = "https://app.dev.driverai.com,https://labs.dev.driverai.com,https://app2.dev.driverai.com,http://localhost:3000,https://app.beta.driverai.com"

        self.backend = Backend(
            self,
            "ApiBackend",
            BackendParams(
                environment="development",
                cors_origins=cors_origins,
                allowed_ips=["98.142.217.111/32"],
                use_legacy_dropzone=True,
            ),
        )
        self.onboarding_lambda = CodeOnboardingLambda(
            self,
            "CodeOnboardingLambda",
            CodeOnboardingLambdaParams(
                environment="development",
                api_url="https://api.dev.driverai.com/api/v1",
                auth0_url="https://auth.dev.driverai.com",
                dropzone_bucket=self.backend.dropzone_bucket,
                use_legacy_dropzone=True,
            ),
        )
        self.document_onboarding_lambda = DocumentOnboardingLambda(
            self,
            "DocumentOnboardingLambda",
            DocumentOnboardingLambdaParams(
                environment="development",
                api_url="https://api.dev.driverai.com/api/v1",
                auth0_url="https://auth.dev.driverai.com",
                dropzone_bucket=self.backend.dropzone_bucket,
                use_legacy_dropzone=True,
            ),
        )
        self.inspector = Inspector(
            self, "Inspector", InspectorParams(environment="development")
        )
