import json
import os
from urllib.parse import unquote_plus

import botocore
import botocore.session
import httpx
from aws_secretsmanager_caching import SecretCache, SecretCacheConfig
from src.utils.aws_s3 import generate_get_presigned_url, head_object
from src.utils.config import settings

# def handler(event, context):
#     print(event)


# # Python lambdas have to be synchronous ¯\_(ツ)_/¯
# # https://stackoverflow.com/questions/60455830/can-you-have-an-async-handler-in-lambda-python-3-6
def handler(event, context):
    # TODO - Verify org S3 bucket exists
    # const orgBucketExists = await storageService.bucketExists(orgBucket)
    # if (!orgBucketExists) {
    #         logger.warn(`Creating organization bucket`, {orgBucket})
    #         await storageService.createBucket(orgBucket)//organization.id!)
    #     }

    # TOOD - We should probably move bucket creation elsewhere so that these lambdas
    # don't require "Create Bucket" permissions. Maybe a "Create Organization"
    # endpoint that calls Auth0 for the org and creates the bucket at the same time.

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
            print("Fetching M2M token from Auth0...")
            # Fetch one M2M token per invocation of the lambda. This could be cached but would require additional impl similar to SecretCache above
            token_response = auth0Client.post(
                "/oauth/token",
                headers={"content-type": "application/json"},
                data=payload,
            )
            token_response.raise_for_status()  # Raises an exception for 4XX/5XX responses
            token_json = token_response.json()

            print("Processing S3 event(s)...")
            # Extract information from the S3 event
            for s3_record in sns_message["Records"]:
                bucket_name = s3_record["s3"]["bucket"]["name"]
                object_key = s3_record["s3"]["object"]["key"]
                real_object_key = unquote_plus(object_key)
                print("key = " + real_object_key)
                print("bucket = " + bucket_name)
                metadata = head_object(bucket=bucket_name, key=real_object_key)
                presigned_url = generate_get_presigned_url(
                    bucket=bucket_name, key=real_object_key
                )

                print("Creating source content...")
                # I changed relative path from documents/filename to just filename
                create_src_content_response = exec_create_source_content(
                    source_content_type="supplemental-document",
                    relative_path=os.path.basename(object_key),
                    workspace_id=metadata["Metadata"]["workspace_id"],
                    token=token_json["access_token"],
                )
                print("Source content created.")
                print(
                    f"Triggering document upload onboarding for bucket = {bucket_name}, key = {object_key}"
                )
                return exec_document_onboarding_service(
                    {
                        "download_url": presigned_url,
                        "object_key": object_key,
                        "org_id": metadata["Metadata"]["organization_id"],
                        "creator_id": metadata["Metadata"]["creator_id"],
                        "workspace_id": metadata["Metadata"]["workspace_id"],
                        "filepath": metadata["Metadata"]["file_path"],
                        # "codebase_name": metadata["Metadata"]["codebase_name"],
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
        print(event_response)
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
