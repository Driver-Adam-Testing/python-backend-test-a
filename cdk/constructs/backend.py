from typing import List
from aws_cdk import (
    Stack,
    aws_elasticloadbalancingv2,
    aws_secretsmanager,
    aws_ecs,
    aws_ecs_patterns,
    aws_ec2,
    aws_iam,
    aws_ssm,
    aws_route53,
    aws_wafv2,
    Duration
)
from constructs import Construct

# TODO: parameterize task count and container size
class BackendParams:
    cors_origins: str
    allowed_ips: List[str]
    environment: str
    def __init__(self, cors_origins, allowed_ips, environment):
        self.cors_origins = cors_origins
        self.allowed_ips = allowed_ips
        self.environment = environment
class Backend(Construct):
    def __init__(self, scope: Construct, id: str, params: BackendParams):
        super().__init__(scope, id)

        vpc_id = aws_ssm.StringParameter.value_from_lookup(scope, parameter_name="/baseline/infra/v2/vpc/id")
        vpc = aws_ec2.Vpc.from_lookup(self, id="BaselineVPC", vpc_id=vpc_id)

        cluster_name = aws_ssm.StringParameter.value_from_lookup(scope, parameter_name="/baseline/infra/v2/ecs/cluster/name")
        cluster = aws_ecs.Cluster.from_cluster_attributes(self, id="BaselineCluster", cluster_name=cluster_name, vpc=vpc)
 
        hosted_zone_id = aws_ssm.StringParameter.value_from_lookup(scope, parameter_name="/baseline/infra/v2/route53/hostedZoneId")
        hosted_zone_name = aws_ssm.StringParameter.value_from_lookup(scope, parameter_name="/baseline/infra/v2/route53/hostedZoneName")
        hosted_zone = aws_route53.HostedZone.from_hosted_zone_attributes(self, id="BaselineHostedZone", zone_name=hosted_zone_name, hosted_zone_id=hosted_zone_id)

        postgres_secret_name = aws_ssm.StringParameter.value_from_lookup(scope, parameter_name="/baseline/infra/v2/pythonBackend/postgresCredentialsName")
        postgres_secret = aws_secretsmanager.Secret.from_secret_name_v2(self, "PostgresSecret", secret_name=postgres_secret_name)

        modal_secret_name = aws_ssm.StringParameter.value_from_lookup(scope, parameter_name="/baseline/infra/v2/pythonBackend/modalCredentialsName")
        modal_secret = aws_secretsmanager.Secret.from_secret_name_v2(self, "ModalSecret", secret_name=modal_secret_name)

        auth0_secret_name = aws_ssm.StringParameter.value_from_lookup(scope, parameter_name="/baseline/infra/v2/pythonBackend/auth0ConfigurationsName")
        auth0_secret = aws_secretsmanager.Secret.from_secret_name_v2(self, "Auth0Secret", secret_name=auth0_secret_name)

        s3_secret_name = aws_ssm.StringParameter.value_from_lookup(scope, parameter_name="/baseline/infra/v2/pythonBackend/s3CredentialsName")
        s3_secret = aws_secretsmanager.Secret.from_secret_name_v2(self, "S3Secret", secret_name=s3_secret_name)

        github_secret_name = aws_ssm.StringParameter.value_from_lookup(scope, parameter_name="/baseline/infra/v2/pythonBackend/githubConfigurationsName")
        github_secret = aws_secretsmanager.Secret.from_secret_name_v2(self, "GitHubCredentials", secret_name=github_secret_name)

        container_environment_vars = {
            "BACKEND_CORS_ORIGINS": params.cors_origins,
            "PORT": "8000",
            "PROJECT_NAME": "DriverAI API",
            "ENVIRONMENT": params.environment,
            "AWS_S3_CODE_BUCKET_SUFFIX": "codebase-dropzone"
        }
        container_secrets = {
            "POSTGRES_SERVER": aws_ecs.Secret.from_secrets_manager(postgres_secret, "SERVER"), 
            "POSTGRES_PORT": aws_ecs.Secret.from_secrets_manager(postgres_secret, "PORT"),
            "POSTGRES_DB": aws_ecs.Secret.from_secrets_manager(postgres_secret, "DB"),
            "POSTGRES_USER": aws_ecs.Secret.from_secrets_manager(postgres_secret, "USER"),
            "POSTGRES_PASSWORD": aws_ecs.Secret.from_secrets_manager(postgres_secret, "PASSWORD"),
            "AUTH0_DOMAIN": aws_ecs.Secret.from_secrets_manager(auth0_secret, "AUTH0_DOMAIN"),
            "AUTH0_CLIENT_ID": aws_ecs.Secret.from_secrets_manager(auth0_secret, "AUTH0_CLIENT_ID"),
            "AUTH0_AUDIENCE": aws_ecs.Secret.from_secrets_manager(auth0_secret, "AUTH0_AUDIENCE"),
            "AUTH0_MGMT_API_CLIENT_ID": aws_ecs.Secret.from_secrets_manager(auth0_secret, "AUTH0_MGMT_API_CLIENT_ID"),
            "AUTH0_MGMT_API_CLIENT_SECRET": aws_ecs.Secret.from_secrets_manager(auth0_secret, "AUTH0_MGMT_API_CLIENT_SECRET"),
            "AUTH0_MGMT_API_AUDIENCE": aws_ecs.Secret.from_secrets_manager(auth0_secret, "AUTH0_MGMT_API_AUDIENCE"),
            "MODAL_TOKEN_ID": aws_ecs.Secret.from_secrets_manager(modal_secret, "MODAL_TOKEN_ID"),
            "MODAL_TOKEN_SECRET": aws_ecs.Secret.from_secrets_manager(modal_secret, "MODAL_TOKEN_SECRET"),
            "MODAL_ENVIRONMENT": aws_ecs.Secret.from_secrets_manager(modal_secret, "MODAL_ENVIRONMENT"),
            "AWS_ACCESS_KEY_ID": aws_ecs.Secret.from_secrets_manager(s3_secret, "AWS_ACCESS_KEY_ID"),
            "AWS_SECRET_ACCESS_KEY": aws_ecs.Secret.from_secrets_manager(s3_secret, "AWS_SECRET_ACCESS_KEY"),
            "GH_CLIENT_ID": aws_ecs.Secret.from_secrets_manager(github_secret, "GH_CLIENT_ID"),
            "GH_CLIENT_SECRET": aws_ecs.Secret.from_secrets_manager(github_secret, "GH_CLIENT_SECRET"),
            "GH_REDIRECT_URI": aws_ecs.Secret.from_secrets_manager(github_secret, "GH_REDIRECT_URI"),
            "GH_WEBHOOK_SECRET": aws_ecs.Secret.from_secrets_manager(github_secret, "GH_WEBHOOK_SECRET"),
        }
        
        task_image = aws_ecs.ContainerImage.from_asset(".", asset_name="python-backend")
        task_options = aws_ecs_patterns.ApplicationLoadBalancedTaskImageOptions(image=task_image, secrets=container_secrets, environment=container_environment_vars, container_port=8000)
        service = aws_ecs_patterns.ApplicationLoadBalancedFargateService(self, "BackendApi",
            protocol=aws_elasticloadbalancingv2.ApplicationProtocol.HTTPS,
            platform_version=aws_ecs.FargatePlatformVersion.LATEST,
            # Github Actions runners only provide x86 - we'd have to go to self-hosted to deploy ARM currently
            # There is a limited beta, so support for ARM is coming
            # https://github.com/orgs/community/discussions/25319
            runtime_platform=aws_ecs.RuntimePlatform(cpu_architecture=aws_ecs.CpuArchitecture.X86_64),
            redirect_http=True,
            assign_public_ip=False,
            desired_count=2,
            cluster=cluster,
            domain_zone=hosted_zone,
            domain_name="api." + hosted_zone.zone_name,
            task_image_options=task_options,
            task_subnets=aws_ec2.SubnetSelection(subnet_type=aws_ec2.SubnetType.PRIVATE_WITH_EGRESS),
            health_check_grace_period=Duration.minutes(6),
            circuit_breaker=aws_ecs.DeploymentCircuitBreaker(enable=True, rollback=True),
            min_healthy_percent=100,
            max_healthy_percent=250,
            cpu=1024,
            memory_limit_mib=2048)
        service.target_group.configure_health_check(path="/api/v1/healthcheck/", port="8000")
        service.task_definition.task_role.attach_inline_policy(aws_iam.Policy(self, "CustomerSecretsRW", document=aws_iam.PolicyDocument(statements=[
            aws_iam.PolicyStatement(
                effect=aws_iam.Effect.ALLOW,
                actions=["secretsmanager:CreateSecret", "secretsmanager:ListSecrets", "secretsmanager:DescribeSecret"],
                resources=[f"arn:aws:secretsmanager:{Stack.of(self).region}:{Stack.of(self).account}:secret:DRIVER_AI_CUSTOMER/*"]
            )
        ])))
        waf_visibility_config_ips = aws_wafv2.CfnWebACL.VisibilityConfigProperty(cloud_watch_metrics_enabled=True, metric_name="MetricForWebACLCDK-IPs", sampled_requests_enabled=True)
        waf_visibility_config = aws_wafv2.CfnWebACL.VisibilityConfigProperty(cloud_watch_metrics_enabled=True, metric_name="MetricForWebACLCDK", sampled_requests_enabled=True)
        waf_visibility_config_crs = aws_wafv2.CfnWebACL.VisibilityConfigProperty(cloud_watch_metrics_enabled=True, metric_name="MetricForWebACLCDK-CRS", sampled_requests_enabled=True)
        waf_rule_overrides = [
            aws_wafv2.CfnWebACL.RuleActionOverrideProperty(name="SizeRestrictions_BODY", action_to_use=aws_wafv2.CfnWebACL.RuleActionProperty(allow={})),
            aws_wafv2.CfnWebACL.RuleActionOverrideProperty(name="SizeRestrictions_URIPATH", action_to_use=aws_wafv2.CfnWebACL.RuleActionProperty(allow={})),
            aws_wafv2.CfnWebACL.RuleActionOverrideProperty(name="SizeRestrictions_QUERYSTRING", action_to_use=aws_wafv2.CfnWebACL.RuleActionProperty(allow={})),
            aws_wafv2.CfnWebACL.RuleActionOverrideProperty(name="GenericLFI_BODY", action_to_use=aws_wafv2.CfnWebACL.RuleActionProperty(allow={})),
            aws_wafv2.CfnWebACL.RuleActionOverrideProperty(name="GenericRFI_BODY", action_to_use=aws_wafv2.CfnWebACL.RuleActionProperty(allow={})),
        ]
        waf_rule_statement = aws_wafv2.CfnWebACL.StatementProperty(managed_rule_group_statement=aws_wafv2.CfnWebACL.ManagedRuleGroupStatementProperty(name="AWSManagedRulesCommonRuleSet", vendor_name="AWS", rule_action_overrides=waf_rule_overrides))
        crs_rule = aws_wafv2.CfnWebACL.RuleProperty(name="CRSRule", priority=1, statement=waf_rule_statement, visibility_config=waf_visibility_config_crs, override_action=aws_wafv2.CfnWebACL.OverrideActionProperty(none={}))
        waf_rules = [crs_rule]
        if len(params.allowed_ips) > 0:
            whitelist_ip_set = aws_wafv2.CfnIPSet(self, "WhitelistIPs", ip_address_version="IPV4", scope="REGIONAL", addresses=params.allowed_ips)
            ipset_rule_statement = aws_wafv2.CfnWebACL.StatementProperty(ip_set_reference_statement=aws_wafv2.CfnWebACL.IPSetReferenceStatementProperty(arn=whitelist_ip_set.attr_arn))
            n = aws_wafv2.CfnWebACL.NotStatementProperty(statement=ipset_rule_statement)
            ipset_rule = aws_wafv2.CfnWebACL.RuleProperty(name="AllowedIPs", priority=0, statement=aws_wafv2.CfnWebACL.StatementProperty(not_statement=n), visibility_config=waf_visibility_config_ips, action=aws_wafv2.CfnWebACL.RuleActionProperty(block={}))
            # waf_rules.append(ipset_rule)            

        waf = aws_wafv2.CfnWebACL(self, "PythonBackendWAF", scope='REGIONAL', default_action=aws_wafv2.CfnWebACL.DefaultActionProperty(allow={}), visibility_config=waf_visibility_config, rules=waf_rules)
        waf_association = aws_wafv2.CfnWebACLAssociation(self, 'WebACLALBAssociation', resource_arn=service.load_balancer.load_balancer_arn, web_acl_arn=waf.attr_arn)
