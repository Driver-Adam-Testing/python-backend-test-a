import json
from aws_cdk import (
    CfnOutput,
    Duration,
    Stack,
    aws_ec2,
    aws_ecr,
    aws_ecs,
    aws_ecs_patterns,
    aws_elasticloadbalancingv2,
    aws_elasticloadbalancingv2_targets,
    aws_events,
    aws_iam,
    aws_logs,
    aws_route53,
    aws_route53_targets,
    aws_s3,
    aws_secretsmanager,
    aws_ssm,
    RemovalPolicy
)
from constructs import Construct
from cdk.settings import settings
from cdk.constructs.guard_duty_S3_malware_protection import GuardDutyS3MalwareProtection


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
        is_private_deploy: bool = False,
        allowed_aws_account: str | None = None,
    ) -> None:
        self.cors_origins = cors_origins
        self.allowed_ips = allowed_ips
        self.environment = environment
        self.use_legacy_dropzone = use_legacy_dropzone
        self.metrics_bus = metrics_bus
        self.aws_region = aws_region
        self.aws_account = aws_account
        self.is_private_deploy = is_private_deploy
        self.allowed_aws_account = allowed_aws_account


class Backend(Construct):
    def __init__(self, scope: Construct, id: str, params: BackendParams) -> None:
        super().__init__(scope, id)

        vpc_id = aws_ssm.StringParameter.value_from_lookup(
            scope, parameter_name="/baseline/infra/v2/vpc/id"
        )
        self.vpc = aws_ec2.Vpc.from_lookup(self, id="BaselineVPC", vpc_id=vpc_id)

        cluster_name = aws_ssm.StringParameter.value_from_lookup(
            scope, parameter_name="/baseline/infra/v2/ecs/cluster/name"
        )
        cluster = aws_ecs.Cluster.from_cluster_attributes(
            self, id="BaselineCluster", cluster_name=cluster_name, vpc=self.vpc
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
        api_domain_name = "api." + hosted_zone.zone_name

        inspector_bucket_name = aws_ssm.StringParameter.value_from_lookup(
            scope, parameter_name="/baseline/infra/v2/inspector/stateBucketName"
        )

        openai_url = aws_ssm.StringParameter.value_from_lookup(
            scope, parameter_name="/baseline/infra/v2/azure/openai/url", default_value=None
        )

        self.dropzone_bucket = aws_s3.Bucket(
            self,
            "DropzoneBucket",
            removal_policy=RemovalPolicy.DESTROY, 
            auto_delete_objects=True,       
            bucket_name=f"{settings.DEPLOYMENT_ENVIRONMENT}-codebase-dropzone",
            cors=[
                {
                    "allowedMethods": [
                        aws_s3.HttpMethods.PUT,
                        aws_s3.HttpMethods.POST,
                        aws_s3.HttpMethods.GET,
                    ],
                    "allowedOrigins": params.cors_origins.split(","),
                    "allowedHeaders": ["*"],
                    "exposedHeaders":[
                        "x-amz-server-side-encryption",
                        "x-amz-request-id",
                        "x-amz-id-2"    
                    ]
                }
            ],
            lifecycle_rules=[aws_s3.LifecycleRule(expiration=Duration.days(7))],
        )

        guard_duty_mlp = GuardDutyS3MalwareProtection(self,"GuardDutyMP")
        guard_duty_mlp.add_bucket(self.dropzone_bucket)

        container_environment_vars = {
            "BACKEND_CORS_ORIGINS": params.cors_origins,
            "PORT": "8000",
            "PROJECT_NAME": "DriverAI API",
            "ENVIRONMENT": params.environment,
            "DROPZONE_BUCKET_NAME": self.dropzone_bucket.bucket_name,
            "AWS_S3_CODE_BUCKET_SUFFIX": "codebase-dropzone",
            "USE_LEGACY_DROPZONE": "True" if params.use_legacy_dropzone else "False",
            "INSPECTOR_BUCKET_NAME": inspector_bucket_name,
            "AWS_REGION": params.aws_region,
            "ECS_CONTAINER_STOP_TIMEOUT": "2s",
            "IS_PRIVATE_DEPLOY": "true" if params.is_private_deploy else "false",
            "HATCHET_CLIENT_HOST_PORT" : f"hatchet.{hosted_zone.zone_name}:7077",
            "HATCHET_CLIENT_TLS_STRATEGY": "none"
            #TODO POST secets optimzation. Consider removing all of this and just sourcing the setEnv.sh from deplyonments on container startup.
        }

        if openai_url is not None:
            container_environment_vars["AZURE_OPENAI_BASE_URL"] = openai_url

        deployment_secrets = aws_secretsmanager.Secret.from_secret_name_v2(
            self, "deployment_secrets", secret_name=settings.SECRECTS_NAME
        )

        hatchet_token_secret = aws_secretsmanager.Secret.from_secret_name_v2(
            self, "hatchet_secret", secret_name="hatchet/appliance/credentials"
        )

        secret_fields = settings.SECRECTS_KEYS.split(',')

        secrets_map = {
            k: aws_ecs.Secret.from_secrets_manager(deployment_secrets, field=k)
            for k in secret_fields
        }
        secrets_map["HATCHET_CLIENT_TOKEN"] = aws_ecs.Secret.from_secrets_manager(hatchet_token_secret)

        container_environment_vars.update(settings.to_dict())

        repository = aws_ecr.Repository.from_repository_name(
            self, "PythonBackendRepo", "python-backend"
        )

        task_options = aws_ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
            image=aws_ecs.ContainerImage.from_ecr_repository(repository, tag="latest"),
            secrets=secrets_map,
            environment=container_environment_vars,
            container_port=8000,
            log_driver=aws_ecs.LogDrivers.aws_logs(
                stream_prefix="python-backend",
                log_retention=aws_logs.RetentionDays.ONE_YEAR,
            ),
        )

        # For private deploys, create ALB in private subnets
        private_alb = None
        if params.is_private_deploy:
            private_alb = aws_elasticloadbalancingv2.ApplicationLoadBalancer(
                self,
                "PrivateALB",
                vpc=self.vpc,
                internet_facing=False,
                vpc_subnets=aws_ec2.SubnetSelection(subnet_group_name="Private"),
            )

        self.service = aws_ecs_patterns.ApplicationLoadBalancedFargateService(
            self,
            "BackendApi",
            load_balancer=private_alb,
            protocol=aws_elasticloadbalancingv2.ApplicationProtocol.HTTPS,
            ssl_policy=aws_elasticloadbalancingv2.SslPolicy.FIPS_TLS13_12_RES,
            platform_version=aws_ecs.FargatePlatformVersion.LATEST,
            # Github Actions runners only provide x86 - we'd have to go to self-hosted to deploy ARM currently
            # There is a limited beta, so support for ARM is coming
            # https://github.com/orgs/community/discussions/25319
            runtime_platform=aws_ecs.RuntimePlatform(
                cpu_architecture=aws_ecs.CpuArchitecture.X86_64
            ),
            redirect_http=not params.is_private_deploy,
            public_load_balancer=not params.is_private_deploy,
            assign_public_ip=False,
            desired_count=2,
            cluster=cluster,
            domain_zone=hosted_zone,
            domain_name=api_domain_name,
            task_image_options=task_options,
            task_subnets=aws_ec2.SubnetSelection(
                subnet_group_name="Private"
            ),
            health_check_grace_period=Duration.seconds(120),
            circuit_breaker=aws_ecs.DeploymentCircuitBreaker(
                enable=json.loads(settings.BACKEND_ENABLE_ROLLBACK.lower()), rollback=json.loads(settings.BACKEND_ENABLE_ROLLBACK.lower())
            ),
            min_healthy_percent=100,
            max_healthy_percent=200,
            cpu=2048,
            memory_limit_mib=4096,
        )
        self.service.target_group.configure_health_check(
            path="/studio/v1/healthcheck/", port="8000",
            interval=Duration.seconds(5),  
            timeout=Duration.seconds(2),  
            healthy_threshold_count=2,  
            unhealthy_threshold_count=2,  
            healthy_http_codes="200",  # 
        )
        self.service.target_group.deregistration_delay = Duration.seconds(5)
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

        self.backend_alb = self.service.load_balancer
        self.backend_alb_listener = self.service.listener

        # Grant permission to read firewall certificate for private deployments
        if params.is_private_deploy:
            firewall_cert_secret = aws_secretsmanager.Secret.from_secret_name_v2(
                self, "FirewallCertSecret", secret_name="/network-firewall/ca-certificate"
            )
            firewall_cert_secret.grant_read(self.service.task_definition.task_role)

            # Create NLB for PrivateLink (VPC Endpoint Services require NLB, not ALB)
            private_subnets = self.vpc.select_subnets(subnet_group_name="Private")

            privatelink_nlb = aws_elasticloadbalancingv2.NetworkLoadBalancer(
                self,
                "PrivateLinkApiNlb",
                vpc=self.vpc,
                internet_facing=False,
                vpc_subnets=aws_ec2.SubnetSelection(subnets=private_subnets.subnets),
            )

            privatelink_nlb_target_group = aws_elasticloadbalancingv2.NetworkTargetGroup(
                self,
                "PrivateLinkApiAlbTargetGroup",
                vpc=self.vpc,
                port=443,
                protocol=aws_elasticloadbalancingv2.Protocol.TCP,
                target_type=aws_elasticloadbalancingv2.TargetType.ALB,
                targets=[
                    aws_elasticloadbalancingv2_targets.AlbTarget(
                        self.service.load_balancer, 443
                    )
                ],
                health_check=aws_elasticloadbalancingv2.HealthCheck(
                    protocol=aws_elasticloadbalancingv2.Protocol.HTTPS,
                    path="/studio/v1/healthcheck/",
                    healthy_threshold_count=2,
                    unhealthy_threshold_count=2,
                    interval=Duration.seconds(30),
                ),
            )

            privatelink_nlb.add_listener(
                "PrivateLinkApiNlbListener",
                port=443,
                protocol=aws_elasticloadbalancingv2.Protocol.TCP,
                default_action=aws_elasticloadbalancingv2.NetworkListenerAction.forward(
                    target_groups=[privatelink_nlb_target_group]
                ),
            )

            # Create VPC Endpoint Service for PrivateLink access
            allowed_principals = None
            if params.allowed_aws_account:
                allowed_principals = [
                    aws_iam.ArnPrincipal(f"arn:aws:iam::{params.allowed_aws_account}:root")
                ]

            self.endpoint_service = aws_ec2.VpcEndpointService(
                self,
                "PrivateLinkApiEndpointService",
                vpc_endpoint_service_load_balancers=[privatelink_nlb],
                acceptance_required=False,
                allowed_principals=allowed_principals,
            )

            # Configure private DNS with automatic domain verification
            aws_route53.VpcEndpointServiceDomainName(
                self,
                "PrivateLinkApiDomainName",
                endpoint_service=self.endpoint_service,
                domain_name=api_domain_name,
                public_hosted_zone=hosted_zone,
            )

            CfnOutput(
                self,
                "PrivateLinkApiServiceName",
                export_name="PrivateLinkApiServiceName",
                value=self.endpoint_service.vpc_endpoint_service_name,
                description="VPC Endpoint Service name for PrivateLink connections",
            )

            CfnOutput(
                self,
                "PrivateLinkApiServiceId",
                export_name="PrivateLinkApiServiceId",
                value=self.endpoint_service.vpc_endpoint_service_id,
                description="VPC Endpoint Service ID for managing connections",
            )

            CfnOutput(
                self,
                "PrivateLinkApiAvailabilityZones",
                export_name="PrivateLinkApiAvailabilityZones",
                value=",".join(private_subnets.availability_zones),
                description="Availability zones where the VPC Endpoint Service is available",
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

        params.metrics_bus.grant_all_put_events(self.service.task_definition.task_role)

        # Grant full S3 admin access. TODO: Scope this down?
        self.service.task_definition.task_role.add_managed_policy(
            aws_iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3FullAccess")
        )

        # Create private hosted zone entry for internal VPC routing
        private_hosted_zone_id = aws_ssm.StringParameter.value_from_lookup(
            scope, parameter_name="/baseline/infra/v2/route53/privateHostedZoneId"
        )
        private_hosted_zone_name = aws_ssm.StringParameter.value_from_lookup(
            scope, parameter_name="/baseline/infra/v2/route53/privateHostedZoneName"
        )
        private_hosted_zone = aws_route53.HostedZone.from_hosted_zone_attributes(
            self,
            id="BaselinePrivateHostedZone",
            zone_name=private_hosted_zone_name,
            hosted_zone_id=private_hosted_zone_id,
        )

        # Create A record in private zone pointing to ALB's private IPs
        # TODO: Manually added Auth0 auth.*.driverai.com record needs to exist in private hosted zone too
        aws_route53.ARecord(
            self,
            "PrivateApiDnsRecord",
            zone=private_hosted_zone,
            record_name=api_domain_name,
            target=aws_route53.RecordTarget.from_alias(
                aws_route53_targets.LoadBalancerTarget(self.service.load_balancer)
            ),
        )
        
        self.api_url = f"https://{api_domain_name}"

        # TODO - re-enable WAF when endpoints have been refactored not to send entire app notes
        # https://linear.app/driver-ai/issue/PE-1077/explore-options-for-allowing-app-notes-containing-httplocalhost-and
        # AwsWAF(self, "AWS_WAF", params=AwsWAFParams(service=service))
