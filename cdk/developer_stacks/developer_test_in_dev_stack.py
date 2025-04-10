import os

from aws_cdk import RemovalPolicy, Stack, aws_s3
from constructs import Construct

# from cdk.constructs.dev.document_onboarding_lambda import (
#     DocumentOnboardingLambda,
#     DocumentOnboardingLambdaParams,
# )
from cdk.developer_constructs.dev_stack_code_onboarding_lambda import (
    DevStackCodeOnboardingLambda,
    DevStackCodeOnboardingLambdaParams,
)


# This stack is intended to be used to manually deploy *additional* infrastructure
# next to resources in dev for testing. It may or may not continue to be useful,
# but the resources below can be replaced with just the additional pieces required.
# Assume it will be deleted after use.
class DeveloperTestInDevStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs: any) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create the S3 bucket
        self.eric_codebase_dropzone_bucket = aws_s3.Bucket(
            self,
            "EricCodebaseDropzone",
            bucket_name="eric-codebase-dropzone",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            block_public_access=aws_s3.BlockPublicAccess.BLOCK_ALL,
            encryption=aws_s3.BucketEncryption.S3_MANAGED,
            # enforce_ssl=True,
            versioned=True,
            cors=[
                aws_s3.CorsRule(
                    allowed_methods=[
                        aws_s3.HttpMethods.PUT,
                        aws_s3.HttpMethods.POST,
                        aws_s3.HttpMethods.GET,
                    ],
                    allowed_origins=[
                        "http://localhost:3000",
                        "http://localhost:4000",
                        os.getenv("BACKEND_CORS_ORIGINS"),
                    ],
                    allowed_headers=["*"],
                    exposed_headers=[
                        "x-amz-server-side-encryption",
                        "x-amz-request-id",
                        "x-amz-id-2",
                    ],
                )
            ],
        )

        self.onboarding_lambda = DevStackCodeOnboardingLambda(
            self,
            "EricCodeOnboardingLambda",
            DevStackCodeOnboardingLambdaParams(
                environment="cloud-local",
                api_url=os.getenv("AUTH0_AUDIENCE"),
                auth0_url="https://auth.dev.driverai.com",
                dropzone_bucket=self.eric_codebase_dropzone_bucket,
                use_legacy_dropzone=True,
                client_id=os.getenv("AUTH0_CLIENT_ID"),
                client_secret=os.getenv("AUTH0_CLIENT_SECRET"),
            ),
        )

        # need to create a bucket
        # self.metrics_lambda = MetricsLambda(
        #     self,
        #     "MetricsLambda",
        #     MetricsLambdaParams(
        #         environment=os.getenv("ENVIRONMENT", "local"),
        #         database_url=os.getenv("DATABASE_URL"),
        #     ),
        # )

        # self.document_onboarding_lambda = DocumentOnboardingLambda(
        #     self,
        #     "DocumentOnboardingLambda",
        #     DocumentOnboardingLambdaParams(
        #         environment="development",
        #         api_url="https://driverai.ngrok.io/api/v1",
        #         auth0_url="https://auth.dev.driverai.com",
        #         dropzone_bucket=self.eric_codebase_dropzone_bucket,
        #         use_legacy_dropzone=True,
        #         event_type=aws_s3.EventType.OBJECT_CREATED,
        #         ignore_tags=True,
        #     ),
        # )
