from aws_cdk import (
    Duration,
    RemovalPolicy,
    aws_cloudwatch,
    aws_cloudwatch_actions,
    aws_ec2,
    aws_lambda,
    aws_lambda_python_alpha,
    aws_logs,
    aws_secretsmanager,
    aws_sns,
    aws_ssm,
)
from aws_cdk import (
    aws_events as events,
)
from aws_cdk import (
    aws_events_targets as targets,
)
from constructs import Construct


class Auth0EventLambdaParams:
    environment: str

    def __init__(
        self,
        environment: str,
        database_url: str | None = None,
        cloudwatch_alarm_arn: str | None = None,
    ) -> None:
        self.environment = environment
        self.database_url = database_url
        self.cloudwatch_alarm_arn = cloudwatch_alarm_arn


class Auth0EventLambda(Construct):
    def __init__(
        self, scope: Construct, id: str, params: Auth0EventLambdaParams
    ) -> None:
        super().__init__(scope, id)

        auth0_eventbridge_bus_name = aws_ssm.StringParameter.value_from_lookup(
            scope, parameter_name="/baseline/infra/v2/eventbridge/auth0_bus_name"
        )
        event_bus = events.EventBus.from_event_bus_name(
            self,
            "Auth0EventBus",
            event_bus_name=auth0_eventbridge_bus_name,
        )
        vpc_id = aws_ssm.StringParameter.value_from_lookup(
            scope, parameter_name="/baseline/infra/v2/vpc/id"
        )

        vpc = aws_ec2.Vpc.from_lookup(self, id="BaselineVPC_Auth0Events", vpc_id=vpc_id)

        # Create secrets for sensitive data
        modal_secrets = aws_secretsmanager.Secret(self, "Auth0EventLambdaModalSecret")

        # Create  SQS DL queue
        # self.events_dlq = aws_sqs.Queue(
        #     self,
        #     "Auth0EventsDLQ",
        #     queue_name="auth0-events-dlq",
        #     visibility_timeout=Duration.seconds(300),
        #     retention_period=Duration.days(14),
        #     receive_message_wait_time=Duration.seconds(20),
        # )

        # Create Lambda function
        self.lambda_function = aws_lambda_python_alpha.PythonFunction(
            scope,
            "Auth0EventProcessorLambda",
            entry="lambdas/auth0_event_processor",
            runtime=aws_lambda.Runtime.PYTHON_3_12,
            index="src/main.py",
            vpc=vpc,
            vpc_subnets=aws_ec2.SubnetSelection(
                subnet_type=aws_ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
            environment={
                "LOG_LEVEL": "INFO",
                "MODAL_SECRET_NAME": modal_secrets.secret_name,
            },
            bundling=aws_lambda_python_alpha.BundlingOptions(
                platform="linux/amd64",
                poetry_include_hashes=False,
                asset_excludes=[".venv", "tests/", ".pytest*"],
            ),
            reserved_concurrent_executions=10,
            timeout=Duration.seconds(60),
            # dead_letter_queue=self.events_dlq,
            # dead_letter_queue_enabled=True,
            # retry_attempts=2,
        )

        # Grant Lambda permissions to read secrets
        modal_secrets.grant_read(self.lambda_function)

        # Configure CloudWatch Logs with retention
        log_group = aws_logs.LogGroup(
            self,
            "Auth0EventProcessorLogGroup",
            log_group_name=f"/aws/lambda/{self.lambda_function.function_name}",
            retention=aws_logs.RetentionDays.TWO_WEEKS,
            removal_policy=RemovalPolicy.DESTROY,
        )

        # Create EventBridge rule with event pattern
        rule = events.Rule(
            self,
            "Auth0EventRule",
            event_bus=event_bus,
            rule_name="auth0-security-events-rule",
            description="Route specific Auth0 events to Lambda",
            event_pattern=events.EventPattern(
                detail={
                    "data": {
                        "type": [
                            "ss",
                            "s",
                            "sdu",
                            "sapi",
                            "organization_member_added",
                            "organization_member_removed",
                        ]
                    }
                }
            ),
        )

        # Add Lambda as target with DLQ configuration
        rule.add_target(
            targets.LambdaFunction(
                self.lambda_function,
                # dead_letter_queue=self.events_dlq,
                # max_event_age=Duration.hours(2),
                # retry_attempts=2,
            )
        )

        # # Add SQS event source to Lambda
        # self.lambda_function.add_event_source(
        #     aws_lambda_event_sources.SqsEventSource(
        #         self.events_dlq,
        #         batch_size=10,
        #         max_batching_window=Duration.seconds(5),
        #         report_batch_item_failures=True,
        #     )
        # )
        #
        # # Grant Lambda permissions to access SQS
        # self.events_dlq.grant_consume_messages(self.lambda_function)

        # # CloudWatch Alarms
        # self.dlq_depth_alarm = aws_cloudwatch.Alarm(
        #     self,
        #     "Auth0EventsDLQAlarm",
        #     alarm_description=f"[{params.environment}] Auth0 Events Undelivered In DLQ",
        #     metric=self.events_dlq.metric_approximate_number_of_messages_visible(),
        #     threshold=1,
        #     evaluation_periods=1,
        #     comparison_operator=aws_cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
        #     treat_missing_data=aws_cloudwatch.TreatMissingData.IGNORE,
        # )
        #
        # self.dlq_message_age_alarm = aws_cloudwatch.Alarm(
        #     self,
        #     "Auth0EventsDLQMessageAgeAlarm",
        #     alarm_description="Auth0 Events DLQ Message Age > 2 hours",
        #     metric=self.events_dlq.metric_approximate_age_of_oldest_message(),
        #     threshold=7200,
        #     evaluation_periods=1,
        #     comparison_operator=aws_cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
        #     treat_missing_data=aws_cloudwatch.TreatMissingData.IGNORE,
        # )
        #
        self.lambda_error_rate_alarm = aws_cloudwatch.Alarm(
            self,
            "Auth0EventsLambdaErrorAlarm",
            alarm_description=f"[{params.environment}] Auth0 Events Lambda Errors > 5 over last 5 minutes",
            metric=self.lambda_function.metric_errors(),
            threshold=5,
            evaluation_periods=1,
            comparison_operator=aws_cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
            treat_missing_data=aws_cloudwatch.TreatMissingData.IGNORE,
        )

        self.lambda_throttle_alarm = aws_cloudwatch.Alarm(
            self,
            "Auth0EventsLambdaThrottleAlarm",
            alarm_description=f"[{params.environment}] Auth0 Events Lambda Throttled",
            metric=self.lambda_function.metric_throttles(),
            threshold=1,
            evaluation_periods=1,
            comparison_operator=aws_cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
            treat_missing_data=aws_cloudwatch.TreatMissingData.IGNORE,
        )

        if params.cloudwatch_alarm_arn:
            notification_action = aws_cloudwatch_actions.SnsAction(
                aws_sns.Topic.from_topic_arn(
                    id="Auth0EventsNotifySupportTopic",
                    topic_arn=params.cloudwatch_alarm_arn,
                    scope=self,
                )
            )
            #     self.dlq_depth_alarm.add_alarm_action(notification_action)
            #     self.dlq_message_age_alarm.add_alarm_action(notification_action)
            self.lambda_error_rate_alarm.add_alarm_action(notification_action)
            self.lambda_throttle_alarm.add_alarm_action(notification_action)
        else:
            print(
                f"*** NO CW ALARM CONFIGURED FOR Auth0EventLambda in {params.environment} ***"
            )
