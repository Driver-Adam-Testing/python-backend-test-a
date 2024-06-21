from aws_cdk import (
    Stack,
    aws_s3 as s3,
)
from cdk.constructs.backend import Backend, BackendParams
from cdk.constructs.onboarding_lambda import OnboardingLambda, OnboardingLambdaParams
from constructs import Construct

class DevelopmentStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        backend = Backend(self, "ApiBackend", BackendParams(
            environment="development",
            cors_origins="https://app.dev.driverai.com,https://labs.dev.driverai.com,https://app2.dev.driverai.com,http://localhost:3000",
            allowed_ips=["98.142.217.111/32"]
        ))
        onboarding_lambda = OnboardingLambda(self, "OnboardingLambda", OnboardingLambdaParams(environment="development", api_url="https://api.ops.driverai.com/api/v1", auth0_url="https://auth.dev.driverai.com"))
