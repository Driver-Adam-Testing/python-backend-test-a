import boto3


def generate_get_presigned_url(key, bucket, expires=3600):
    s3_client = boto3.client(
        "s3",
    )
    return s3_client.generate_presigned_url(
        ClientMethod="get_object",
        Params={
            "Bucket": bucket,
            "Key": key,
        },
        ExpiresIn=expires,
    )
