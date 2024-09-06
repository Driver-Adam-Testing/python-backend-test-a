import logging

import boto3
from botocore.exceptions import ClientError
from src.utils.config import settings

# Initialize S3 client
s3_client = boto3.client(
    "s3",
    region_name="us-east-1",
    endpoint_url=settings.AWS_S3_ENDPOINT_URL if settings.AWS_S3_ENDPOINT_URL else None,
)


def generate_get_presigned_url(bucket, key, expires=3600):
    return s3_client.generate_presigned_url(
        ClientMethod="get_object",
        Params={
            "Bucket": bucket,
            "Key": key,
        },
        ExpiresIn=expires,
    )


def head_object(bucket, key):
    return s3_client.head_object(Bucket=bucket, Key=key)


def copy_s3_object(source_bucket, source_key, dest_bucket, dest_key):
    """
    Copies an S3 object from one bucket to another.

    :param source_bucket: Name of the source bucket
    :param source_key: Key of the source object
    :param dest_bucket: Name of the destination bucket
    :param dest_key: Key to be used for the destination object
    :return: True if the operation was successful, False otherwise
    """
    s3_client = boto3.client("s3")

    try:
        # Construct the copy source dictionary
        copy_source = {"Bucket": source_bucket, "Key": source_key}

        # Perform the copy operation
        s3_client.copy_object(CopySource=copy_source, Bucket=dest_bucket, Key=dest_key)

        logging.info(
            f"Successfully copied object from {source_bucket}/{source_key} to {dest_bucket}/{dest_key}"
        )
        return True

    except ClientError as e:
        logging.error(f"Error copying object: {e}")
        return False


def ensure_bucket_exists(bucket_name, region=None):
    """
    Check if a bucket exists, and create it if it doesn't.

    :param bucket_name: Name of the bucket to check/create
    :param region: AWS region to create the bucket in (optional)
    :return: True if the bucket exists or was created successfully, False otherwise
    """
    s3_client = boto3.client("s3")

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
                if region is None:
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
                return False
        else:
            # Something else went wrong when checking the bucket
            logging.error(f"Error checking bucket {bucket_name}: {e}")
            return False
