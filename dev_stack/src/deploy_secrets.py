import argparse

import boto3
from utils import load_secrets_from_json

CODE_LAMBDA_FN = "asset-onboarding-lambda-config.json"
METRICS_LAMBDA_FN = "metrics-lambda-config.json"


asset_lambda_secrets = load_secrets_from_json(CODE_LAMBDA_FN)
metrics_lambda_secrets = load_secrets_from_json(METRICS_LAMBDA_FN)


# Parse command line arguments
parser = argparse.ArgumentParser(description="Deploy secrets to AWS")
parser.add_argument("--profile", type=str, required=True, help="AWS profile name")
parser.add_argument("--region", type=str, required=True, help="AWS region")
parser.add_argument("--name", type=str, required=True, help="CloudFormation stack name")
args = parser.parse_args()

profile = args.profile
region = args.region
name = args.name
stack_name = f"{name.replace(" ", "").strip()}TempTestInDevStack"

# Boto3 session with profile
session = boto3.Session(profile_name=profile, region_name=region)
cf = session.client("cloudformation")
secretsmanager = session.client("secretsmanager")


# # Fetch CloudFormation exports
response = cf.list_exports()
# Get outputs for the specific stack only
print(f"🔍 Getting outputs from stack: {stack_name}")
stack = cf.describe_stacks(StackName=stack_name)["Stacks"][0]
# print(stack)
outputs = {o["ExportName"]: o["OutputValue"] for o in stack.get("Outputs", [])}
# print(outputs)
# Set secret values in Secrets Manager
for env_key, output_key in asset_lambda_secrets["secret_map"].items():
    secret_name = outputs.get(output_key)
    secret_value = asset_lambda_secrets["env"].get(env_key)
    print(f"🔍 Checking {secret_name} in stack {stack_name}")

    if not secret_name:
        print(f"⚠️ Output {output_key} not found in stack {stack_name}")
        continue
    #
    if not secret_value:
        print(f"⚠️ Secret value for {env_key} not found in file/env")
        continue
    print(f"🔐 Updating {secret_name} with value from {env_key}")
    secretsmanager.put_secret_value(SecretId=secret_name, SecretString=secret_value)


for env_key, output_key in metrics_lambda_secrets["secret_map"].items():
    secret_name = outputs.get(output_key)
    secret_value = metrics_lambda_secrets["env"].get(env_key)
    print(f"🔍 Checking {secret_name} in stack {stack_name}")

    if not secret_name:
        print(f"⚠️ Output {output_key} not found in stack {stack_name}")
        continue
    #
    if not secret_value:
        print(f"⚠️ Secret value for {env_key} not found in file/env")
        continue
    print(f"🔐 Updating {secret_name} with value from {env_key}")
    secretsmanager.put_secret_value(SecretId=secret_name, SecretString=secret_value)
