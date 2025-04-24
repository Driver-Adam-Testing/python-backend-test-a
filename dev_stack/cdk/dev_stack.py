import os
from dataclasses import dataclass

from aws_cdk import RemovalPolicy, Stack, aws_s3
from constructs import Construct

from cdk.constructs.asset_onboarding_lambda import (
    AssetOnboardingLambda,
    AssetOnboardingLambdaParams,
)
from cdk.constructs.metrics_lambda import (
    MetricsLambda,
    MetricsLambdaParams,
)


@dataclass
class DevStackParams:
    environment: str
    cdk_prefix: str
    database_url: str


# This stack is intended to be used to manually deploy *additional* infrastructure
# next to resources in dev for testing. It may or may not continue to be useful,
# but the resources below can be replaced with just the additional pieces required.
# Assume it will be deleted after use.
class DevStack(Stack):
    def __init__(
        self, scope: Construct, construct_id: str, params: DevStackParams, **kwargs: any
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        prefix = params.cdk_prefix.replace("-", "").replace(" ", "").strip()
        env = params.environment
        # Create the S3 bucket
        self.asset_dropzone_bucket = aws_s3.Bucket(
            self,
            "AssetDropzone",
            bucket_name=f"{prefix.lower()}-asset-dropzone",
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
                        os.getenv("CORS_ORIGINS"),
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

        self.onboarding_lambda = AssetOnboardingLambda(
            self,
            "AssetOnboardingLambda",
            AssetOnboardingLambdaParams(
                environment=env,
                api_url=os.getenv("API_URL"),
                auth0_url=os.getenv("AUTH0_URL"),
                dropzone_bucket=self.asset_dropzone_bucket,
                use_legacy_dropzone=True,
                cdk_prefix=prefix,
            ),
        )

        self.metrics_lambda = MetricsLambda(
            self,
            "MetricsLambda",
            MetricsLambdaParams(
                environment=env,
                database_url=os.getenv("DATABASE_URL"),
                cdk_prefix=prefix,
            ),
        )
