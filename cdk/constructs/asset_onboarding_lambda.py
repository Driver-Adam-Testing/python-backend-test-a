from dataclasses import dataclass

from aws_cdk import (
    Duration,
    aws_ec2,
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
from cdk.settings import settings


@dataclass
class AssetOnboardingLambdaParams:
    environment: str
    api_url: str
    auth0_url: str
    auth0_audience: str
    dropzone_bucket: aws_s3.Bucket
    use_legacy_dropzone: bool
    vpc: aws_ec2.IVpc
    is_private_deploy: bool


class AssetOnboardingLambda(Construct):
    def __init__(
        self, scope: Construct, id: str, params: AssetOnboardingLambdaParams
    ) -> None:
        super().__init__(scope, id)

        deployment_secrets = aws_secretsmanager.Secret.from_secret_name_v2(
            self, "deployment_secrets", secret_name=settings.SECRECTS_NAME
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
                "CLIENT_ID_SECRET": settings.ONBOARDING_LAMDBA_CLIENT_ID,
                "CLIENT_SECRET_SECRET": deployment_secrets.secret_name,
                "API_URL": params.api_url,
                "AUTH0_AUDIENCE": params.auth0_audience,
                "AUTH0_URL": params.auth0_url,
                "AWS_S3_CODE_BUCKET_SUFFIX": "codebase-dropzone",
                "USE_LEGACY_DROPZONE": str(params.use_legacy_dropzone),
                "SENTRY_DSN": settings.SENTRY_DSN,
                "IS_PRIVATE_DEPLOY": str(params.is_private_deploy)
            },
            bundling=aws_lambda_python_alpha.BundlingOptions(
                asset_excludes=[".venv", ".env", "tests/", ".pytest*"]
            ),
            timeout=Duration.seconds(15),
            vpc=params.vpc,
            vpc_subnets=aws_ec2.SubnetSelection(
                subnet_type=aws_ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
        )
        deployment_secrets.grant_read(lambda_function)
       
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
        params.dropzone_bucket.add_event_notification(
            aws_s3.EventType.OBJECT_TAGGING_PUT,
            aws_s3_notifications.SnsDestination(sns_topic),
            aws_s3.NotificationKeyFilter(prefix="assets/"),
        )
        params.dropzone_bucket.grant_read(lambda_function)
