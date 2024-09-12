import boto3
from src.utils.config import settings

# Initialize S3 client
s3_client = boto3.client(
    "s3",
    region_name="us-east-1",
    endpoint_url=settings.AWS_S3_ENDPOINT_URL if settings.AWS_S3_ENDPOINT_URL else None,
)


def generate_get_presigned_url(bucket, key, expires=3600):
    return s3_client.generate_presigned_url(
        ClientMethod="get_object",
        Params={
            "Bucket": bucket,
            "Key": key,
        },
        ExpiresIn=expires,
    )


def head_object(bucket, key):
    return s3_client.head_object(Bucket=bucket, Key=key)
