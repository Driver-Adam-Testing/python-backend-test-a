import hashlib
import uuid

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


def get_presigned_url_from_content_information(
    codebase_id: uuid.UUID, organization_id: str, relative_path: str
):
    org_id_hash = hashlib.sha256(organization_id.encode()).hexdigest()[:63]
    object_key = f"{codebase_id}/{relative_path}"

    return generate_get_presigned_url(key=object_key, bucket=org_id_hash)


def get_presigned_url_without_codebase(organization_id: str, relative_path: str):
    org_id_hash = hashlib.sha256(organization_id.encode()).hexdigest()[:63]
    object_key = f"documents/{relative_path}"

    return generate_get_presigned_url(key=object_key, bucket=org_id_hash)
