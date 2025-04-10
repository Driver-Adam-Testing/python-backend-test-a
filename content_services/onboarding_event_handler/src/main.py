import json
import logging
import os
from typing import Any
from urllib.parse import unquote_plus

import botocore
import httpx
from aws_secretsmanager_caching import SecretCache, SecretCacheConfig
from src.utils.aws_s3 import generate_get_presigned_url, has_guard_duty_tag, head_object
from src.utils.config import settings

log_level = os.environ.get("LOG_LEVEL").upper() or logging.INFO
if len(logging.getLogger().handlers) > 0:
    # The Lambda environment pre-configures a handler logging to stderr. If a handler is already configured,
    # `.basicConfig` does not execute. Thus we set the level directly.
    logging.getLogger().setLevel(log_level)
else:
    logging.basicConfig(level=log_level)

logger = logging.getLogger()
logger.info(f"Log level set to {log_level}")


# Python lambdas have to be synchronous ¯\_(ツ)_/¯
# https://stackoverflow.com/questions/60455830/can-you-have-an-async-handler-in-lambda-python-3-6
def handler(
    event: dict,
    context: Any,  # noqa: ANN401
) -> str:
    # Parse the SNS message
    for record in event["Records"]:
        sns_message = json.loads(record["Sns"]["Message"])

        sm_client = botocore.session.get_session().create_client("secretsmanager")
        cache_config = SecretCacheConfig()
        cache = SecretCache(config=cache_config, client=sm_client)

        client_id = (
            cache.get_secret_string(settings.CLIENT_ID_SECRET)
            if settings.ENVIRONMENT not in ["local", "cloud-local"]
            else settings.CLIENT_ID_SECRET
        )
        client_secret = (
            cache.get_secret_string(settings.CLIENT_SECRET_SECRET)
            if settings.ENVIRONMENT not in ["local", "cloud-local"]
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

        onboarded = []
        with httpx.Client(base_url=settings.AUTH0_URL) as auth0Client:
            logger.info("Fetching M2M token from Auth0...")
            # Fetch one M2M token per invocation of the lambda. This could be cached but would require additional impl similar to SecretCache above
            token_response = auth0Client.post(
                "/oauth/token",
                headers={"content-type": "application/json"},
                data=payload,
            )
            token_response.raise_for_status()  # Raises an exception for 4XX/5XX responses
            token_json = token_response.json()

            logger.info("Processing S3 event(s)...")
            for s3_record in sns_message["Records"]:
                bucket_name = s3_record["s3"]["bucket"]["name"]
                object_key = s3_record["s3"]["object"]["key"]
                real_object_key = unquote_plus(object_key)
                logger.info("key = " + real_object_key)
                logger.info("bucket = " + bucket_name)
                if (
                    has_guard_duty_tag(bucket=bucket_name, key=real_object_key)
                    or settings.ENVIRONMENT == "cloud-local"
                ):
                    logger.info("No threats found, continuing document onboarding")
                    metadata = head_object(bucket=bucket_name, key=real_object_key)
                    presigned_url = generate_get_presigned_url(
                        bucket=bucket_name, key=real_object_key
                    )
                    logger.info(
                        f"Triggering codebase onboarding for bucket = {bucket_name}, key = {object_key}"
                    )
                    request_body = {
                        "download_url": presigned_url,
                        "object_key": object_key,
                        "org_id": metadata["Metadata"]["unhashed_organization_id"],
                        "provider": metadata["Metadata"]["provider"],
                        "version_id": metadata["Metadata"]["version_id"],
                    }
                    onboarding_result = exec_onboarding_service(
                        request_body,
                        token_json["access_token"],
                    )
                    onboarded.append(onboarding_result)
                else:
                    # Handle THREATS_FOUND and other guard duty statuses
                    # TODO: send user email
                    logger.error("GuardDuty found something.")
        return onboarded


def exec_onboarding_service(event: dict[str, Any], token: str) -> dict[str, Any]:
    with httpx.Client(base_url=settings.API_URL, follow_redirects=True) as driverClient:
        payload = {**event}
        logger.debug(payload)
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        }
        response = driverClient.post("/onboarding/", headers=headers, json=payload)
        response.raise_for_status()  # Raises an exception for 4XX/5XX responses
        event_response = response.json()
        logger.info(event_response)
        return event_response
