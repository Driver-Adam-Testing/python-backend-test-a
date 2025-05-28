# Purpose
This Python code defines a module that leverages the AWS Cloud Development Kit (CDK) to set up a serverless infrastructure for processing metrics using AWS Lambda, EventBridge, and other AWS services. The primary class, `MetricsLambda`, is a construct that encapsulates the creation and configuration of an AWS Lambda function designed to handle metric events. It integrates with AWS Secrets Manager to manage database credentials, AWS SSM for retrieving VPC information, and AWS SQS for handling dead-letter queues. The Lambda function is configured to run in a specified VPC and is set up with specific environment variables and bundling options to ensure it operates correctly within the AWS environment.

Additionally, the module sets up CloudWatch alarms to monitor the health and performance of the metrics processing system. These alarms are configured to trigger based on specific conditions, such as the number of undelivered messages in the dead-letter queue or the age of messages, and can send notifications via SNS if a CloudWatch alarm ARN is provided. This code is intended to be part of a larger infrastructure-as-code setup, providing a reusable and configurable component for managing metric processing in different environments like development, staging, and production.
# Imports and Dependencies

---
- `os`
- `aws_cdk.Duration`
- `aws_cdk.aws_cloudwatch`
- `aws_cdk.aws_cloudwatch_actions`
- `aws_cdk.aws_ec2`
- `aws_cdk.aws_events`
- `aws_cdk.aws_lambda`
- `aws_cdk.aws_lambda_python_alpha`
- `aws_cdk.aws_secretsmanager`
- `aws_cdk.aws_sns`
- `aws_cdk.aws_sqs`
- `aws_cdk.aws_ssm`
- `aws_cdk.aws_events_targets`
- `constructs.Construct`


# Classes

---
### MetricsLambda 
- **Type**: `class`
- **Members**:
    - `lambda_function`: An AWS Lambda function configured with specific runtime, environment variables, and bundling options.
    - `metrics_dlq`: An SQS queue used as a dead-letter queue for the event bus.
    - `metrics_bus`: An EventBus for handling metrics events with a dead-letter queue.
    - `metrics_rule`: An EventBridge rule that triggers the Lambda function based on specific event patterns.
    - `metric_dlq_alarm`: A CloudWatch alarm monitoring the number of undelivered messages in the DLQ.
    - `metric_message_age_alarm`: A CloudWatch alarm monitoring the age of the oldest message in the DLQ.
    - `lambda_error_rate_alarm`: A CloudWatch alarm monitoring the error rate of the Lambda function.
- **Description**: The `MetricsLambda` class is a construct that sets up an AWS Lambda function to process metrics events, along with associated infrastructure such as an EventBridge event bus, SQS dead-letter queue, and CloudWatch alarms for monitoring. It configures the Lambda function with specific runtime and environment settings, and sets up alarms to monitor the health and performance of the event processing pipeline, including message delivery and error rates. The class also supports notification actions for alarms if a CloudWatch alarm ARN is provided.
- **Inherits From**:
    - Construct

**Methods**

---
#### MetricsLambda.__init__
The `__init__` function initializes a `MetricsLambda` construct, setting up a Lambda function, event bus, alarms, and related AWS resources for monitoring and handling metrics.
- **Inputs**:
    - `scope`: A `Construct` object that defines the scope in which this construct is created.
    - `id`: A string that serves as the unique identifier for this construct.
    - `params`: An instance of `MetricsLambdaParams` containing configuration parameters such as environment, database URL, and CloudWatch alarm ARN.
- **Control Flow**:
    - The function begins by calling the superclass constructor with `scope` and `id`.
    - A secret for the database URL is created using AWS Secrets Manager.
    - The VPC ID is retrieved from AWS SSM Parameter Store, and a VPC object is created using this ID.
    - The absolute path to the `driver_db` directory is determined.
    - A Python Lambda function is created with specified configurations, including VPC settings, environment variables, and bundling options.
    - The Lambda function is granted read access to the database URL secret.
    - An event target is created for the Lambda function, and an SQS dead-letter queue is set up.
    - An event bus is created with the dead-letter queue, and a rule is set up to trigger the Lambda function based on specific event patterns.
    - If the environment is 'development', 'staging', or 'production', CloudWatch alarms are created for DLQ message count, message age, and Lambda error rate.
    - If a CloudWatch alarm ARN is provided, SNS actions are added to the alarms for notifications; otherwise, a warning message is printed.
- **Output**:
    - The function does not return any value; it initializes the `MetricsLambda` construct with all necessary AWS resources and configurations.



---
### MetricsLambdaParams 
- **Type**: `class`
- **Members**:
    - `environment`: The environment in which the metrics lambda is running.
    - `database_url`: The URL of the database, which can be None if not provided.
    - `cloudwatch_alarm_arn`: The ARN of the CloudWatch alarm, which can be None if not provided.
- **Description**: The `MetricsLambdaParams` class is a simple data holder for parameters required to configure a metrics lambda function. It includes the environment, an optional database URL, and an optional CloudWatch alarm ARN. This class is used to encapsulate configuration details that are passed to the `MetricsLambda` class for setting up the lambda function and its associated resources.

**Methods**

---
#### MetricsLambdaParams.__init__
The `__init__` function initializes an instance of the `MetricsLambdaParams` class with environment, database URL, and CloudWatch alarm ARN attributes.
- **Inputs**:
    - `environment`: A string representing the environment in which the metrics lambda is operating, such as 'development', 'staging', or 'production'.
    - `database_url`: An optional string representing the URL of the database; defaults to None if not provided.
    - `cloudwatch_alarm_arn`: An optional string representing the Amazon Resource Name (ARN) of a CloudWatch alarm; defaults to None if not provided.
- **Control Flow**:
    - The function assigns the provided 'environment' argument to the instance's 'environment' attribute.
    - The function assigns the provided 'database_url' argument to the instance's 'database_url' attribute, which can be None if not provided.
    - The function assigns the provided 'cloudwatch_alarm_arn' argument to the instance's 'cloudwatch_alarm_arn' attribute, which can be None if not provided.
- **Output**:
    - The function does not return any value; it initializes the instance attributes.



