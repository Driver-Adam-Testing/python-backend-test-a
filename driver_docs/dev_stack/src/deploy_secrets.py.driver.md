# Purpose
This Python script is designed to deploy secrets to AWS Secrets Manager, specifically for AWS Lambda functions. It utilizes the `boto3` library to interact with AWS services and `argparse` to handle command-line arguments. The script begins by loading secrets from two JSON configuration files, `asset-onboarding-lambda-config.json` and `metrics-lambda-config.json`, using a utility function `load_secrets_from_json`. These files contain mappings of environment keys to secret names and their corresponding values. The script then parses command-line arguments to obtain the AWS profile, region, and CloudFormation stack name, which are essential for establishing a session with AWS and identifying the correct resources.

The core functionality involves fetching CloudFormation stack outputs and updating the corresponding secrets in AWS Secrets Manager. It retrieves the stack's outputs and maps them to the secret names defined in the JSON configuration files. For each secret, the script checks if the output and secret value exist, and if so, it updates the secret in Secrets Manager with the new value. This script is a specialized tool for managing and deploying secrets for AWS Lambda functions, ensuring that sensitive information is securely stored and updated in AWS infrastructure.
# Imports and Dependencies

---
- `argparse`
- `boto3`
- `utils`


# Global Variables

---
### CODE_LAMBDA_FN 
- **Type**: `string`
- **Description**: `CODE_LAMBDA_FN` is a string variable that holds the filename 'asset-onboarding-lambda-config.json'. This file is expected to contain configuration details or secrets related to the asset onboarding Lambda function.
- **Use**: This variable is used to load secrets from the specified JSON file using the `load_secrets_from_json` function.


---
### METRICS_LAMBDA_FN 
- **Type**: `str`
- **Description**: `METRICS_LAMBDA_FN` is a string variable that holds the filename of a JSON configuration file, specifically 'metrics-lambda-config.json'. This file is likely used to store configuration details for a Lambda function related to metrics.
- **Use**: This variable is used to load secrets from the specified JSON configuration file for the metrics Lambda function.


---
### args 
- **Type**: `argparse.Namespace`
- **Description**: The `args` variable is an instance of `argparse.Namespace` that holds the parsed command-line arguments. It is created by calling `parser.parse_args()`, where `parser` is an `argparse.ArgumentParser` object configured to accept three required arguments: `--profile`, `--region`, and `--name`. Each of these arguments is expected to be a string and is used to configure the AWS deployment process.
- **Use**: This variable is used to store and access the command-line arguments provided by the user, which are necessary for configuring the AWS session and CloudFormation stack operations.


---
### asset_lambda_secrets 
- **Type**: `dict`
- **Description**: The `asset_lambda_secrets` variable is a dictionary that is populated by the `load_secrets_from_json` function, which reads secrets from the JSON file specified by `CODE_LAMBDA_FN`. This dictionary contains mappings of environment keys to secret values and a secret map used for updating AWS Secrets Manager.
- **Use**: This variable is used to store and manage secrets for the asset onboarding lambda function, facilitating the update of secret values in AWS Secrets Manager.


---
### cf 
- **Type**: `boto3.client`
- **Description**: The `cf` variable is an instance of a Boto3 CloudFormation client, created using a session with a specified AWS profile and region. It allows interaction with AWS CloudFormation services, such as listing exports and describing stacks.
- **Use**: This variable is used to perform operations on AWS CloudFormation, such as fetching stack outputs and managing stack resources.


---
### metrics_lambda_secrets 
- **Type**: `dictionary`
- **Description**: The `metrics_lambda_secrets` variable is a dictionary that stores secrets loaded from a JSON configuration file named 'metrics-lambda-config.json'. This dictionary contains mappings of environment keys to secret values and a secret map that associates environment keys with output keys.
- **Use**: This variable is used to update secret values in AWS Secrets Manager by mapping environment keys to their corresponding secret names and values.


---
### name 
- **Type**: `str`
- **Description**: The `name` variable is a string that represents the CloudFormation stack name, which is provided as a command-line argument when the script is executed. It is required for the script to function correctly, as it is used to identify the specific stack from which outputs are fetched and secrets are updated.
- **Use**: This variable is used to construct the `stack_name` and `stripped_name` variables, which are essential for interacting with AWS CloudFormation and Secrets Manager.


---
### outputs 
- **Type**: `dict`
- **Description**: The `outputs` variable is a dictionary that maps CloudFormation export names to their corresponding output values. It is constructed by iterating over the 'Outputs' list of a specific CloudFormation stack and extracting the 'ExportName' and 'OutputValue' for each output.
- **Use**: This variable is used to retrieve and map specific output values from a CloudFormation stack, which are then used to update secret values in AWS Secrets Manager.


---
### parser 
- **Type**: `argparse.ArgumentParser`
- **Description**: The `parser` variable is an instance of `argparse.ArgumentParser`, which is used to handle command-line arguments for the script. It is configured with a description and three required arguments: `--profile`, `--region`, and `--name`, each with a specific type and help message.
- **Use**: This variable is used to parse and manage command-line arguments provided to the script, ensuring that the necessary parameters are supplied for the script's execution.


---
### profile 
- **Type**: `str`
- **Description**: The `profile` variable is a string that holds the AWS profile name specified by the user through command line arguments. It is used to configure the AWS session for deploying secrets to AWS services.
- **Use**: This variable is used to create a Boto3 session with the specified AWS profile name.


---
### region 
- **Type**: `str`
- **Description**: The `region` variable is a string that holds the AWS region specified by the user through command line arguments. It is used to configure the AWS session and clients to interact with AWS services in the specified region.
- **Use**: This variable is used to set the `region_name` parameter when creating a Boto3 session, ensuring that all AWS service interactions occur within the specified region.


---
### remapped_key 
- **Type**: `str`
- **Description**: The `remapped_key` variable is a string that is constructed by concatenating the `stripped_name` with the `output_key`. It is used to create a unique key that corresponds to a specific output in the CloudFormation stack.
- **Use**: This variable is used to retrieve the corresponding secret name from the CloudFormation stack outputs.


---
### response 
- **Type**: `dict`
- **Description**: The `response` variable is a dictionary that stores the result of the `list_exports` method call on the AWS CloudFormation client. This method retrieves a list of exported output values from the CloudFormation stacks in the account.
- **Use**: This variable is used to store and access the exported outputs from CloudFormation, which are later used to map and update secret values in AWS Secrets Manager.


---
### secret_name 
- **Type**: `str`
- **Description**: The `secret_name` variable is a string that holds the name of a secret in AWS Secrets Manager. It is derived from the outputs of a CloudFormation stack, specifically by looking up a remapped key in the stack's outputs.
- **Use**: This variable is used to identify and update the corresponding secret in AWS Secrets Manager with a new value.


---
### secret_value 
- **Type**: `str`
- **Description**: The `secret_value` variable is a string that holds the value of a secret retrieved from the `asset_lambda_secrets` or `metrics_lambda_secrets` dictionaries. These dictionaries are loaded from JSON files and contain mappings of environment keys to secret values.
- **Use**: This variable is used to update the AWS Secrets Manager with the corresponding secret value for a given secret name.


---
### secretsmanager 
- **Type**: `boto3.client`
- **Description**: The `secretsmanager` variable is an instance of a Boto3 client for AWS Secrets Manager, created using a session with a specified AWS profile and region. It is used to interact with AWS Secrets Manager to manage secret values.
- **Use**: This variable is used to update secret values in AWS Secrets Manager by calling methods such as `put_secret_value`.


---
### session 
- **Type**: `boto3.Session`
- **Description**: The `session` variable is an instance of the `boto3.Session` class, which is used to create a session with AWS services. It is initialized with a specific AWS profile and region, allowing the script to interact with AWS resources using the specified credentials and settings.
- **Use**: This variable is used to create clients for AWS services like CloudFormation and Secrets Manager, enabling the script to perform operations such as listing exports and updating secret values.


---
### stack 
- **Type**: `dict`
- **Description**: The `stack` variable is a dictionary that represents the details of a specific AWS CloudFormation stack. It is obtained by calling the `describe_stacks` method on the CloudFormation client, using the `stack_name` as the identifier. The dictionary contains various attributes of the stack, including its outputs, which are used later in the script to map and update secret values in AWS Secrets Manager.
- **Use**: This variable is used to access the outputs of a specific CloudFormation stack, which are then utilized to update secret values in AWS Secrets Manager.


---
### stack_name 
- **Type**: `str`
- **Description**: The `stack_name` variable is a string that represents the name of an AWS CloudFormation stack. It is constructed by taking the `name` argument provided by the user, removing spaces, and appending the suffix 'TempTestInDevStack'. This variable is used to identify the specific CloudFormation stack from which outputs are fetched and secrets are updated.
- **Use**: This variable is used to specify the CloudFormation stack name for operations such as fetching stack outputs and updating secret values in AWS Secrets Manager.


---
### stripped_name 
- **Type**: `str`
- **Description**: The `stripped_name` variable is a string derived from the `name` argument provided via command line. It is created by removing hyphens, spaces, and leading or trailing whitespace from the `name`. This results in a more compact and sanitized version of the stack name.
- **Use**: This variable is used to construct keys for accessing and updating secret values in AWS Secrets Manager.


