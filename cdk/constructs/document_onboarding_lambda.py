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


class DocumentOnboardingLambdaParams:
    environment: str
    api_url: str
    auth0_url: str
    use_legacy_dropzone: bool
    dropzone_bucket: aws_s3.Bucket
    s3_endpoint_url: str | None

    def __init__(
        self,
        environment,
        api_url,
        auth0_url,
        use_legacy_dropzone,
        dropzone_bucket,
        s3_endpoint_url=None,
    ):
        self.environment = environment
        self.api_url = api_url
        self.auth0_url = auth0_url
        self.use_legacy_dropzone = use_legacy_dropzone
        self.dropzone_bucket = dropzone_bucket
        self.s3_endpoint_url = s3_endpoint_url


class DocumentOnboardingLambda(Construct):
    def __init__(
        self, scope: Construct, id: str, params: DocumentOnboardingLambdaParams
    ):
        super().__init__(scope, id)

        client_id_secret = aws_secretsmanager.Secret(scope, "DocLambdaClientIdSecret")
        client_secret_secret = aws_secretsmanager.Secret(
            scope, "DocLambdaClientSecretSecret"
        )
        lambda_function = aws_lambda_python_alpha.PythonFunction(
            scope,
            "DocumentOnboardingLambdaPy",
            entry="content_services/document_upload_event_handler",
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
                "AWS_S3_ENDPOINT_URL": params.s3_endpoint_url
                if params.s3_endpoint_url
                else "",
                "DROPZONE_BUCKET_NAME": params.dropzone_bucket.bucket_name,
                "USE_LEGACY_DROPZONE": "True"
                if params.use_legacy_dropzone
                else "False",
            },
            bundling=aws_lambda_python_alpha.BundlingOptions(
                asset_excludes=[".venv", ".env", "tests/", ".pytest*"]
            ),
            timeout=Duration.seconds(15),
        )
        client_id_secret.grant_read(lambda_function)
        client_secret_secret.grant_read(lambda_function)
        params.dropzone_bucket.grant_read(lambda_function)

        sns_topic = aws_sns.Topic(scope, "DocumentOnboardingTopic")
        lambda_function.add_event_source(
            aws_lambda_event_sources.SnsEventSource(sns_topic)
        )
        params.dropzone_bucket.add_event_notification(
            aws_s3.EventType.OBJECT_TAGGING_PUT,
            aws_s3_notifications.SnsDestination(sns_topic),
            aws_s3.NotificationKeyFilter(prefix="documents/"),
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
            "LegacyDropzoneBucketDocOnboarding",
            bucket_name=f"{params.environment}-codebase-dropzone",
        )
        legacy_dropzone_bucket.add_event_notification(
            aws_s3.EventType.OBJECT_TAGGING_PUT,
            aws_s3_notifications.SnsDestination(sns_topic),
            aws_s3.NotificationKeyFilter(prefix="documents/"),
        )
        legacy_dropzone_bucket.grant_read(lambda_function)
