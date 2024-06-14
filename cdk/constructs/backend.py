from aws_cdk import (
    aws_elasticloadbalancingv2,
    aws_secretsmanager,
    aws_ecs,
    aws_ecs_patterns,
    aws_ec2,
    aws_ssm,
    aws_route53,
    aws_wafv2,
    Duration
)
from constructs import Construct

# TODO: parameterize task count and container size
class BackendParams:
    cors_origins: str
    def __init__(self, cors_origins):
        self.cors_origins = cors_origins
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

        container_environment_vars = {
            "BACKEND_CORS_ORIGINS": params.cors_origins,
            "PORT": "8888",
            "PROJECT_NAME": "DriverAI API"
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
        }
        
        task_image = aws_ecs.ContainerImage.from_asset(".", asset_name="python-backend")
        task_options = aws_ecs_patterns.ApplicationLoadBalancedTaskImageOptions(image=task_image, secrets=container_secrets, environment=container_environment_vars, container_port=8888)
        service = aws_ecs_patterns.ApplicationLoadBalancedFargateService(self, "BackendApi",\
            protocol=aws_elasticloadbalancingv2.ApplicationProtocol.HTTPS,\
            platform_version=aws_ecs.FargatePlatformVersion.LATEST,\
            runtime_platform=aws_ecs.RuntimePlatform(cpu_architecture=aws_ecs.CpuArchitecture.ARM64),\
            redirect_http=True,\
            assign_public_ip=False,\
            desired_count=2,\
            cluster=cluster,\
            domain_zone=hosted_zone,\
            domain_name="api." + hosted_zone.zone_name,\
            task_image_options=task_options,\
            task_subnets=aws_ec2.SubnetSelection(subnet_type=aws_ec2.SubnetType.PRIVATE_WITH_EGRESS),\
            health_check_grace_period=Duration.minutes(2))
        service.target_group.configure_health_check(path="/api/v1/healthcheck/", port="8888")

        waf_visibility_config = aws_wafv2.CfnWebACL.VisibilityConfigProperty(cloud_watch_metrics_enabled=True, metric_name="MetricForWebACLCDK", sampled_requests_enabled=True)
        waf_visibility_config_crs = aws_wafv2.CfnWebACL.VisibilityConfigProperty(cloud_watch_metrics_enabled=True, metric_name="MetricForWebACLCDK-CRS", sampled_requests_enabled=True)
        waf_rule_overrides = [\
            aws_wafv2.CfnWebACL.RuleActionOverrideProperty(name="SizeRestrictions_BODY", action_to_use=aws_wafv2.CfnWebACL.RuleActionProperty(allow={})),\
            aws_wafv2.CfnWebACL.RuleActionOverrideProperty(name="SizeRestrictions_URIPATH", action_to_use=aws_wafv2.CfnWebACL.RuleActionProperty(allow={})),\
            aws_wafv2.CfnWebACL.RuleActionOverrideProperty(name="SizeRestrictions_QUERYSTRING", action_to_use=aws_wafv2.CfnWebACL.RuleActionProperty(allow={})),\
            aws_wafv2.CfnWebACL.RuleActionOverrideProperty(name="GenericLFI_BODY", action_to_use=aws_wafv2.CfnWebACL.RuleActionProperty(allow={})),\
            aws_wafv2.CfnWebACL.RuleActionOverrideProperty(name="GenericRFI_BODY", action_to_use=aws_wafv2.CfnWebACL.RuleActionProperty(allow={})),\
        ]
        waf_rule_statement = aws_wafv2.CfnWebACL.StatementProperty(managed_rule_group_statement=aws_wafv2.CfnWebACL.ManagedRuleGroupStatementProperty(name="AWSManagedRulesCommonRuleSet", vendor_name="AWS", rule_action_overrides=waf_rule_overrides))
        waf_rules = [aws_wafv2.CfnWebACL.RuleProperty(name="CRSRule", priority=0, statement=waf_rule_statement, visibility_config=waf_visibility_config_crs, override_action=aws_wafv2.CfnWebACL.OverrideActionProperty(none={}))]

        waf = aws_wafv2.CfnWebACL(self, "PythonBackendWAF", scope='REGIONAL', default_action=aws_wafv2.CfnWebACL.DefaultActionProperty(allow={}), visibility_config=waf_visibility_config, rules=waf_rules)
        waf_association = aws_wafv2.CfnWebACLAssociation(self, 'WebACLALBAssociation', resource_arn=service.load_balancer.load_balancer_arn, web_acl_arn=waf.attr_arn)
