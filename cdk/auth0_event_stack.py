import os

from aws_cdk import Stack
from constructs import Construct

from cdk.constructs.auth0_event_lambda import Auth0EventLambda, Auth0EventLambdaParams


class Auth0EventStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs: any) -> None:
        super().__init__(scope, construct_id, **kwargs)

        deployment_environment = os.environ.get("DEPLOYMENT_ENVIRONMENT")
        print(
            f"Deploying Auth0 Event Stream infrastructure for {deployment_environment}"
        )

        self.auth0_event_lambda = Auth0EventLambda(
            self,
            "Auth0EventLambda",
            Auth0EventLambdaParams(
                environment=deployment_environment,
            ),
        )

        # Output the DLQ URL for monitoring
        # from aws_cdk import CfnOutput
        #
        # CfnOutput(
        #     self,
        #     "Auth0EventsDLQUrl",
        #     value=self.auth0_event_lambda.events_dlq.queue_url,
        #     description="SQS DLQ URL for Auth0 events",
        #     export_name=f"Auth0EventsDLQUrl-{DEPLOYMENT_ENVIRONMENT}",
        # )
