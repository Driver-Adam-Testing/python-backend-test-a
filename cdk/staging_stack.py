from aws_cdk import Stack, aws_s3
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

        backend = Backend(
            self,
            "ApiBackend",
            BackendParams(
                environment="staging",
                cors_origins="https://app.staging.driverai.com",
                allowed_ips=[],  # All IPs currently allowed
            ),
        )
        dropzone_bucket = aws_s3.Bucket(self, "DropzoneBucket")
        onboarding_lambda = CodeOnboardingLambda(
            self,
            "OnboardingLambda",
            CodeOnboardingLambdaParams(
                environment="staging",
                api_url="https://api.staging.driverai.com/api/v1",
                auth0_url="https://auth.staging.driverai.com",
                dropzone_bucket_name=dropzone_bucket.bucket_name,
            ),
        )
        inspector = Inspector(self, "Inspector", InspectorParams(environment="staging"))
