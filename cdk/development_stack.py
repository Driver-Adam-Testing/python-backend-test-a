from aws_cdk import (
    Stack,
)
from constructs import Construct

from cdk.constructs.backend import Backend, BackendParams
from cdk.constructs.onboarding_lambda import OnboardingLambda, OnboardingLambdaParams


class DevelopmentStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        backend = Backend(
            self,
            "ApiBackend",
            BackendParams(
                environment="development",
                cors_origins="https://app.dev.driverai.com,https://labs.dev.driverai.com,https://app2.dev.driverai.com,http://localhost:3000,https://app.beta.driverai.com",
                allowed_ips=["98.142.217.111/32"],
            ),
        )
        onboarding_lambda = OnboardingLambda(
            self,
            "OnboardingLambda",
            OnboardingLambdaParams(
                environment="development",
                api_url="https://api.dev.driverai.com/api/v1",
                auth0_url="https://auth.dev.driverai.com",
            ),
        )
