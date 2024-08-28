from aws_cdk import (
    Duration,
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
    dropzone_bucket: aws_s3.Bucket

    def __init__(self, environment, api_url, auth0_url, dropzone_bucket):
        self.environment = environment
        self.api_url = api_url
        self.auth0_url = auth0_url
        self.dropzone_bucket = dropzone_bucket


class DocumentOnboardingLambda(Construct):
    def __init__(
        self, scope: Construct, id: str, params: DocumentOnboardingLambdaParams
    ):
        super().__init__(scope, id)

        # dropzone_bucket = aws_s3.Bucket.from_bucket_name(
        #     scope, "dropzone-bucket", params.environment + "-codebase-dropzone"
        # )

        client_id_secret = aws_secretsmanager.Secret(scope, "ClientIdSecret")
        client_secret_secret = aws_secretsmanager.Secret(scope, "ClientSecretSecret")
        lambda_function = aws_lambda_python_alpha.PythonFunction(
            scope,
            "DocumentOnboardingLambdaPy",
            entry="content_services/onboarding_event_handler",
            runtime=aws_lambda.Runtime.PYTHON_3_12,
            index="src/main.py",
            environment={
                "ENVIRONMENT": params.environment,
                "CLIENT_ID_SECRET": client_id_secret.secret_name,
                "CLIENT_SECRET_SECRET": client_secret_secret.secret_name,
                "API_URL": params.api_url,
                "AUTH0_URL": params.auth0_url,
                "AWS_S3_CODE_BUCKET_SUFFIX": "codebase-dropzone",
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
            aws_s3.EventType.OBJECT_CREATED,
            aws_s3_notifications.SnsDestination(sns_topic),
            aws_s3.NotificationKeyFilter(prefix="documents/"),
        )
