import json
import logging
import os
from urllib.parse import unquote_plus

import botocore
import botocore.session
import httpx
from aws_secretsmanager_caching import SecretCache, SecretCacheConfig
from src.utils.aws_s3 import copy_s3_object, ensure_bucket_exists, head_object
from src.utils.config import settings


# # Python lambdas have to be synchronous ¯\_(ツ)_/¯
# # https://stackoverflow.com/questions/60455830/can-you-have-an-async-handler-in-lambda-python-3-6
def handler(event, context):
    logging.info(event)
    results = []

    for record in event["Records"]:
        sns_message = json.loads(record["Sns"]["Message"])

        sm_client = botocore.session.get_session().create_client(
            "secretsmanager",
            region_name="us-east-1",
        )
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
            token_response = auth0Client.post(
                "/oauth/token",
                headers={"content-type": "application/json"},
                data=payload,
            )
            token_response.raise_for_status()
            token_json = token_response.json()

            logging.info("Processing S3 event(s)...")
            # Extract information from the S3 event
            for s3_record in sns_message["Records"]:
                bucket_name = s3_record["s3"]["bucket"]["name"]
                object_key = s3_record["s3"]["object"]["key"]
                real_object_key = unquote_plus(
                    object_key
                )  # Decode URL-encoded object key

                logging.info("key = " + real_object_key)
                logging.info("bucket = " + bucket_name)
                metadata = head_object(bucket=bucket_name, key=real_object_key)
                # Check if the destination bucket exists, and create it if it doesn't
                bucket_exists = ensure_bucket_exists(
                    metadata["Metadata"]["org_bucket"], region="us-east-1"
                )
                if bucket_exists:
                    logging.info("Copying to organization bucket...")
                    destination_bucket_name = metadata["Metadata"]["org_bucket"]
                    real_file_name = os.path.basename(real_object_key)
                    destination_real_object_key = f"documents/{real_file_name}"
                    copy_s3_object(
                        source_bucket=bucket_name,
                        source_key=real_object_key,
                        dest_bucket=destination_bucket_name,
                        dest_key=destination_real_object_key,
                    )

                    logging.info("Creating source content...")
                    # I changed relative path from documents/filename to just filename
                    # TODO: right now duplicate records can be created. We need to check if the pdf exists already exists
                    create_src_content_response = exec_create_source_content(
                        source_content_type="supplemental-document",
                        relative_path=os.path.basename(destination_real_object_key),
                        workspace_id=metadata["Metadata"]["workspace_id"],
                        token=token_json["access_token"],
                    )
                    source_content_id = create_src_content_response["data"][
                        "createSourceContent"
                    ]
                    logging.info(f"Source content created with ID:{ source_content_id}")
                    logging.info(
                        f"Triggering pdf summary generation for bucket = {destination_bucket_name}, key = {destination_real_object_key}"
                    )

                    pdf_summary_response = exec_generate_pdf_summaries(
                        {
                            "source_content_id": source_content_id,
                        },
                        token_json["access_token"],
                    )
                    results.append(
                        {
                            "source_content_id": source_content_id,
                            "bucket": destination_bucket_name,
                            "key": destination_real_object_key,
                            "pdf_summary_response": pdf_summary_response,
                        }
                    )

    return results


def exec_generate_pdf_summaries(event, token):
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
