from aws_cdk import (
    Stack,
)
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


class OpsStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs: any) -> None:
        super().__init__(scope, construct_id, **kwargs)

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
        self.onboarding_lambda = CodeOnboardingLambda(
            self,
            "CodeOnboardingLambda",
            CodeOnboardingLambdaParams(
                environment="ops",
                api_url="https://api.ops.driverai.com/api/v1",
                auth0_url="https://auth.dev.driverai.com",
                dropzone_bucket=self.backend.dropzone_bucket,
                use_legacy_dropzone=False,
            ),
        )
        self.document_onboarding_lambda = DocumentOnboardingLambda(
            self,
            "DocumentOnboardingLambda",
            DocumentOnboardingLambdaParams(
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
