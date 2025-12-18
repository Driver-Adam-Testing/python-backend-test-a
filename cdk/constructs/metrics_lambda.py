import os

from aws_cdk import (
    Duration,
    aws_cloudwatch,
    aws_cloudwatch_actions,
    aws_ec2,
    aws_events,
    aws_lambda,
    aws_lambda_python_alpha,
    aws_secretsmanager,
    aws_sns,
    aws_sqs,
    aws_ssm,
)
from aws_cdk import (
    aws_events_targets as targets,
)
from constructs import Construct


class MetricsLambdaParams:
    environment: str

    def __init__(
        self,
        environment: str,
        database_url: str | None = None,
        is_private_deploy: bool = False,
    ) -> None:
        self.environment = environment
        self.database_url = database_url
        self.is_private_deploy = is_private_deploy


class MetricsLambda(Construct):
    def __init__(self, scope: Construct, id: str, params: MetricsLambdaParams) -> None:
        super().__init__(scope, id)

        database_url_secret = aws_secretsmanager.Secret(self, "MetricsLambdaDBSecret")
        vpc_id = aws_ssm.StringParameter.value_from_lookup(
            scope, parameter_name="/baseline/infra/v2/vpc/id"
        )
        vpc = aws_ec2.Vpc.from_lookup(self, id="BaselineVPC_DRV_24", vpc_id=vpc_id)
        driver_db_path = os.path.abspath("driver_db")
        alarm_topic_arn = aws_ssm.StringParameter.value_for_string_parameter(self, '/infrastructure/alarms/topic-arn')
        alarm_topic = aws_sns.Topic.from_topic_arn(self, 'InfrastructureAlarmsTopic', alarm_topic_arn)

        self.lambda_function = aws_lambda_python_alpha.PythonFunction(
            scope,
            "MetricsLambdaPy",
            entry="lambdas/metrics_handler",
            runtime=aws_lambda.Runtime.PYTHON_3_12,
            index="src/main.py",
            vpc=vpc,
            vpc_subnets=aws_ec2.SubnetSelection(
                subnet_type=aws_ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
            environment={
                "ENVIRONMENT": params.environment,
                "LOG_LEVEL": "INFO",
                "DATABASE_URL": params.database_url or "",
                "DATABASE_URL_SECRET_NAME": database_url_secret.secret_name,
                "IS_PRIVATE_DEPLOY": "true" if params.is_private_deploy else "false",
            },
            bundling=aws_lambda_python_alpha.BundlingOptions(
                platform="linux/amd64",
                asset_excludes=[".venv", ".env", "tests/", ".pytest*"],
                volumes=[
                    {"containerPath": "/driver_db", "hostPath": driver_db_path},
                ],
            ),
            reserved_concurrent_executions=10,
            timeout=Duration.seconds(60),
        )
        database_url_secret.grant_read(self.lambda_function)

        # Grant permission to read firewall certificate for private deployments
        if params.is_private_deploy:
            firewall_cert_secret = aws_secretsmanager.Secret.from_secret_name_v2(
                self, "FirewallCertSecret", secret_name="/network-firewall/ca-certificate"
            )
            firewall_cert_secret.grant_read(self.lambda_function)

        event_target = targets.LambdaFunction(
            self.lambda_function,
        )
        self.metrics_dlq = aws_sqs.Queue(self, "MetricsDLQ")
        self.metrics_bus = aws_events.EventBus(
            self,
            "MetricsBus",
            event_bus_name="metrics-event-bus",
            dead_letter_queue=self.metrics_dlq,
        )
        self.metrics_rule = aws_events.Rule(
            self,
            "MetricsProcessorRule",
            event_bus=self.metrics_bus,
            targets=[event_target],
            event_pattern=aws_events.EventPattern(source=["metrics.client"]),
        )
        
        self.metric_dlq_alarm = aws_cloudwatch.Alarm(
            self,
            "MetricDLQAlarm",
            alarm_description=f"[{params.environment}] Metrics Undelivered In DLQ",
            metric=self.metrics_dlq.metric_approximate_number_of_messages_visible(),
            threshold=1,
            evaluation_periods=1,
            comparison_operator=aws_cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
            treat_missing_data=aws_cloudwatch.TreatMissingData.IGNORE,
        )
        self.metric_message_age_alarm = aws_cloudwatch.Alarm(
            self,
            "MetricMessageAgeAlarm",
            alarm_description=f"[{params.environment}] Metrics DLQ Message Age > 2 hours Alarm",
            metric=self.metrics_dlq.metric_approximate_age_of_oldest_message(),
            threshold=7200,  # Seconds, = 2 hours
            evaluation_periods=1,
            comparison_operator=aws_cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
            treat_missing_data=aws_cloudwatch.TreatMissingData.IGNORE,
        )
        self.lambda_error_rate_alarm = aws_cloudwatch.Alarm(
            self,
            "MetricLambdaErrorAlarm",
            alarm_description=f"[{params.environment}] Metrics Lambda Errors > 5 over last 5 minutes",
            metric=self.lambda_function.metric_errors(),
            threshold=5,
            evaluation_periods=1,
            comparison_operator=aws_cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
            treat_missing_data=aws_cloudwatch.TreatMissingData.IGNORE,
        )
