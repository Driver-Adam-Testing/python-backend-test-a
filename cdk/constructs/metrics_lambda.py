import os

from aws_cdk import (
    Duration,
    aws_cloudwatch,
    aws_cloudwatch_actions,
    aws_events,
    aws_lambda,
    aws_lambda_python_alpha,
    aws_sns,
    aws_sqs,
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
        database_url: str,
    ) -> None:
        self.environment = environment
        self.database_url = database_url


class MetricsLambda(Construct):
    def __init__(self, scope: Construct, id: str, params: MetricsLambdaParams) -> None:
        super().__init__(scope, id)

        driver_db_path = os.path.abspath("driver_db")
        self.lambda_function = aws_lambda_python_alpha.PythonFunction(
            scope,
            "MetricsLambdaPy",
            entry="lambdas/metrics_handler",
            runtime=aws_lambda.Runtime.PYTHON_3_12,
            index="src/main.py",
            environment={
                "ENVIRONMENT": params.environment,
                "LOG_LEVEL": "INFO",
                "DATABASE_URL": params.database_url,
            },
            bundling=aws_lambda_python_alpha.BundlingOptions(
                platform="linux/amd64",
                asset_excludes=[".venv", ".env", "tests/", ".pytest*"],
                volumes=[{"containerPath": "/driver_db", "hostPath": driver_db_path}],
            ),
            reserved_concurrent_executions=10,
            timeout=Duration.seconds(60),
        )
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

        if params.environment in ["development", "staging", "production"]:
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
            notification_topic_arn = None
            if params.environment == "development":
                notification_topic_arn = (
                    "arn:aws:sns:us-east-1:550082761109:ErrorSupport"
                )
            elif params.environment == "staging":
                notification_topic_arn = (
                    "arn:aws:sns:us-east-1:794038236739:CloudwatchAlarms.fifo"
                )
            elif params.environment == "production":
                notification_topic_arn = (
                    "arn:aws:sns:us-east-1:896724907114:CloudwatchAlarms"
                )
            else:
                raise LookupError(
                    f"Unable to locate notification topic ARN for {params.environment}"
                )

            self.metric_dlq_alarm.add_alarm_action(
                aws_cloudwatch_actions.SnsAction(
                    aws_sns.Topic.from_topic_arn(
                        id="NotifySupportTopic",
                        topic_arn=notification_topic_arn,
                        scope=self,
                    )
                )
            )
        else:
            print(
                f"*** NO CW DLQ ALARM CONFIGURED FOR MetricAlarm in {params.environment} ***"
            )
