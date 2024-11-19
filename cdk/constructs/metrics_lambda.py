from aws_cdk import (
    Duration,
    aws_events,
    aws_lambda,
    aws_lambda_python_alpha,
)
from constructs import Construct


class MetricsLambdaParams:
    environment: str

    def __init__(
        self,
        environment: str,
    ) -> None:
        self.environment = environment


class MetricsLambda(Construct):
    def __init__(self, scope: Construct, id: str, params: MetricsLambdaParams) -> None:
        super().__init__(scope, id)

        self.lambda_function = aws_lambda_python_alpha.PythonFunction(
            scope,
            "MetricsLambdaPy",
            entry="lambdas/metrics_handler",
            runtime=aws_lambda.Runtime.PYTHON_3_12,
            index="src/main.py",
            environment={
                "ENVIRONMENT": params.environment,
                "LOG_LEVEL": "INFO",
            },
            bundling=aws_lambda_python_alpha.BundlingOptions(
                asset_excludes=[".venv", ".env", "tests/", ".pytest*"]
            ),
            reservedConcurrentExecutions=10,
            timeout=Duration.seconds(60),
        )

        self.metrics_bus = aws_events.EventBus(
            self, "MetricsBus", event_bus_name="metrics-event-bus"
        )
        self.metrics_rule = aws_events.Rule(
            self,
            "MetricsProcessorRule",
            event_bus=self.metrics_bus,
            targets=[self.lambda_function],
        )
