from aws_cdk import (
    CfnOutput,
    Duration,
    Stack,
    aws_ec2,
    aws_ecr,
    aws_ecs,
    aws_ecs_patterns,
    aws_elasticloadbalancingv2,
    aws_events,
    aws_iam,
    aws_logs,
    aws_route53,
    aws_s3,
    aws_secretsmanager,
    aws_ssm,
)
from constructs import Construct


# TODO: parameterize task count and container size
class BackendParams:
    def __init__(
        self,
        cors_origins: str,
        allowed_ips: list[str],
        environment: str,
        use_legacy_dropzone: bool,
        metrics_bus: aws_events.EventBus,
        aws_region: str,
        aws_account: str,
    ) -> None:
        self.cors_origins = cors_origins
        self.allowed_ips = allowed_ips
        self.environment = environment
        self.use_legacy_dropzone = use_legacy_dropzone
        self.metrics_bus = metrics_bus
        self.aws_region = aws_region
        self.aws_account = aws_account


class Backend(Construct):
    def __init__(self, scope: Construct, id: str, params: BackendParams) -> None:
        super().__init__(scope, id)

        vpc_id = aws_ssm.StringParameter.value_from_lookup(
            scope, parameter_name="/baseline/infra/v2/vpc/id"
        )
        vpc = aws_ec2.Vpc.from_lookup(self, id="BaselineVPC", vpc_id=vpc_id)

        cluster_name = aws_ssm.StringParameter.value_from_lookup(
            scope, parameter_name="/baseline/infra/v2/ecs/cluster/name"
        )
        cluster = aws_ecs.Cluster.from_cluster_attributes(
            self, id="BaselineCluster", cluster_name=cluster_name, vpc=vpc
        )

        hosted_zone_id = aws_ssm.StringParameter.value_from_lookup(
            scope, parameter_name="/baseline/infra/v2/route53/hostedZoneId"
        )
        hosted_zone_name = aws_ssm.StringParameter.value_from_lookup(
            scope, parameter_name="/baseline/infra/v2/route53/hostedZoneName"
        )
        hosted_zone = aws_route53.HostedZone.from_hosted_zone_attributes(
            self,
            id="BaselineHostedZone",
            zone_name=hosted_zone_name,
            hosted_zone_id=hosted_zone_id,
        )

        postgres_secret_name = aws_ssm.StringParameter.value_from_lookup(
            scope,
            parameter_name="/baseline/infra/v2/pythonBackend/postgresCredentialsName",
        )
        postgres_secret = aws_secretsmanager.Secret.from_secret_name_v2(
            self, "PostgresSecret", secret_name=postgres_secret_name
        )

        modal_secret_name = aws_ssm.StringParameter.value_from_lookup(
            scope,
            parameter_name="/baseline/infra/v2/pythonBackend/modalCredentialsName",
        )
        modal_secret = aws_secretsmanager.Secret.from_secret_name_v2(
            self, "ModalSecret", secret_name=modal_secret_name
        )

        auth0_secret_name = aws_ssm.StringParameter.value_from_lookup(
            scope,
            parameter_name="/baseline/infra/v2/pythonBackend/auth0ConfigurationsName",
        )
        auth0_secret = aws_secretsmanager.Secret.from_secret_name_v2(
            self, "Auth0Secret", secret_name=auth0_secret_name
        )

        s3_secret_name = aws_ssm.StringParameter.value_from_lookup(
            scope, parameter_name="/baseline/infra/v2/pythonBackend/s3CredentialsName"
        )
        s3_secret = aws_secretsmanager.Secret.from_secret_name_v2(
            self, "S3Secret", secret_name=s3_secret_name
        )

        github_secret_name = aws_ssm.StringParameter.value_from_lookup(
            scope,
            parameter_name="/baseline/infra/v2/pythonBackend/githubConfigurationsName",
        )
        github_secret = aws_secretsmanager.Secret.from_secret_name_v2(
            self, "GitHubCredentials", secret_name=github_secret_name
        )
        sentry_secret_name = aws_ssm.StringParameter.value_from_lookup(
            scope,
            parameter_name="/baseline/infra/v2/pythonBackend/sentryCredentialName",
        )
        sentry_secret = aws_secretsmanager.Secret.from_secret_name_v2(
            self,
            "SentryCredential",
            secret_name=sentry_secret_name,
        )
        openai_secret_name = aws_ssm.StringParameter.value_from_lookup(
            scope, parameter_name="/baseline/infra/v2/pythonBackend/openAIApiKeyName"
        )
        openai_secret = aws_secretsmanager.Secret.from_secret_name_v2(
            self, "OpenAIApiKeyCredentials", secret_name=openai_secret_name
        )

        inspector_bucket_name = aws_ssm.StringParameter.value_from_lookup(
            scope, parameter_name="/baseline/infra/v2/inspector/stateBucketName"
        )

        self.dropzone_bucket = aws_s3.Bucket(
            self,
            "DropzoneBucket",
            cors=[
                {
                    "allowedMethods": [
                        aws_s3.HttpMethods.PUT,
                        aws_s3.HttpMethods.POST,
                        aws_s3.HttpMethods.GET,
                    ],
                    "allowedOrigins": params.cors_origins.split(","),
                    "allowedHeaders": ["*"],
                }
            ],
            lifecycle_rules=[aws_s3.LifecycleRule(expiration=Duration.days(7))],
        )
        container_environment_vars = {
            "BACKEND_CORS_ORIGINS": params.cors_origins.split(","),
            "PORT": "8000",
            "PROJECT_NAME": "DriverAI API",
            "ENVIRONMENT": params.environment,
            "DROPZONE_BUCKET_NAME": self.dropzone_bucket.bucket_name,
            "AWS_S3_CODE_BUCKET_SUFFIX": "codebase-dropzone",
            "USE_LEGACY_DROPZONE": "True" if params.use_legacy_dropzone else "False",
            "INSPECTOR_BUCKET_NAME": inspector_bucket_name,
            "AWS_REGION": params.aws_region,
        }

        container_secrets = {
            "POSTGRES_SERVER": aws_ecs.Secret.from_secrets_manager(
                postgres_secret, "SERVER"
            ),
            "POSTGRES_PORT": aws_ecs.Secret.from_secrets_manager(
                postgres_secret, "PORT"
            ),
            "POSTGRES_DB": aws_ecs.Secret.from_secrets_manager(postgres_secret, "DB"),
            "POSTGRES_USER": aws_ecs.Secret.from_secrets_manager(
                postgres_secret, "USER"
            ),
            "POSTGRES_PASSWORD": aws_ecs.Secret.from_secrets_manager(
                postgres_secret, "PASSWORD"
            ),
            "ASYNC_DATABASE_URL": aws_ecs.Secret.from_secrets_manager(
                postgres_secret, "ASYNC_DATABASE_URL"
            ),
            "AUTH0_DOMAIN": aws_ecs.Secret.from_secrets_manager(
                auth0_secret, "AUTH0_DOMAIN"
            ),
            "AUTH0_MGMT_API_DOMAIN": aws_ecs.Secret.from_secrets_manager(
                auth0_secret, "AUTH0_MGMT_API_DOMAIN"
            ),
            "AUTH0_CLIENT_ID": aws_ecs.Secret.from_secrets_manager(
                auth0_secret, "AUTH0_CLIENT_ID"
            ),
            "AUTH0_AUDIENCE": aws_ecs.Secret.from_secrets_manager(
                auth0_secret, "AUTH0_AUDIENCE"
            ),
            "AUTH0_MGMT_API_CLIENT_ID": aws_ecs.Secret.from_secrets_manager(
                auth0_secret, "AUTH0_MGMT_API_CLIENT_ID"
            ),
            "AUTH0_MGMT_API_CLIENT_SECRET": aws_ecs.Secret.from_secrets_manager(
                auth0_secret, "AUTH0_MGMT_API_CLIENT_SECRET"
            ),
            "AUTH0_MGMT_API_AUDIENCE": aws_ecs.Secret.from_secrets_manager(
                auth0_secret, "AUTH0_MGMT_API_AUDIENCE"
            ),
            # TODO: This is wrong and gross, but we have stuffed TURNSTILE keys into the Auth0 secret to avoid creating
            # another secret, since we are abandoning this overall approach very soon.
            "TURNSTILE_SECRET": aws_ecs.Secret.from_secrets_manager(
                auth0_secret, "TURNSTILE_SECRET"
            ),
            "ENABLE_SIGNUP": aws_ecs.Secret.from_secrets_manager(
                auth0_secret, "ENABLE_SIGNUP"
            ),
            "MODAL_TOKEN_ID": aws_ecs.Secret.from_secrets_manager(
                modal_secret, "MODAL_TOKEN_ID"
            ),
            "MODAL_TOKEN_SECRET": aws_ecs.Secret.from_secrets_manager(
                modal_secret, "MODAL_TOKEN_SECRET"
            ),
            "MODAL_ENVIRONMENT": aws_ecs.Secret.from_secrets_manager(
                modal_secret, "MODAL_ENVIRONMENT"
            ),
            "AWS_ACCESS_KEY_ID": aws_ecs.Secret.from_secrets_manager(
                s3_secret, "AWS_ACCESS_KEY_ID"
            ),
            "AWS_SECRET_ACCESS_KEY": aws_ecs.Secret.from_secrets_manager(
                s3_secret, "AWS_SECRET_ACCESS_KEY"
            ),
            "GH_CLIENT_ID": aws_ecs.Secret.from_secrets_manager(
                github_secret, "GH_CLIENT_ID"
            ),
            "GH_CLIENT_SECRET": aws_ecs.Secret.from_secrets_manager(
                github_secret, "GH_CLIENT_SECRET"
            ),
            "GH_REDIRECT_URI": aws_ecs.Secret.from_secrets_manager(
                github_secret, "GH_REDIRECT_URI"
            ),
            "GH_WEBHOOK_SECRET": aws_ecs.Secret.from_secrets_manager(
                github_secret, "GH_WEBHOOK_SECRET"
            ),
            "GH_CLIENT_PEM_SECRET": aws_ecs.Secret.from_secrets_manager(
                github_secret, "GH_CLIENT_PEM_SECRET"
            ),
            "OPENAI_API_KEY": aws_ecs.Secret.from_secrets_manager(
                openai_secret,
                "OPENAI_API_KEY",  # TODO unused. can we remove from here without harm?
            ),
            "SENTRY_DSN": aws_ecs.Secret.from_secrets_manager(
                sentry_secret, "SENTRY_DSN"
            ),
        }

        repository = aws_ecr.Repository.from_repository_name(
            self, "PythonBackendRepo", "python-backend"
        )

        task_options = aws_ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
            image=aws_ecs.ContainerImage.from_ecr_repository(repository, tag="latest"),
            secrets=container_secrets,
            environment=container_environment_vars,
            container_port=8000,
            log_driver=aws_ecs.LogDrivers.aws_logs(
                stream_prefix="python-backend",
                log_retention=aws_logs.RetentionDays.ONE_YEAR,
            ),
        )
        self.service = aws_ecs_patterns.ApplicationLoadBalancedFargateService(
            self,
            "BackendApi",
            protocol=aws_elasticloadbalancingv2.ApplicationProtocol.HTTPS,
            ssl_policy=aws_elasticloadbalancingv2.SslPolicy.FIPS_TLS13_12_RES,
            platform_version=aws_ecs.FargatePlatformVersion.LATEST,
            # Github Actions runners only provide x86 - we'd have to go to self-hosted to deploy ARM currently
            # There is a limited beta, so support for ARM is coming
            # https://github.com/orgs/community/discussions/25319
            runtime_platform=aws_ecs.RuntimePlatform(
                cpu_architecture=aws_ecs.CpuArchitecture.X86_64
            ),
            redirect_http=True,
            assign_public_ip=False,
            desired_count=2,
            cluster=cluster,
            domain_zone=hosted_zone,
            domain_name="api." + hosted_zone.zone_name,
            task_image_options=task_options,
            task_subnets=aws_ec2.SubnetSelection(
                subnet_type=aws_ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
            health_check_grace_period=Duration.minutes(6),
            circuit_breaker=aws_ecs.DeploymentCircuitBreaker(
                enable=True, rollback=True
            ),
            min_healthy_percent=100,
            max_healthy_percent=250,
            cpu=2048,
            memory_limit_mib=4096,
        )
        self.service.target_group.configure_health_check(
            path="/studio/v1/healthcheck/", port="8000"
        )
        self.service.task_definition.task_role.attach_inline_policy(
            aws_iam.Policy(
                self,
                "CustomerSecretsRW",
                document=aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                "secretsmanager:CreateSecret",
                                "secretsmanager:ListSecrets",
                                "secretsmanager:DescribeSecret",
                            ],
                            resources=[
                                f"arn:aws:secretsmanager:{Stack.of(self).region}:{Stack.of(self).account}:secret:DRIVER_AI_CUSTOMER/*"
                            ],
                        )
                    ]
                ),
            )
        )

        # Output ECS Cluster ARN
        CfnOutput(
            self,
            "EcsClusterArn",
            export_name="EcsClusterArn",
            value=cluster.cluster_arn,
        )

        # Output ECS Service ARN
        CfnOutput(
            self,
            "EcsServiceArn",
            export_name="EcsServiceArn",
            value=self.service.service.service_arn,
        )

        # In the service: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/events/client/put_events.html
        # response = client.put_events(
        #     Entries=[
        #         {
        #             'Time': datetime(2015, 1, 1),
        #             'Source': 'string',
        #             'Resources': [
        #                 'string',
        #             ],
        #             'DetailType': 'string',
        #             'Detail': 'string', JSON-stringified whatever. Max size for 1 entry is 256KB
        #             'EventBusName': 'string',
        #             'TraceHeader': 'string'
        #         },
        #     ],
        #     EndpointId='string'
        # )
        params.metrics_bus.grant_all_put_events(self.service.task_definition.task_role)

        # TODO - re-enable WAF when endpoints have been refactored not to send entire app notes
        # https://linear.app/driver-ai/issue/PE-1077/explore-options-for-allowing-app-notes-containing-httplocalhost-and
        # AwsWAF(self, "AWS_WAF", params=AwsWAFParams(service=service))
