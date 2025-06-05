# Purpose
This Python code defines a construct for deploying an AWS Lambda function using the AWS Cloud Development Kit (CDK). The primary purpose of this file is to set up an infrastructure component that facilitates asset onboarding through a Lambda function, which is triggered by events from an SNS topic and interacts with S3 buckets. The `AssetOnboardingLambda` class is a custom construct that encapsulates the configuration and deployment of a Lambda function, including its environment variables, permissions, and event sources. It uses several AWS services such as IAM for permissions, Secrets Manager for managing sensitive information, and S3 for storage and event notifications.

The code is structured to be part of a larger infrastructure-as-code setup, likely intended to be imported and used within a broader CDK application. It defines a public API through the `AssetOnboardingLambda` class, which takes parameters encapsulated in the `AssetOnboardingLambdaParams` dataclass. This setup allows for flexible configuration of the Lambda function's environment and behavior. The code also includes outputs for the secrets used by the Lambda function, making them accessible for other parts of the infrastructure. The use of AWS managed policies and the note about scoping down privileges indicate a focus on security and best practices in managing AWS resources.
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
    - `scope`: The scope in which this construct is defined.
    - `id`: The unique identifier for this construct.
    - `params`: Parameters for configuring the AssetOnboardingLambda, encapsulated in AssetOnboardingLambdaParams.
- **Description**: The AssetOnboardingLambda class is a construct that sets up an AWS Lambda function for asset onboarding, integrating with AWS Secrets Manager, SNS, and S3. It creates secrets for client ID and secret, configures a Python-based Lambda function with specific environment variables, and sets up event sources and permissions. The class also manages SNS topics for event notifications and outputs the secret names for further use. It is designed to handle asset onboarding events and requires specific AWS resources and permissions to function correctly.
- **Inherits From**:
    - Construct

**Methods**

---
#### AssetOnboardingLambda.__init__
The `__init__` function initializes an AWS CDK construct for an asset onboarding Lambda function, setting up necessary AWS resources and permissions.
- **Inputs**:
    - `scope`: A Construct object that defines the scope in which this construct is defined.
    - `id`: A string identifier for this construct.
    - `params`: An instance of AssetOnboardingLambdaParams containing configuration parameters such as environment, API URLs, and bucket information.
- **Control Flow**:
    - Call the superclass constructor with the provided scope and id.
    - Create AWS Secrets Manager secrets for client ID and client secret using the provided CDK prefix.
    - Define a Python Lambda function with specified entry point, runtime, environment variables, and bundling options.
    - Grant read permissions to the Lambda function for the created secrets and the provided dropzone bucket.
    - Create an SNS topic and add it as an event source to the Lambda function.
    - Attach an Amazon S3 full access managed policy to the Lambda function's role.
    - Retrieve a legacy dropzone bucket by name and add an event notification for object creation, linking it to the SNS topic.
    - Grant read permissions to the Lambda function for the legacy dropzone bucket.
    - Create CloudFormation outputs for the client ID and client secret secret names.
- **Output**:
    - The function does not return any value; it sets up AWS resources and permissions as part of the construct initialization.



---
### AssetOnboardingLambdaParams 
- **Type**: `dataclass`
- **Members**:
    - `environment`: Specifies the environment in which the lambda function operates.
    - `api_url`: Holds the URL for the API endpoint.
    - `auth0_url`: Contains the URL for the Auth0 authentication service.
    - `dropzone_bucket`: References an AWS S3 bucket used as the dropzone for assets.
    - `use_legacy_dropzone`: Indicates whether to use the legacy dropzone setup.
    - `cdk_prefix`: Provides a prefix for naming AWS CDK resources.
- **Description**: The `AssetOnboardingLambdaParams` class is a data structure that encapsulates configuration parameters required for setting up an asset onboarding lambda function. It includes details such as the environment, API and Auth0 URLs, the S3 bucket used for asset dropzone, a flag for using legacy dropzone, and a prefix for AWS CDK resource naming. This class is used to pass configuration settings to the `AssetOnboardingLambda` construct.


