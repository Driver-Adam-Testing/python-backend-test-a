import boto3
from src.utils.config import settings

# Initialize S3 client
s3_client = boto3.client(
    "s3",
    region_name="us-east-1",
    endpoint_url=settings.AWS_S3_ENDPOINT_URL if settings.AWS_S3_ENDPOINT_URL else None,
)


def generate_get_presigned_url(bucket: str, key: str, expires: int = 3600) -> str:
    return s3_client.generate_presigned_url(
        ClientMethod="get_object",
        Params={
            "Bucket": bucket,
            "Key": key,
        },
        ExpiresIn=expires,
    )


def head_object(bucket: str, key: str) -> dict:
    return s3_client.head_object(Bucket=bucket, Key=key)


def has_no_threats_tag(bucket: str, key: str) -> bool:
    tags = s3_client.get_object_tagging(Bucket=bucket, Key=key)
    return (
        len(
            [
                tag
                for tag in tags["TagSet"]
                if tag["Key"] == "GuardDutyMalwareScanStatus"
                and tag["Value"] == "NO_THREATS_FOUND"
            ]
        )
        == 1
    )
