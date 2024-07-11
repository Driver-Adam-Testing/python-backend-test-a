import boto3
from config import settings

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


def generate_get_presigned_url(key, bucket, expires=3600):
    return s3_client.generate_presigned_url(
        ClientMethod='get_object',
        Params={
            'Bucket': bucket,
            'Key': key,
        },
        ExpiresIn=expires
    )
