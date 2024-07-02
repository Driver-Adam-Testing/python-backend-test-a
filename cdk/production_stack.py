from aws_cdk import (
    Stack,
    aws_s3 as s3,
)
from constructs import Construct

from cdk.constructs.backend import Backend, BackendParams
from cdk.constructs.onboarding_lambda import OnboardingLambda, OnboardingLambdaParams

class ProductionStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        backend = Backend(self, "ApiBackend", BackendParams(
            environment="production",
            cors_origins="https://app.driverai.com",
            allowed_ips=[] # Currently disabled
        ))
        onboarding_lambda = OnboardingLambda(self, "OnboardingLambda", OnboardingLambdaParams(environment="production", api_url="https://api.us1.driverai.com/api/v1", auth0_url="https://auth.driverai.com"))

