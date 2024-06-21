import boto3
from app.core.config import settings

# Initialize S3 client
s3_client = boto3.client(
    's3',
    region_name='us-east-1',
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
)


def generate_presigned_url(key, metadata, expires=3600):
    env_name = 'development'
    bucket = f"{env_name}-{settings.AWS_S3_CODE_BUCKET_SUFFIX}"
    return s3_client.generate_presigned_url(
        ClientMethod='put_object',
        Params={
            'Bucket': bucket,
            'Key': key,
            "ContentType": "application/zip",
            'Metadata': metadata
        },
        ExpiresIn=expires
    )
