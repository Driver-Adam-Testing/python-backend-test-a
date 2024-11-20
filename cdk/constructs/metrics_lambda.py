import os

from aws_cdk import (
    Duration,
    aws_events,
    aws_lambda,
    aws_lambda_python_alpha,
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
        print(driver_db_path)
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
        # const eventTarget = new awsEventsTargets.LambdaFunction(lambdaAlias, {
        #     event: awsEvents.RuleTargetInput.fromObject(meetingSyncEvent)
        # })
        event_target = targets.LambdaFunction(
            self.lambda_function,
            # event=aws_events.RuleTargetInput.from_object(meeting_sync_event)
            # event_pattern=aws_events.EventPattern(
            #     source=["*"]
            # )
        )
        self.metrics_bus = aws_events.EventBus(
            self, "MetricsBus", event_bus_name="metrics-event-bus"
        )
        self.metrics_rule = aws_events.Rule(
            self,
            "MetricsProcessorRule",
            event_bus=self.metrics_bus,
            targets=[event_target],
            event_pattern=aws_events.EventPattern(source=["metrics.client"]),
        )
