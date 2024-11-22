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
)
from constructs import Construct


class CodeOnboardingLambdaParams:
    environment: str
    api_url: str
    auth0_url: str
    dropzone_bucket: aws_s3.Bucket
    use_legacy_dropzone: bool

    def __init__(
        self, environment, api_url, auth0_url, dropzone_bucket, use_legacy_dropzone
    ) -> None:
        self.environment = environment
        self.api_url = api_url
        self.auth0_url = auth0_url
        self.dropzone_bucket = dropzone_bucket
        self.use_legacy_dropzone = use_legacy_dropzone


class CodeOnboardingLambda(Construct):
    def __init__(
        self, scope: Construct, id: str, params: CodeOnboardingLambdaParams
    ) -> None:
        super().__init__(scope, id)

        client_id_secret = aws_secretsmanager.Secret(scope, "ClientIdSecret")
        client_secret_secret = aws_secretsmanager.Secret(scope, "ClientSecretSecret")
        lambda_function = aws_lambda_python_alpha.PythonFunction(
            scope,
            "CodeOnboardingLambdaPy",
            entry="content_services/onboarding_event_handler",
            runtime=aws_lambda.Runtime.PYTHON_3_12,
            index="src/main.py",
            environment={
                "ENVIRONMENT": params.environment,
                "LOG_LEVEL": "INFO",
                "CLIENT_ID_SECRET": client_id_secret.secret_name,
                "CLIENT_SECRET_SECRET": client_secret_secret.secret_name,
                "API_URL": params.api_url,
                "AUTH0_URL": params.auth0_url,
                "AWS_S3_CODE_BUCKET_SUFFIX": "codebase-dropzone",
                "USE_LEGACY_DROPZONE": str(params.use_legacy_dropzone),
            },
            bundling=aws_lambda_python_alpha.BundlingOptions(
                asset_excludes=[".venv", ".env", "tests/", ".pytest*"]
            ),
            timeout=Duration.seconds(15),
        )
        client_id_secret.grant_read(lambda_function)
        client_secret_secret.grant_read(lambda_function)
        params.dropzone_bucket.grant_read(lambda_function)

        sns_topic = aws_sns.Topic(scope, "CodeOnboardingTopic")
        lambda_function.add_event_source(
            aws_lambda_event_sources.SnsEventSource(sns_topic)
        )
        params.dropzone_bucket.add_event_notification(
            aws_s3.EventType.OBJECT_TAGGING_PUT,
            aws_s3_notifications.SnsDestination(sns_topic),
            aws_s3.NotificationKeyFilter(prefix="codebases/"),
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
        legacy_dropzone_bucket.add_event_notification(
            aws_s3.EventType.OBJECT_TAGGING_PUT,
            aws_s3_notifications.SnsDestination(sns_topic),
            aws_s3.NotificationKeyFilter(prefix="codebases/"),
        )
        legacy_dropzone_bucket.grant_read(lambda_function)
