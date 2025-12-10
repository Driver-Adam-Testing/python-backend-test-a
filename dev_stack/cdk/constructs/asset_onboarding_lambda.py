from dataclasses import dataclass

from aws_cdk import (
    CfnOutput,
    Duration,
    aws_iam,
    aws_lambda,
    aws_lambda_event_sources,
    aws_lambda_python_alpha,
    aws_s3,
    aws_s3_notifications,
    aws_secretsmanager,
    aws_sns,
)
from constructs import Construct


@dataclass
class AssetOnboardingLambdaParams:
    environment: str
    api_url: str
    auth0_url: str
    dropzone_bucket: aws_s3.Bucket
    use_legacy_dropzone: bool
    cdk_prefix: str


class AssetOnboardingLambda(Construct):
    def __init__(
        self, scope: Construct, id: str, params: AssetOnboardingLambdaParams
    ) -> None:
        super().__init__(scope, id)
        # Append DevName
        client_id_secret = aws_secretsmanager.Secret(
            scope, f"{params.cdk_prefix}ClientIdSecret"
        )
        client_secret_secret = aws_secretsmanager.Secret(
            scope, f"{params.cdk_prefix}ClientSecretSecret"
        )
        lambda_function = aws_lambda_python_alpha.PythonFunction(
            scope,
            "AssetOnboardingLambdaPy",
            entry="../content_services/onboarding_event_handler",
            runtime=aws_lambda.Runtime.PYTHON_3_12,
            index="src/main.py",
            environment={
                "ENVIRONMENT": params.environment,
                "LOG_LEVEL": "INFO",
                "CLIENT_ID_SECRET": client_id_secret.secret_name,
                "CLIENT_SECRET_SECRET": client_secret_secret.secret_name,
                "API_URL": params.api_url,
                "AUTH0_URL": params.auth0_url,
                "AWS_S3_CODE_BUCKET_SUFFIX": "asset-dropzone",
                "USE_LEGACY_DROPZONE": str(params.use_legacy_dropzone),
            },
            bundling=aws_lambda_python_alpha.BundlingOptions(
                asset_excludes=[".venv", ".env", "tests/", ".pytest*"]
            ),
            timeout=Duration.seconds(15),
        )
        client_secret_secret.grant_read(lambda_function)
        client_id_secret.grant_read(lambda_function)
        params.dropzone_bucket.grant_read(lambda_function)

        sns_topic = aws_sns.Topic(scope, "CodeOnboardingTopic")
        lambda_function.add_event_source(
            aws_lambda_event_sources.SnsEventSource(sns_topic)
        )

        # TODO: We should find a way to scope down these privileges.
        # Because we need to create arbitrary buckets per org,
        # it's not clear how to do so without breaking existing
        # functionality.
        lambda_function.role.add_managed_policy(
            aws_iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3FullAccess")
        )
        legacy_dropzone_bucket = aws_s3.Bucket.from_bucket_name(
            scope,
            "LegacyDropzoneBucket",
            bucket_name=params.dropzone_bucket.bucket_name,
        )
        legacy_dropzone_bucket.add_event_notification(
            aws_s3.EventType.OBJECT_CREATED_PUT,
            aws_s3_notifications.SnsDestination(sns_topic),
            aws_s3.NotificationKeyFilter(prefix="assets/"),
        )
        legacy_dropzone_bucket.grant_read(lambda_function)

        CfnOutput(
            self,
            f"{params.cdk_prefix}ClientIdSecretNameOutput",
            value=client_id_secret.secret_name,
            export_name=f"{params.cdk_prefix}CodeLambdaClientIdOutput",
        )
        CfnOutput(
            self,
            f"{params.cdk_prefix}ClientSecretSecretNameOutput",
            value=client_secret_secret.secret_name,
            export_name=f"{params.cdk_prefix}CodeLambdaClientSecretOutput",
        )
