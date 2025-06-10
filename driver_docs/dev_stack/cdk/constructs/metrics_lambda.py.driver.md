# Purpose
This Python code defines a construct for deploying a serverless application using the AWS Cloud Development Kit (CDK). The primary purpose of this file is to set up a Lambda function that processes metrics, along with the necessary infrastructure components such as a VPC, event bus, and alarms for monitoring. The `MetricsLambda` class, which extends the `Construct` class, encapsulates the creation and configuration of these AWS resources. It includes a Lambda function written in Python, which is deployed within a specified VPC and configured with environment variables and bundling options. The construct also sets up an Amazon SQS dead-letter queue (DLQ) for handling failed message processing and an Amazon EventBridge event bus to route events to the Lambda function.

Additionally, the code configures CloudWatch alarms to monitor the health and performance of the system, such as the number of undelivered messages in the DLQ, the age of messages in the DLQ, and the error rate of the Lambda function. These alarms can trigger notifications via Amazon SNS if a specified ARN is provided. The use of data classes for parameter management and the integration of AWS Secrets Manager for secure handling of database URLs further enhance the robustness and security of the deployment. This file is intended to be part of a larger infrastructure-as-code setup, providing a reusable and configurable component for managing metrics processing in an AWS environment.
# Imports and Dependencies

---
- `os`
- `dataclasses`
- `aws_cdk`
- `constructs`


# Global Variables

---
### cloudwatch_alarm_arn 
- **Type**: `Optional[str]`
- **Description**: The `cloudwatch_alarm_arn` is an optional string variable that holds the Amazon Resource Name (ARN) of a CloudWatch alarm. It is part of the `MetricsLambdaParams` dataclass, which is used to configure parameters for the `MetricsLambda` construct.
- **Use**: This variable is used to specify the ARN of a CloudWatch alarm for sending notifications via SNS when certain conditions are met in the `MetricsLambda` construct.


---
### database_url 
- **Type**: `string`
- **Description**: The `database_url` variable is a string that represents the URL of the database used by the MetricsLambda construct. It is part of the `MetricsLambdaParams` dataclass, which is used to configure the environment and other parameters for the MetricsLambda construct.
- **Use**: This variable is used to set the `DATABASE_URL` environment variable for the AWS Lambda function within the MetricsLambda construct.


# Classes

---
### MetricsLambda 
- **Type**: `class`
- **Members**:
    - `lambda_function`: An AWS Lambda function configured with specific runtime, environment variables, and bundling options.
    - `metrics_dlq`: An SQS queue used as a dead-letter queue for the event bus.
    - `metrics_bus`: An AWS EventBus configured to handle events with a specific pattern and dead-letter queue.
    - `metrics_rule`: An AWS EventBridge rule that triggers the Lambda function based on specific event patterns.
    - `metric_dlq_alarm`: A CloudWatch alarm monitoring the number of undelivered messages in the DLQ.
    - `metric_message_age_alarm`: A CloudWatch alarm monitoring the age of the oldest message in the DLQ.
    - `lambda_error_rate_alarm`: A CloudWatch alarm monitoring the error rate of the Lambda function.
- **Description**: The `MetricsLambda` class is a construct that sets up an AWS Lambda function to process metrics, along with associated AWS resources such as an EventBridge event bus, SQS dead-letter queue, and CloudWatch alarms. It configures the Lambda function with specific environment variables and bundling options, and sets up event rules to trigger the function based on certain patterns. Additionally, it includes alarms to monitor the health and performance of the Lambda function and the event processing pipeline, with optional SNS notifications for alarm actions.
- **Inherits From**:
    - Construct

**Methods**

---
#### MetricsLambda.__init__
The `__init__` function initializes a `MetricsLambda` construct, setting up AWS resources such as a Lambda function, event bus, alarms, and secret management for metrics processing.
- **Inputs**:
    - `scope`: A `Construct` object that defines the scope in which this construct is created.
    - `id`: A string that serves as the unique identifier for this construct.
    - `params`: An instance of `MetricsLambdaParams` containing configuration parameters such as environment, CDK prefix, database URL, and CloudWatch alarm ARN.
- **Control Flow**:
    - Call the superclass `__init__` method to initialize the base construct.
    - Create a secret in AWS Secrets Manager for the database URL using the CDK prefix from `params`.
    - Retrieve the VPC ID from AWS SSM Parameter Store and use it to look up the VPC.
    - Determine the absolute path to the driver database and print it.
    - Create a Python Lambda function with specified configurations, including VPC settings, environment variables, and bundling options.
    - Grant the Lambda function read access to the database URL secret.
    - Create an SQS queue for the dead-letter queue (DLQ).
    - Create an EventBus and associate it with the DLQ, using the stack name and environment from `params`.
    - Create an EventBridge rule to trigger the Lambda function based on events from the EventBus.
    - If the environment is 'development', 'staging', or 'production', set up CloudWatch alarms for DLQ message count, message age, and Lambda error rate.
    - If a CloudWatch alarm ARN is provided, add SNS actions to the alarms for notifications; otherwise, print a warning message.
    - Create a CloudFormation output for the database URL secret name.
- **Output**:
    - The function does not return any value; it sets up AWS resources and configurations as part of the construct initialization.



---
### MetricsLambdaParams 
- **Type**: `dataclass`
- **Members**:
    - `environment`: Specifies the environment in which the lambda function is deployed.
    - `cdk_prefix`: A prefix used for naming resources in AWS CDK.
    - `database_url`: Optional URL for the database connection.
    - `cloudwatch_alarm_arn`: Optional ARN for a CloudWatch alarm to notify on certain events.
- **Description**: The `MetricsLambdaParams` class is a data structure used to encapsulate configuration parameters for deploying a metrics-related AWS Lambda function. It includes essential information such as the deployment environment, a prefix for AWS CDK resource naming, and optional parameters for database connectivity and CloudWatch alarm notifications. This class is designed to be used as a parameter object when initializing instances of the `MetricsLambda` class, providing a structured way to pass configuration data.


