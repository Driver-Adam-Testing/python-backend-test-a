from dataclasses import dataclass

from aws_cdk import (
    Duration,
    aws_iam,
    aws_lambda,
    aws_lambda_event_sources,
    aws_lambda_python_alpha,
    aws_s3,
    aws_s3_notifications,
    aws_secretsmanager,
    aws_sns,
    aws_ssm,
)
from constructs import Construct


@dataclass
class AssetOnboardingLambdaParams:
    environment: str
    api_url: str
    auth0_url: str
    auth0_audience: str
    dropzone_bucket: aws_s3.Bucket
    use_legacy_dropzone: bool


class AssetOnboardingLambda(Construct):
    def __init__(
        self, scope: Construct, id: str, params: AssetOnboardingLambdaParams
    ) -> None:
        super().__init__(scope, id)

        client_id_secret = aws_secretsmanager.Secret(scope, "ClientIdSecret")
        client_secret_secret = aws_secretsmanager.Secret(scope, "ClientSecretSecret")

        sentry_secret_name = aws_ssm.StringParameter.value_from_lookup(
            scope,
            parameter_name="/baseline/infra/v2/pythonBackend/sentryCredentialName",
        )
        sentry_secret = aws_secretsmanager.Secret.from_secret_name_v2(
            scope, "SentrySecret", secret_name=sentry_secret_name
        )
        lambda_function = aws_lambda_python_alpha.PythonFunction(
            scope,
            "AssetOnboardingLambdaPy",
            entry="content_services/onboarding_event_handler",
            runtime=aws_lambda.Runtime.PYTHON_3_12,
            index="src/main.py",
            environment={
                "ENVIRONMENT": params.environment,
                "LOG_LEVEL": "INFO",
                "CLIENT_ID_SECRET": client_id_secret.secret_name,
                "CLIENT_SECRET_SECRET": client_secret_secret.secret_name,
                "API_URL": params.api_url,
                "AUTH0_AUDIENCE": params.auth0_audience,
                "AUTH0_URL": params.auth0_url,
                "AWS_S3_CODE_BUCKET_SUFFIX": "codebase-dropzone",
                "USE_LEGACY_DROPZONE": str(params.use_legacy_dropzone),
                "SENTRY_DSN": sentry_secret.secret_value_from_json("SENTRY_DSN").unsafe_unwrap(),
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
            bucket_name=f"{params.environment}-codebase-dropzone",
        )
        #TODO: Guard Duty tags object in the droppzone bucket but since its not enabled in pms, we use OBJECT_CREATED_PUT
        sns_event_type = aws_s3.EventType.OBJECT_TAGGING_PUT if params.environment != 'pms' else aws_s3.EventType.OBJECT_CREATED_PUT
        legacy_dropzone_bucket.add_event_notification(
            sns_event_type,
            aws_s3_notifications.SnsDestination(sns_topic),
            aws_s3.NotificationKeyFilter(prefix="assets/"),
        )
        legacy_dropzone_bucket.grant_read(lambda_function)
