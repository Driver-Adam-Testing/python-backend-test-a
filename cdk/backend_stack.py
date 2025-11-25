import json

from aws_cdk import Stack
from constructs import Construct

from cdk.constructs.asset_onboarding_lambda import (
    AssetOnboardingLambda,
    AssetOnboardingLambdaParams,
)
from cdk.constructs.auth0_event_lambda import Auth0EventLambda
from cdk.constructs.backend import Backend, BackendParams
from cdk.constructs.hatchet_worker import HatchetWorker, HatchetWorkerParams
from cdk.constructs.metrics_lambda import MetricsLambda, MetricsLambdaParams
from cdk.settings import settings


class BackendStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs: any) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.cdkenv = kwargs.get("env")
        print(f"AWS environment set to : {self.cdkenv}")
        print(
            f"Rollback set to : {json.loads(settings.BACKEND_ENABLE_ROLLBACK.lower())}"
        )

        cors_origins = settings.CORS_ORIGINS

        self.metrics_lambda = MetricsLambda(
            self,
            "MetricsLambda",
            MetricsLambdaParams(
                environment=settings.DEPLOYMENT_ENVIRONMENT,
                cloudwatch_alarm_arn=settings.METRICSLAMBDA_CW_ALARM,
            ),
        )

        self.auth0_event_lambda = Auth0EventLambda(
            self, "Auth0EventLambda", environment=settings.DEPLOYMENT_ENVIRONMENT
        )

        self.hatchetworker = HatchetWorker(
            self,
            "HatchetWorker",
            HatchetWorkerParams(
                environment=settings.DEPLOYMENT_ENVIRONMENT,
                metrics_bus=self.metrics_lambda.metrics_bus,
                aws_region=self.cdkenv.region,
                aws_account=self.cdkenv.account,
            ),
        )

        self.backend = Backend(
            self,
            "ApiBackend",
            BackendParams(
                environment=settings.DEPLOYMENT_ENVIRONMENT,
                cors_origins=cors_origins,
                allowed_ips=[settings.BACKEND_ALLOWED_IPS],
                use_legacy_dropzone=True,
                metrics_bus=self.metrics_lambda.metrics_bus,
                aws_region=self.cdkenv.region,
                aws_account=self.cdkenv.account,
                is_private_deploy=settings.IS_PRIVATE_DEPLOY,
            ),
        )
        self.onboarding_lambda = AssetOnboardingLambda(
            self,
            "AssetOnboardingLambda",
            AssetOnboardingLambdaParams(
                environment=settings.DEPLOYMENT_ENVIRONMENT,
                api_url=f"{self.backend.api_url}/studio/v1",
                auth0_audience=settings.ONBOARDING_LAMDBA_AUTH0_AUDIENCE,
                auth0_url=settings.ONBOARDING_LAMDBA_AUTH0_URL,
                dropzone_bucket=self.backend.dropzone_bucket,
                use_legacy_dropzone=True,
                vpc=self.backend.vpc,
                is_private_deploy=settings.IS_PRIVATE_DEPLOY
            ),
        )
