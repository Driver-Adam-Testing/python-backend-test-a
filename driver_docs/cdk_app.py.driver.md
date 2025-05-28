# Purpose
This Python script is designed to manage the deployment of different infrastructure environments using the AWS Cloud Development Kit (CDK). It imports several stack classes, each corresponding to a specific deployment environment: DevelopmentStack, OpsStack, ProductionStack, StagingStack, and TestInDevStack. The script determines which stack to deploy based on the `DEPLOYMENT_ENVIRONMENT` environment variable, allowing for flexible deployment configurations. Each stack is associated with a specific AWS account and region, which are either retrieved from environment variables or hardcoded within the script.

The script serves as an entry point for deploying infrastructure as code, making it a critical component in a continuous integration and deployment pipeline. It does not define public APIs or external interfaces but rather orchestrates the deployment process by instantiating the appropriate stack class based on the deployment environment. The use of the AWS CDK allows for infrastructure to be defined using familiar programming constructs, enhancing maintainability and scalability. The script concludes by calling `app.synth()`, which synthesizes the defined stacks into AWS CloudFormation templates, ready for deployment.
# Imports and Dependencies

---
- `os`
- `aws_cdk`
- `cdk.development_stack`
- `cdk.ops_stack`
- `cdk.production_stack`
- `cdk.staging_stack`
- `cdk.test_in_dev_stack`


# Global Variables

---
### app 
- **Type**: `cdk.App`
- **Description**: The `app` variable is an instance of the `cdk.App` class from the AWS CDK library. It serves as the root of the CDK application, which is responsible for synthesizing the cloud infrastructure stacks defined in the code. The `app` variable is used to manage and deploy different stacks based on the deployment environment.
- **Use**: The `app` variable is used to initialize and manage the deployment of various AWS infrastructure stacks depending on the specified deployment environment.


---
### deployment_environment 
- **Type**: `str`
- **Description**: The `deployment_environment` variable is a string that retrieves the current deployment environment setting from the environment variable `DEPLOYMENT_ENVIRONMENT`. This variable determines which stack configuration to deploy in the AWS CDK application.
- **Use**: This variable is used to select and deploy the appropriate AWS CDK stack based on the specified deployment environment.


