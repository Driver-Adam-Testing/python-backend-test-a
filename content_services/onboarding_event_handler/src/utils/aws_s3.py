import boto3
from src.utils.config import settings
from urllib.parse import quote_plus

# Initialize S3 client
s3_client = boto3.client(
    's3',
    region_name='us-east-1',
    endpoint_url=settings.AWS_S3_ENDPOINT_URL
            if settings.AWS_S3_ENDPOINT_URL
            else None,
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
    
def head_object(bucket, key):
    return s3_client.head_object(Bucket=bucket, Key=key)
