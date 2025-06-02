# Purpose
This Python script is designed to deploy a temporary development stack using the AWS Cloud Development Kit (CDK). It is a script that automates the setup of a development environment by creating a stack with specific parameters. The script begins by ensuring that certain environment variables—`DEV_NAME`, `DEPLOYMENT_ENVIRONMENT`, and `DATABASE_URL`—are set, as these are crucial for defining the stack's configuration. The `DEV_NAME` is sanitized to create a valid stack name, which is then used to identify the stack being deployed.

The script reads a configuration file, `cdk-stack-config.json`, to load additional environment-specific settings, which are then applied to the current environment. It utilizes the `DevStack` class, presumably defined in the `cdk.dev_stack` module, to instantiate a new stack with parameters such as the CDK prefix, deployment environment, and database URL. The stack is configured to deploy in a specific AWS account and region. Finally, the script synthesizes the application, which prepares the stack for deployment. This script is a focused utility for developers working with AWS CDK, providing a streamlined way to set up and deploy development stacks with predefined configurations.
# Imports and Dependencies

---
- `json`
- `os`
- `aws_cdk`
- `cdk.dev_stack.DevStack`
- `cdk.dev_stack.DevStackParams`


# Global Variables

---
### app 
- **Type**: `cdk.App`
- **Description**: The `app` variable is an instance of the `cdk.App` class from the AWS CDK library. It serves as the root of the construct tree and is responsible for synthesizing the entire AWS Cloud Development Kit (CDK) application. This instance is used to define and manage the lifecycle of AWS infrastructure stacks.
- **Use**: The `app` variable is used to initialize and manage the AWS CDK application, allowing for the definition and deployment of infrastructure stacks.


---
### cdk_stack_config 
- **Type**: `dict`
- **Description**: `cdk_stack_config` is a dictionary that is loaded from a JSON file located at './state/out/cdk-stack-config.json'. This JSON file contains configuration settings for the AWS CDK stack, particularly under the 'env' key, which holds environment variables to be set for the deployment.
- **Use**: This variable is used to read and store configuration data for the CDK stack, which is then used to set environment variables for the deployment process.


---
### dev_name 
- **Type**: `str`
- **Description**: The `dev_name` variable is a string that is derived from the `DEV_NAME` environment variable. It is processed to remove hyphens, spaces, and any leading or trailing whitespace.
- **Use**: This variable is used as a prefix for naming the development stack and as part of the parameters for the `DevStack` instance.


---
### dev_stack_name 
- **Type**: `str`
- **Description**: The `dev_stack_name` variable is a string that concatenates a sanitized version of the `DEV_NAME` environment variable with the suffix 'TempTestInDevStack'. This variable is used to define the name of the AWS CDK stack being deployed.
- **Use**: This variable is used to specify the name of the development stack in the AWS CDK application.


