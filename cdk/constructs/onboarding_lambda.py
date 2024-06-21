from typing import List
from aws_cdk import (
    aws_secretsmanager,
    aws_lambda,
    aws_lambda_event_sources,
    aws_lambda_python_alpha,
    aws_sns,
    aws_ssm
)
from constructs import Construct

class OnboardingLambdaParams:
    environment: str
    api_url: str
    auth0_url: str
    def __init__(self, environment, api_url, auth0_url):
        self.environment = environment
        self.api_url = api_url
        self.auth0_url = auth0_url

class OnboardingLambda(Construct):
    def __init__(self, scope: Construct, id: str, params: OnboardingLambdaParams):
        super().__init__(scope, id)

        s3_secret_name = aws_ssm.StringParameter.value_from_lookup(scope, parameter_name="/baseline/infra/v2/pythonBackend/s3CredentialsName")
        s3_secret = aws_secretsmanager.Secret.from_secret_name_v2(self, "S3Secret", secret_name=s3_secret_name)

        client_id_secret = aws_secretsmanager.Secret(scope, "ClientIdSecret")
        client_secret_secret = aws_secretsmanager.Secret(scope, "ClientSecretSecret")
        lambda_function = aws_lambda_python_alpha.PythonFunction(scope, "OnboardingLambdaPy", 
            entry="content_services/onboarding_event_handler", 
            runtime=aws_lambda.Runtime.PYTHON_3_12, 
            index="src/main.py", 
            environment={
                "ENVIRONMENT": params.environment, 
                "CLIENT_ID_SECRET": client_id_secret.secret_name, 
                "CLIENT_SECRET_SECRET": client_secret_secret.secret_name,
                "L_AWS_ACCESS_KEY_ID": s3_secret_name,
                "L_AWS_SECRET_ACCESS_KEY": s3_secret_name,
                "API_URL": params.api_url,
                "AUTH0_URL": params.auth0_url,
            },
            bundling=aws_lambda_python_alpha.BundlingOptions(asset_excludes=['.venv', '.env', 'tests/', '.pytest*'])
        )
        client_id_secret.grant_read(lambda_function)
        client_secret_secret.grant_read(lambda_function)
        s3_secret.grant_read(lambda_function)

        sns_topic = aws_sns.Topic(scope, "CodeOnboardingTopic")
        lambda_function.add_event_source(aws_lambda_event_sources.SnsEventSource(sns_topic))
