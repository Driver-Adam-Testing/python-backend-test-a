import json
from aws_cdk import (
    CfnOutput,
    Duration,
    Stack,
    aws_ec2,
    aws_ecr,
    aws_ecs,
    aws_events,
    aws_iam,
    aws_logs,
    aws_route53,
    aws_s3,
    aws_secretsmanager,
    aws_ssm,
    aws_elasticloadbalancingv2 as elbv2,
    RemovalPolicy,
)
from constructs import Construct
from cdk.settings import settings


class SCIMServerParams:
    def __init__(
        self,
        environment: str,
        aws_region: str,
        aws_account: str,
        metrics_bus: aws_events.EventBus,
        load_balancer: elbv2.ApplicationLoadBalancer,
        listener: elbv2.ApplicationListener
    ) -> None:
        self.environment = environment
        self.aws_region = aws_region
        self.aws_account = aws_account
        self.metrics_bus = metrics_bus
        self.load_balancer = load_balancer
        self.listener = listener


class SCIMServer(Construct):
    def __init__(self, scope: Construct, id: str, params: SCIMServerParams) -> None:
        super().__init__(scope, id)

        # --- Baseline lookups / shared infra ---
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

        base_env = {
            "PROJECT_NAME": "DriverAI SCIM Server",
            "ENVIRONMENT": params.environment,
            "AWS_REGION": params.aws_region,
            "ECS_CONTAINER_STOP_TIMEOUT": "2s",
        }

        if settings.IS_PRIVATE_DEPLOY == "true":
            base_env["IS_PRIVATE_DEPLOY"] = "true"

        deployment_secrets = aws_secretsmanager.Secret.from_secret_name_v2(
            self, "deployment_secrets", secret_name=settings.SECRECTS_NAME
        )

        secret_fields = settings.SECRECTS_KEYS.split(",")
        secrets_map = {
            k: aws_ecs.Secret.from_secrets_manager(deployment_secrets, field=k)
            for k in secret_fields
        }

        base_env.update(settings.to_dict())

        scim_task_def = aws_ecs.FargateTaskDefinition(
            self,
            "SCIMServerTaskDef",
            cpu=2048,
            memory_limit_mib=4096,
            runtime_platform=aws_ecs.RuntimePlatform(
                cpu_architecture=aws_ecs.CpuArchitecture.X86_64
            ),
        )

        scim_container = scim_task_def.add_container(
            "SCIMServerContainer",
            image=aws_ecs.ContainerImage.from_ecr_repository(
                aws_ecr.Repository.from_repository_name(
                    self, "SCIMServerRepo", "scim-server" 
                ),
                tag="latest",
            ),
            environment=base_env,
            secrets=secrets_map,
            logging=aws_ecs.LogDrivers.aws_logs(
                stream_prefix="scim-server",
                log_retention=aws_logs.RetentionDays.ONE_YEAR,
            ),
        )
        # Optional: a port for metrics/debugging
        # worker_container.add_port_mappings(aws_ecs.PortMapping(container_port=9000))

        # Inline policy example: customer-scoped Secrets Manager access (match main service)
        scim_task_def.task_role.attach_inline_policy(
            aws_iam.Policy(
                self,
                "CustomerSecretsRWWorker",
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

        # --- Fargate Service (Internal only, no ALB) ---
        self.scim_service = aws_ecs.FargateService(
            self,
            "SCIMServerSvc",
            cluster=cluster,
            task_definition=scim_task_def,
            desired_count=1,  # Run 2 copies
            assign_public_ip=False,
            vpc_subnets=aws_ec2.SubnetSelection(
                subnet_group_name="Private"
            ),
            circuit_breaker=aws_ecs.DeploymentCircuitBreaker(enable=True, rollback=True),
            min_healthy_percent=100,
            max_healthy_percent=200,
        )

        # Allow the worker to emit metrics/events
        params.metrics_bus.grant_all_put_events(scim_task_def.task_role)

        if settings.IS_PRIVATE_DEPLOY == "true":
            firewall_cert_secret = aws_secretsmanager.Secret.from_secret_name_v2(
                self, "FirewallCertSecret", secret_name="/network-firewall/ca-certificate"
            )
            firewall_cert_secret.grant_read(self.scim_service.task_definition.task_role)

        # Outputs
        CfnOutput(
            self,
            "SCIMServiceArn",
            export_name="SCIMServiceArn",
            value=self.scim_service.service_arn,
        )
