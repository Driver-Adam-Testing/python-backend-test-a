import os

from aws_cdk import Stack
from constructs import Construct

from cdk.constructs.auth0_event_lambda import Auth0EventLambda

"""
This stack is not required!!!
It is only here to allow deploying the Auth0EventLambda construct in isolation for testing purposes.
"""


class Auth0EventStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs: any) -> None:
        super().__init__(scope, construct_id, **kwargs)

        deployment_environment = os.environ["DEPLOYMENT_ENVIRONMENT"]
        print(
            f"Deploying Auth0 Event Stream infrastructure for {deployment_environment}"
        )

        self.auth0_event_lambda = Auth0EventLambda(
            self,
            "Auth0EventLambda",
            environment=deployment_environment,
        )
