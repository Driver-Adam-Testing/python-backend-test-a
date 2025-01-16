import hashlib

import boto3


def generate_get_presigned_url(key: str, bucket: str, expires: int = 3600) -> str:
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


def get_presigned_url(organization_id: str, path: str) -> str:
    org_id_hash = hashlib.sha256(organization_id.encode()).hexdigest()[:63]

    return generate_get_presigned_url(key=path, bucket=org_id_hash)
