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


def has_allowed_guard_duty_tag(bucket: str, key: str) -> bool:
    """
    Check if the S3 object has the 'GuardDutyMalwareScanStatus' tag with value 'NO_THREATS_FOUND' or 'UNSUPPORTED'.
    """
    tags = s3_client.get_object_tagging(Bucket=bucket, Key=key)
    """
    supported_tags = ["NO_THREATS_FOUND", "UNSUPPORTED"]
    the 'UNSUPPORTED' tag is a misnomer because GuardDuty tags file as UNSUPPORTED
    if they have too many files ( > 1000) or file is too large but we can still process it.
    """
    supported_tags = ["NO_THREATS_FOUND", "UNSUPPORTED"]
    return (
        len(
            [
                tag
                for tag in tags["TagSet"]
                if tag["Key"] == "GuardDutyMalwareScanStatus"
                and tag["Value"] in supported_tags
            ]
        )
        == 1
    )
