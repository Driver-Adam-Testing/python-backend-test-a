from typing import List
from aws_cdk import (
    aws_secretsmanager,
    aws_lambda,
    aws_lambda_event_sources,
    aws_lambda_python_alpha,
    aws_s3,
    aws_sns,
    aws_ssm,
    Duration
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
        
        dropzone_bucket = aws_s3.Bucket.from_bucket_name(scope, "dropzone-bucket", params.environment + "-codebase-dropzone")

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
                "API_URL": params.api_url,
                "AUTH0_URL": params.auth0_url,
                "AWS_S3_CODE_BUCKET_SUFFIX": "codebase-onboarding"
            },
            bundling=aws_lambda_python_alpha.BundlingOptions(asset_excludes=['.venv', '.env', 'tests/', '.pytest*']),
            timeout=Duration.seconds(15)
        )
        client_id_secret.grant_read(lambda_function)
        client_secret_secret.grant_read(lambda_function)
        dropzone_bucket.grant_read(lambda_function)

        sns_topic = aws_sns.Topic(scope, "CodeOnboardingTopic")
        lambda_function.add_event_source(aws_lambda_event_sources.SnsEventSource(sns_topic))
