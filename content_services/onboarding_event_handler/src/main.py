import json
from urllib.parse import unquote_plus

import botocore
import botocore.session
import httpx
from aws_secretsmanager_caching import SecretCache, SecretCacheConfig
from src.utils.aws_s3 import generate_get_presigned_url, head_object
from src.utils.config import settings


# Python lambdas have to be synchronous ¯\_(ツ)_/¯
# https://stackoverflow.com/questions/60455830/can-you-have-an-async-handler-in-lambda-python-3-6
def handler(event, context):
    # botocore.session.get_session().set_stream_logger('', logging.DEBUG)
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
                print(
                    f"Triggering codebase onboarding for bucket = {bucket_name}, key = {object_key}"
                )
                return exec_onboarding_service(
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


def exec_onboarding_service(event, token):
    with httpx.Client(base_url=settings.API_URL, follow_redirects=True) as driverClient:
        payload = {**event}
        print(payload)
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        }
        response = driverClient.post("/onboarding/", headers=headers, json=payload)
        response.raise_for_status()  # Raises an exception for 4XX/5XX responses
        event_response = response.json()
        print(event_response)
        # Make sure event was received successfully
        return "OK"
