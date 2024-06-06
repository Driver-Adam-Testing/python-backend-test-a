import boto3
import os

s3_client = boto3.client(
    "s3",
    endpoint_url=os.getenv("AWS_S3_ENDPOINT_URL"),
    aws_access_key_id="test",
    aws_secret_access_key="test",
)
