from dataclasses import dataclass

from aws_cdk import (
    Duration,
    aws_cloudwatch,
    aws_cloudwatch_actions,
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
            },
            bundling=aws_lambda_python_alpha.BundlingOptions(
                asset_excludes=[".venv", ".env", "tests/", ".pytest*"]
            ),
            timeout=Duration.seconds(15),
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

        # Lambda Error Rate Alarm
        alarm_topic_arn = aws_ssm.StringParameter.value_for_string_parameter(
            self, '/infrastructure/alarms/topic-arn'
        )
        alarm_topic = aws_sns.Topic.from_topic_arn(
            self, 'InfrastructureAlarmsTopic', alarm_topic_arn
        )
        alarm_action = aws_cloudwatch_actions.SnsAction(alarm_topic)

        error_rate_alarm = aws_cloudwatch.Alarm(
            self,
            "AssetOnboardingLambdaErrorAlarm",
            alarm_description=f"[{params.environment}] Asset Onboarding Lambda errors > 5 in 5 minutes",
            metric=lambda_function.metric_errors(
                statistic="Sum",
                period=Duration.minutes(5),
            ),
            threshold=5,
            evaluation_periods=1,
            comparison_operator=aws_cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
            treat_missing_data=aws_cloudwatch.TreatMissingData.NOT_BREACHING,
        )
        error_rate_alarm.add_alarm_action(alarm_action)
