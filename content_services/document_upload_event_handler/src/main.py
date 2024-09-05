import json
import logging
import os
from urllib.parse import unquote_plus

import boto3
import botocore
import botocore.session
import httpx
from aws_secretsmanager_caching import SecretCache, SecretCacheConfig
from botocore.exceptions import ClientError
from src.utils.aws_s3 import generate_get_presigned_url, head_object
from src.utils.config import settings

# def handler(event, context):
#     logging.info(event)


# # Python lambdas have to be synchronous ¯\_(ツ)_/¯
# # https://stackoverflow.com/questions/60455830/can-you-have-an-async-handler-in-lambda-python-3-6
def handler(event, context):
    # Parse the SNS message
    for record in event["Records"]:
        sns_message = json.loads(record["Sns"]["Message"])

        sm_client = botocore.session.get_session().create_client("secretsmanager")
        cache_config = SecretCacheConfig()
        cache = SecretCache(config=cache_config, client=sm_client)

        client_id = (
            cache.get_secret_string(settings.CLIENT_ID_SECRET)
            if settings.ENVIRONMENT != "local"
            else settings.CLIENT_ID_SECRET
        )
        client_secret = (
            cache.get_secret_string(settings.CLIENT_SECRET_SECRET)
            if settings.ENVIRONMENT != "local"
            else settings.CLIENT_SECRET_SECRET
        )
        payload = json.dumps(
            {
                "client_id": client_id,
                "client_secret": client_secret,
                "audience": settings.API_URL,
                "grant_type": "client_credentials",
            }
        )

        with httpx.Client(base_url=settings.AUTH0_URL) as auth0Client:
            logging.info("Fetching M2M token from Auth0...")
            # Fetch one M2M token per invocation of the lambda. This could be cached but would require additional impl similar to SecretCache above
            token_response = auth0Client.post(
                "/oauth/token",
                headers={"content-type": "application/json"},
                data=payload,
            )
            token_response.raise_for_status()  # Raises an exception for 4XX/5XX responses
            token_json = token_response.json()

            logging.info("Processing S3 event(s)...")
            # Extract information from the S3 event
            for s3_record in sns_message["Records"]:
                bucket_name = s3_record["s3"]["bucket"]["name"]
                object_key = s3_record["s3"]["object"]["key"]
                real_object_key = unquote_plus(object_key)
                logging.info("key = " + real_object_key)
                logging.info("bucket = " + bucket_name)
                metadata = head_object(bucket=bucket_name, key=real_object_key)
                bucket_exists = ensure_bucket_exists(
                    metadata["Metadata"]["org_bucket"], region="us-east-1"
                )
                if bucket_exists:
                    logging.info("Copying to organization bucket...")
                    copy_s3_object(
                        source_bucket=bucket_name,
                        source_key=object_key,
                        dest_bucket=metadata["Metadata"]["org_bucket"],
                        dest_key=f"documents/{object_key}",  # TODO - change as appropriate
                    )

                    logging.info("Creating source content...")
                    # I changed relative path from documents/filename to just filename
                    create_src_content_response = exec_create_source_content(
                        source_content_type="supplemental-document",
                        relative_path=os.path.basename(object_key),
                        workspace_id=metadata["Metadata"]["workspace_id"],
                        token=token_json["access_token"],
                    )
                    logging.info("Source content created.")
                    logging.info(
                        f"Triggering document upload onboarding for bucket = {bucket_name}, key = {object_key}"
                    )
                    presigned_url = generate_get_presigned_url(
                        bucket=bucket_name, key=real_object_key
                    )
                    # TODO: These parameters are wrong, we just need to pass source content id
                    exec_document_onboarding_service(
                        {
                            "download_url": presigned_url,
                            "object_key": object_key,
                            "org_id": metadata["Metadata"]["organization_id"],
                            "creator_id": metadata["Metadata"]["creator_id"],
                            "workspace_id": metadata["Metadata"]["workspace_id"],
                            "filepath": metadata["Metadata"]["file_path"],
                            "codebase_name": metadata["Metadata"]["codebase_name"],
                            "provider": metadata["Metadata"]["provider"],
                        },
                        token_json["access_token"],
                    )


def exec_document_onboarding_service(event, token):
    with httpx.Client(base_url=settings.API_URL, follow_redirects=True) as driverClient:
        payload = {**event}
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        }
        response = driverClient.post(
            "/onboarding/generate-pdf-summaries", headers=headers, json=payload
        )
        response.raise_for_status()  # Raises an exception for 4XX/5XX responses
        event_response = response.json()
        logging.info(event_response)
        # Make sure event was received successfully
        return "OK"


# Codebase ID is also included as an optional input. It seems like we want to move away from using that?
def exec_create_source_content(
    relative_path: str, source_content_type: str, workspace_id: str, token: str
):
    query = """
    mutation CreateSourceContent($input: SourceContentInput!) {
        createSourceContent(input: $input)
    }
    """

    variables = {
        "input": {
            "relative_path": relative_path,
            "source_content_type": source_content_type,
            "workspace_id": workspace_id,
        }
    }

    payload = {"query": query, "variables": variables}

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    with httpx.Client(base_url=settings.API_URL, follow_redirects=True) as driverClient:
        response = driverClient.post("/graphql", json=payload, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Query failed with status code: {response.status_code}")


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
