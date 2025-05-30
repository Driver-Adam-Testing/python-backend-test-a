# Purpose
This Python code defines a construct for deploying an AWS Lambda function using the AWS Cloud Development Kit (CDK). The primary purpose of this file is to set up an AWS Lambda function, `AssetOnboardingLambda`, which is designed to handle asset onboarding events. The code leverages several AWS services, including IAM for permissions, S3 for storage, Secrets Manager for managing sensitive information, and SNS for event notifications. The `AssetOnboardingLambdaParams` dataclass is used to encapsulate configuration parameters required for the Lambda function, such as environment settings and URLs.

The `AssetOnboardingLambda` class is a CDK construct that encapsulates the creation and configuration of the Lambda function. It sets up the function's environment variables, manages its dependencies, and configures event sources and permissions. The Lambda function is triggered by SNS events and has permissions to read from S3 buckets, including a legacy dropzone bucket. The code also includes a note about the need to refine IAM permissions, indicating that the current setup grants broad S3 access, which may need to be scoped down for security reasons. This file is intended to be part of a larger infrastructure-as-code setup, facilitating the deployment and management of cloud resources in a consistent and automated manner.
# Imports and Dependencies

---
- `dataclasses`
- `aws_cdk`
- `constructs`


# Classes

---
### AssetOnboardingLambda 
- **Type**: `class`
- **Members**:
    - `client_id_secret`: An AWS Secrets Manager secret for storing the client ID.
    - `client_secret_secret`: An AWS Secrets Manager secret for storing the client secret.
    - `lambda_function`: A Python-based AWS Lambda function for handling asset onboarding events.
    - `sns_topic`: An SNS topic used to trigger the Lambda function via SNS events.
    - `legacy_dropzone_bucket`: An S3 bucket used for legacy dropzone operations, with event notifications configured.
- **Description**: The `AssetOnboardingLambda` class is a construct that sets up an AWS Lambda function for handling asset onboarding events. It configures the Lambda function with necessary environment variables, secrets, and permissions, and integrates it with an SNS topic for event-driven execution. The class also manages access to S3 buckets, including a legacy dropzone bucket, and grants the Lambda function necessary read permissions. Additionally, it applies a managed policy to the Lambda function's role to allow full access to S3, although there is a note indicating a need to refine these permissions.
- **Inherits From**:
    - Construct

**Methods**

---
#### AssetOnboardingLambda.__init__
The `__init__` function initializes an `AssetOnboardingLambda` construct, setting up AWS resources such as Lambda functions, Secrets Manager secrets, SNS topics, and S3 bucket notifications for asset onboarding.
- **Inputs**:
    - `scope`: A `Construct` object that defines the scope in which this construct is created.
    - `id`: A string that serves as the unique identifier for this construct within the scope.
    - `params`: An `AssetOnboardingLambdaParams` object containing configuration parameters such as environment, API URLs, and S3 bucket references.
- **Control Flow**:
    - Call the superclass `__init__` method to initialize the base `Construct` class with `scope` and `id`.
    - Create two AWS Secrets Manager secrets for client ID and client secret.
    - Define a Python-based AWS Lambda function with specified entry point, runtime, and environment variables, including secrets and URLs from `params`.
    - Exclude certain files and directories from the Lambda function bundle and set a timeout of 15 seconds.
    - Grant read permissions on the secrets and the `dropzone_bucket` to the Lambda function.
    - Create an SNS topic and add it as an event source to the Lambda function.
    - Attach the `AmazonS3FullAccess` managed policy to the Lambda function's role to allow S3 operations.
    - Retrieve a legacy S3 bucket by name and set up an event notification for object tagging, sending notifications to the SNS topic.
    - Grant read permissions on the legacy S3 bucket to the Lambda function.
- **Output**:
    - The function does not return any value; it sets up AWS resources and permissions as part of the construct initialization.



---
### AssetOnboardingLambdaParams 
- **Type**: `dataclass`
- **Members**:
    - `environment`: Specifies the environment in which the lambda function operates.
    - `api_url`: Holds the URL for the API endpoint.
    - `auth0_url`: Contains the URL for the Auth0 authentication service.
    - `dropzone_bucket`: References an AWS S3 bucket used as the dropzone.
    - `use_legacy_dropzone`: Indicates whether to use the legacy dropzone bucket.
- **Description**: The `AssetOnboardingLambdaParams` class is a data structure that encapsulates configuration parameters required for setting up an asset onboarding lambda function. It includes details about the environment, API and Auth0 URLs, the S3 bucket used for the dropzone, and a flag to determine if a legacy dropzone should be used. This class is used to pass configuration settings to the `AssetOnboardingLambda` construct.


