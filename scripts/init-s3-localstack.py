import boto3
import os

print(os.environ)
print("Creating S3 bucket...", os.getenv("BUCKET_NAME"))
print("AWS_S3_ENDPOINT_URL: ", os.getenv("AWS_S3_ENDPOINT_URL"))
print("AWS_ACCESS_KEY_ID: ", os.getenv("AWS_ACCESS_KEY_ID"))

s3_client = boto3.client(
    "s3",
    endpoint_url=os.getenv("AWS_S3_ENDPOINT_URL"),
    aws_access_key_id="NOT_USED",
    aws_secret_access_key="NOT_USED",
)

s3_client.create_bucket(Bucket=os.getenv("BUCKET_NAME"))
