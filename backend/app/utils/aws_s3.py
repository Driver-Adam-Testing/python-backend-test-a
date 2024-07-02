import boto3
from app.core.config import settings

# Initialize S3 client
s3_client = boto3.client(
    's3',
    region_name='us-east-1',
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    endpoint_url=settings.AWS_S3_ENDPOINT_URL
            if settings.AWS_S3_ENDPOINT_URL
            else None,
)

def generate_put_presigned_url(key, content_type, metadata={}, expires=3600):
    bucket = f"{settings.ENVIRONMENT}-{settings.AWS_S3_CODE_BUCKET_SUFFIX}"
    print(metadata)
    return s3_client.generate_presigned_url(
        ClientMethod='put_object',
        Params={
            'Bucket': bucket,
            'Key': key,
            "ContentType": content_type,
            'Metadata': metadata
        },
        ExpiresIn=expires
    )

def generate_get_presigned_url(key, expires=3600):
    bucket = f"{settings.ENVIRONMENT}-{settings.AWS_S3_CODE_BUCKET_SUFFIX}"
    return s3_client.generate_presigned_url(
        ClientMethod='get_object',
        Params={
            'Bucket': bucket,
            'Key': key,
        },
        ExpiresIn=expires
    )