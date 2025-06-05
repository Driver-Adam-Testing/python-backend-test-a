# Purpose
This Python code defines a module that integrates AWS Web Application Firewall (WAF) with an Application Load Balanced Fargate Service using the AWS Cloud Development Kit (CDK). The primary purpose of this code is to create and configure a WAF to protect a web application deployed on AWS Fargate. The `AwsWAF` class, which inherits from the `Construct` class, is the central component of this module. It sets up a WAF with specific visibility configurations and rule overrides, including managed rule groups from AWS and custom IP whitelisting. The WAF is then associated with the load balancer of the Fargate service, ensuring that incoming traffic is filtered according to the defined security rules.

The code is structured to be part of a larger infrastructure-as-code setup, likely intended to be imported and used within a broader AWS CDK application. It does not define a standalone script but rather a reusable construct that can be integrated into AWS infrastructure projects. The `AwsWAFParams` class is used to pass parameters, such as the Fargate service to be protected, into the `AwsWAF` construct. This design allows for flexibility and reusability, enabling developers to easily apply WAF protection to different services by providing the necessary parameters. The code also includes placeholders for future enhancements, such as re-enabling certain rules once application endpoints are refactored.
# Imports and Dependencies

---
- `aws_cdk.aws_ecs_patterns`
- `aws_cdk.aws_wafv2`
- `constructs.Construct`


# Classes

---
### AwsWAF 
- **Type**: `class`
- **Members**:
    - `waf_visibility_config_ips`: Configuration for WAF visibility specific to IPs.
    - `waf_visibility_config`: General configuration for WAF visibility.
    - `waf_visibility_config_crs`: Configuration for WAF visibility specific to CRS rules.
    - `waf_rule_overrides`: List of rule action overrides for specific WAF rules.
    - `waf_rule_statement`: Statement property for managed rule group with overrides.
    - `crs_rule`: Rule property for CRS with specific priority and statement.
    - `waf_rules`: List of WAF rules to be applied.
    - `waf`: CfnWebACL instance representing the WAF configuration.
    - `waf_association`: Associates the WAF with a specific resource.
- **Description**: The AwsWAF class is a construct that sets up an AWS Web Application Firewall (WAF) using AWS CDK. It configures visibility settings, rule action overrides, and manages rule groups to protect an application load-balanced Fargate service. The class allows for the specification of allowed IPs and associates the WAF with a load balancer, providing a regional scope for the WAF rules and default actions.
- **Inherits From**:
    - Construct

**Methods**

---
#### AwsWAF.__init__
The `__init__` function initializes an AWS WAF (Web Application Firewall) configuration for a given AWS CDK construct, setting up visibility configurations, rule overrides, and associating the WAF with an application load balancer.
- **Inputs**:
    - `scope`: A `Construct` object that represents the scope in which this construct is defined.
    - `id`: A string that serves as the unique identifier for this construct within its scope.
    - `params`: An `AwsWAFParams` object containing parameters for the WAF, including the service to be protected and allowed IPs.
- **Control Flow**:
    - Call the superclass `__init__` method to initialize the base `Construct` class with `scope` and `id`.
    - Define three visibility configurations for the WAF, each with metrics enabled and specific metric names.
    - Create a list of rule action overrides for specific WAF rules, allowing certain actions.
    - Define a managed rule group statement using the AWS Managed Rules Common Rule Set with the specified rule action overrides.
    - Create a rule property `crs_rule` with the managed rule group statement and visibility configuration, and add it to the `waf_rules` list.
    - Check if there are any allowed IPs in `params.allowed_ips`; if so, create an IP set and a corresponding rule to block requests not from these IPs, but this rule is commented out and not added to `waf_rules`.
    - Instantiate a `CfnWebACL` object with the defined rules and visibility configuration, allowing all requests by default.
    - Associate the created WAF with the application load balancer using `CfnWebACLAssociation`.
- **Output**:
    - The function does not return any value; it sets up the WAF configuration and association as a side effect.



---
### AwsWAFParams 
- **Type**: `class`
- **Members**:
    - `service`: An instance of ApplicationLoadBalancedFargateService from aws_ecs_patterns.
- **Description**: The AwsWAFParams class is a simple container for holding a reference to an AWS ECS ApplicationLoadBalancedFargateService. It is used to pass this service instance to other components, such as the AwsWAF class, which configures AWS WAF (Web Application Firewall) settings for the service. This class primarily serves as a parameter object to facilitate the association of a WAF with a specific ECS service.

**Methods**

---
#### AwsWAFParams.__init__
The `__init__` function initializes an instance of the `AwsWAFParams` class by setting the `service` attribute.
- **Inputs**:
    - `service`: An instance of `aws_ecs_patterns.ApplicationLoadBalancedFargateService` that is assigned to the `service` attribute of the `AwsWAFParams` instance.
- **Control Flow**:
    - The function takes a single parameter `service`.
    - The `service` parameter is assigned to the `service` attribute of the `AwsWAFParams` instance.
- **Output**:
    - The function does not return any value; it initializes the `service` attribute of the `AwsWAFParams` instance.



