# Purpose
This Python code defines a Cloud Development Kit (CDK) stack, specifically designed for development and testing purposes. The `DevStack` class, which inherits from the `Stack` class provided by AWS CDK, is used to deploy additional infrastructure alongside existing development resources. The stack is intended for temporary use, as indicated by the comment suggesting it may be deleted after its purpose is fulfilled. The primary components of this stack include an Amazon S3 bucket and two AWS Lambda functions, each serving distinct roles within the infrastructure.

The S3 bucket, named `asset_dropzone_bucket`, is configured with specific properties such as automatic deletion of objects, public access blocking, and server-side encryption. It also supports CORS (Cross-Origin Resource Sharing) to allow interactions from specified origins. The stack further integrates two Lambda functions: `AssetOnboardingLambda` and `MetricsLambda`. These functions are instantiated with parameters that include environment-specific configurations and URLs retrieved from environment variables. The `AssetOnboardingLambda` is associated with the S3 bucket, indicating its role in processing assets uploaded to the bucket, while the `MetricsLambda` is likely involved in collecting or processing metrics, as suggested by its name and the inclusion of a database URL in its parameters. Overall, this code provides a narrowly focused infrastructure setup for development and testing, leveraging AWS services to facilitate asset management and metrics collection.
# Imports and Dependencies

---
- `os`
- `dataclasses`
- `aws_cdk`
- `constructs`
- `cdk.constructs.asset_onboarding_lambda`
- `cdk.constructs.metrics_lambda`


# Classes

---
### DevStack 
- **Type**: `class`
- **Members**:
    - `asset_dropzone_bucket`: An S3 bucket configured for asset dropzone with specific CORS and encryption settings.
    - `onboarding_lambda`: An instance of AssetOnboardingLambda configured with environment and API details.
    - `metrics_lambda`: An instance of MetricsLambda configured with environment and database details.
- **Description**: The DevStack class is a specialized AWS CDK stack designed for deploying additional infrastructure components for development and testing purposes. It creates an S3 bucket for asset management with specific configurations such as CORS rules and encryption. Additionally, it sets up two Lambda functions: one for asset onboarding and another for metrics collection, both configured with environment-specific parameters. This stack is intended for temporary use and may be deleted after its purpose is fulfilled.
- **Inherits From**:
    - Stack

**Methods**

---
#### DevStack.__init__
The `__init__` function initializes a DevStack instance by setting up an S3 bucket and two Lambda functions with specific configurations.
- **Inputs**:
    - `scope`: A Construct object that defines the scope in which this stack is defined.
    - `construct_id`: A string that uniquely identifies this stack within the scope.
    - `params`: An instance of DevStackParams containing configuration parameters like environment, cdk_prefix, and database_url.
    - `kwargs`: Additional keyword arguments that are passed to the parent Stack class.
- **Control Flow**:
    - Call the parent class's __init__ method with scope, construct_id, and kwargs.
    - Extract and sanitize the cdk_prefix from params by removing dashes, spaces, and trimming whitespace.
    - Extract the environment from params.
    - Create an S3 bucket with specific configurations such as removal policy, auto-delete objects, block public access, encryption, versioning, and CORS rules.
    - Initialize an AssetOnboardingLambda with parameters including environment, API URL, Auth0 URL, and the created S3 bucket.
    - Initialize a MetricsLambda with parameters including environment, database URL, and cdk_prefix.
- **Output**:
    - The function does not return any value; it initializes the DevStack instance with configured resources.



---
### DevStackParams 
- **Type**: `dataclass`
- **Members**:
    - `environment`: Specifies the environment in which the stack is deployed.
    - `cdk_prefix`: Defines a prefix used for naming resources in the stack.
    - `database_url`: Holds the URL for the database connection.
- **Description**: The `DevStackParams` class is a data structure used to encapsulate parameters required for deploying a development stack, including the environment, a prefix for resource naming, and the database URL. It is designed to be used with the `DevStack` class to provide configuration details necessary for setting up infrastructure components such as S3 buckets and Lambda functions.


