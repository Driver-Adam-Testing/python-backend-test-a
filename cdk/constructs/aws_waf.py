from aws_cdk import aws_ecs_patterns, aws_wafv2
from constructs import Construct


class AwsWAFParams:
    service: aws_ecs_patterns.ApplicationLoadBalancedFargateService

    def __init__(self, service):
        self.service = service


class AwsWAF(Construct):
    def __init__(self, scope: Construct, id: str, params: AwsWAFParams):
        super().__init__(scope, id)

        waf_visibility_config_ips = aws_wafv2.CfnWebACL.VisibilityConfigProperty(
            cloud_watch_metrics_enabled=True,
            metric_name="MetricForWebACLCDK-IPs",
            sampled_requests_enabled=True,
        )
        waf_visibility_config = aws_wafv2.CfnWebACL.VisibilityConfigProperty(
            cloud_watch_metrics_enabled=True,
            metric_name="MetricForWebACLCDK",
            sampled_requests_enabled=True,
        )
        waf_visibility_config_crs = aws_wafv2.CfnWebACL.VisibilityConfigProperty(
            cloud_watch_metrics_enabled=True,
            metric_name="MetricForWebACLCDK-CRS",
            sampled_requests_enabled=True,
        )
        # TODO - re-enable when endpoints have been refactored not to send entire app notes
        waf_rule_overrides = [
            aws_wafv2.CfnWebACL.RuleActionOverrideProperty(
                name="SizeRestrictions_BODY",
                action_to_use=aws_wafv2.CfnWebACL.RuleActionProperty(allow={}),
            ),
            aws_wafv2.CfnWebACL.RuleActionOverrideProperty(
                name="SizeRestrictions_URIPATH",
                action_to_use=aws_wafv2.CfnWebACL.RuleActionProperty(allow={}),
            ),
            aws_wafv2.CfnWebACL.RuleActionOverrideProperty(
                name="SizeRestrictions_QUERYSTRING",
                action_to_use=aws_wafv2.CfnWebACL.RuleActionProperty(allow={}),
            ),
            aws_wafv2.CfnWebACL.RuleActionOverrideProperty(
                name="GenericLFI_BODY",
                action_to_use=aws_wafv2.CfnWebACL.RuleActionProperty(allow={}),
            ),
            aws_wafv2.CfnWebACL.RuleActionOverrideProperty(
                name="GenericRFI_BODY",
                action_to_use=aws_wafv2.CfnWebACL.RuleActionProperty(allow={}),
            ),
        ]
        waf_rule_statement = aws_wafv2.CfnWebACL.StatementProperty(
            managed_rule_group_statement=aws_wafv2.CfnWebACL.ManagedRuleGroupStatementProperty(
                name="AWSManagedRulesCommonRuleSet",
                vendor_name="AWS",
                rule_action_overrides=waf_rule_overrides,
            )
        )
        crs_rule = aws_wafv2.CfnWebACL.RuleProperty(
            name="CRSRule",
            priority=1,
            statement=waf_rule_statement,
            visibility_config=waf_visibility_config_crs,
            override_action=aws_wafv2.CfnWebACL.OverrideActionProperty(none={}),
        )
        waf_rules = [crs_rule]
        if len(params.allowed_ips) > 0:
            whitelist_ip_set = aws_wafv2.CfnIPSet(
                self,
                "WhitelistIPs",
                ip_address_version="IPV4",
                scope="REGIONAL",
                addresses=params.allowed_ips,
            )
            ipset_rule_statement = aws_wafv2.CfnWebACL.StatementProperty(
                ip_set_reference_statement=aws_wafv2.CfnWebACL.IPSetReferenceStatementProperty(
                    arn=whitelist_ip_set.attr_arn
                )
            )
            n = aws_wafv2.CfnWebACL.NotStatementProperty(statement=ipset_rule_statement)
            ipset_rule = aws_wafv2.CfnWebACL.RuleProperty(
                name="AllowedIPs",
                priority=0,
                statement=aws_wafv2.CfnWebACL.StatementProperty(not_statement=n),
                visibility_config=waf_visibility_config_ips,
                action=aws_wafv2.CfnWebACL.RuleActionProperty(block={}),
            )
            # waf_rules.append(ipset_rule)

        waf = aws_wafv2.CfnWebACL(
            self,
            "PythonBackendWAF",
            scope="REGIONAL",
            default_action=aws_wafv2.CfnWebACL.DefaultActionProperty(allow={}),
            visibility_config=waf_visibility_config,
            rules=waf_rules,
        )
        waf_association = aws_wafv2.CfnWebACLAssociation(
            self,
            "WebACLALBAssociation",
            resource_arn=self.service.load_balancer.load_balancer_arn,
            web_acl_arn=waf.attr_arn,
        )
