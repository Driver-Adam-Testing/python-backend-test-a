import hashlib
from urllib.parse import unquote_plus, urlparse

import boto3

from app.core.config import settings

# Initialize S3 client
s3_client = boto3.client(
    "s3",
    region_name="us-east-1",
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    endpoint_url=settings.AWS_S3_ENDPOINT_URL if settings.AWS_S3_ENDPOINT_URL else None,
)


def org_id_to_hash(organization_id: str) -> str:
    return hashlib.sha256(organization_id.encode()).hexdigest()[:63]


def dropzone_bucket_name() -> str:
    return (
        settings.DROPZONE_BUCKET_NAME
        if not settings.USE_LEGACY_DROPZONE
        else f"{settings.ENVIRONMENT}-{settings.AWS_S3_CODE_BUCKET_SUFFIX}"
    )


def parse_presigned_url(url: str) -> tuple[str, str]:
    parsed_url = urlparse(url)
    host = parsed_url.netloc
    path = parsed_url.path.lstrip("/")  # Remove leading slash

    # Extract bucket from the domain
    if ".s3." in host:  # Domain-style
        bucket = host.split(".s3.")[0]
    elif host.startswith(("s3-", "s3.")):  # Path-style
        bucket = path.split("/")[0]
        path = "/".join(path.split("/")[1:])
    else:
        raise ValueError("Invalid S3 URL format")
    key = unquote_plus(path)
    return bucket, key


def generate_put_presigned_url(
    key: str, content_type: str, metadata: dict | None = None, expires: int = 3600
) -> str:
    if metadata is None:
        metadata = {}
    bucket = (
        settings.DROPZONE_BUCKET_NAME
        if not settings.USE_LEGACY_DROPZONE
        else f"{settings.ENVIRONMENT}-{settings.AWS_S3_CODE_BUCKET_SUFFIX}"
    )
    return s3_client.generate_presigned_url(
        ClientMethod="put_object",
        Params={
            "Bucket": bucket,
            "Key": key,
            "ContentType": content_type,
            "Metadata": metadata,
        },
        ExpiresIn=expires,
    )


def generate_get_presigned_url(key: str, expires: int = 3600) -> str:
    bucket = (
        settings.DROPZONE_BUCKET_NAME
        if not settings.USE_LEGACY_DROPZONE
        else f"{settings.ENVIRONMENT}-{settings.AWS_S3_CODE_BUCKET_SUFFIX}"
    )
    return s3_client.generate_presigned_url(
        ClientMethod="get_object",
        Params={
            "Bucket": bucket,
            "Key": key,
        },
        ExpiresIn=expires,
    )


def generate_org_get_presigned_url(
    organization_id: str, key: str, expires: int = 600
) -> str:
    bucket = hashlib.sha256(organization_id.encode()).hexdigest()[:63]
    return s3_client.generate_presigned_url(
        ClientMethod="get_object",
        Params={
            "Bucket": bucket,
            "Key": key,
        },
        ExpiresIn=expires,
    )


def head_org_object(organization_id: str, key: str, expires: int = 600) -> bool:
    bucket = hashlib.sha256(organization_id.encode()).hexdigest()[:63]
    try:
        s3_client.head_object(
            Bucket=bucket,
            Key=key,
        )
        return True
    except s3_client.exceptions.NoSuchKey:
        return False


def delete_file_from_s3(key: str, bucket: str) -> None:
    """
    Delete a file from S3.
    NOTE: this should be in shared but shared package does not have access to settings need to instantiate boto3 client
    """
    response = s3_client.delete_object(Bucket=bucket, Key=key)
    print(response)
