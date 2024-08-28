from aws_cdk import Stack, aws_s3
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

        cors_origins = "https://app.driverai.com"

        dropzone_bucket = aws_s3.Bucket(
            self,
            "DropzoneBucket",
            cors=[
                {
                    "allowedMethods": [
                        aws_s3.HttpMethods.PUT,
                        aws_s3.HttpMethods.POST,
                        aws_s3.HttpMethods.GET,
                    ],
                    "allowedOrigins": cors_origins.split(","),
                    "allowedHeaders": ["*"],
                }
            ],
        )
        backend = Backend(
            self,
            "ApiBackend",
            BackendParams(
                environment="production",
                cors_origins=cors_origins,
                allowed_ips=[],  # All IPs currently allowed
                dropzone_bucket_name=dropzone_bucket.bucket_name,
                use_legacy_dropzone=True,
            ),
        )
        onboarding_lambda = CodeOnboardingLambda(
            self,
            "OnboardingLambda",
            CodeOnboardingLambdaParams(
                environment="production",
                api_url="https://api.us1.driverai.com/api/v1",
                auth0_url="https://auth.driverai.com",
                dropzone_bucket_name=dropzone_bucket.bucket_name,
            ),
        )
        inspector = Inspector(
            self, "Inspector", InspectorParams(environment="production")
        )
