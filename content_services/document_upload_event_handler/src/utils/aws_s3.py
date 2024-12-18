import logging

import boto3
from botocore.exceptions import ClientError
from src.utils.config import settings

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


def copy_s3_object(
    source_bucket: str, source_key: str, dest_bucket: str, dest_key: str
) -> bool:
    copy_source = {"Bucket": source_bucket, "Key": source_key}
    try:
        s3_client.copy_object(CopySource=copy_source, Bucket=dest_bucket, Key=dest_key)
        logging.info(
            f"Successfully copied object from {source_bucket}/{source_key} to {dest_bucket}/{dest_key}"
        )
        return True
    except ClientError as e:
        logging.error(f"Error copying object: {e}")
        raise


def ensure_bucket_exists(bucket_name: str, region: str | None = None) -> bool:
    try:
        # Check if the bucket exists
        s3_client.head_bucket(Bucket=bucket_name)
        logging.info(f"Bucket {bucket_name} already exists.")
        return True
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "404":
            # Bucket doesn't exist, so create it
            try:
                # https://stackoverflow.com/questions/51912072/invalidlocationconstraint-error-while-creating-s3-bucket-when-the-used-command-i
                # us-east-1 is special
                if region is None or region == "us-east-1":
                    s3_client.create_bucket(Bucket=bucket_name)
                else:
                    location = {"LocationConstraint": region}
                    s3_client.create_bucket(
                        Bucket=bucket_name, CreateBucketConfiguration=location
                    )
                logging.info(f"Bucket {bucket_name} created successfully.")
                return True
            except ClientError as create_error:
                logging.error(f"Couldn't create bucket {bucket_name}: {create_error}")
                raise Exception(f"Couldn't create bucket {bucket_name}: {create_error}")
        elif error_code == "301":
            # Handle specific error code 301
            logging.error(f"Bucket {bucket_name} has been moved permanently.")
            raise Exception(f"Error checking bucket {bucket_name}: {e}")
        else:
            # Something else went wrong when checking the bucket
            logging.error(f"Error checking bucket {bucket_name}: {e}")
            raise Exception(f"Error checking bucket {bucket_name}: {e}")


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
