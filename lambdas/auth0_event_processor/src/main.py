import json
import os
from typing import Any

import botocore
from aws_secretsmanager_caching import SecretCache, SecretCacheConfig

# Initialize secrets manager client and cache at module level
sm_client = botocore.session.get_session().create_client("secretsmanager")
cache_config = SecretCacheConfig()
cache = SecretCache(config=cache_config, client=sm_client)

# Load Modal secrets and set environment variables at module initialization
modal_secrets = json.loads(cache.get_secret_string(os.getenv("MODAL_SECRET_NAME")))
os.environ["MODAL_TOKEN_ID"] = modal_secrets["MODAL_TOKEN_ID"]
os.environ["MODAL_TOKEN_SECRET"] = modal_secrets["MODAL_TOKEN_SECRET"]
os.environ["MODAL_ENVIRONMENT"] = modal_secrets["MODAL_ENVIRONMENT"]

# Import Modal SDK after setting environment variables
import modal


def handler(event: dict, context: Any) -> dict[str, Any]:
    """Process Auth0 events by invoking Modal function."""
    modal_environment = os.getenv("MODAL_ENVIRONMENT")
    auth0_event_handler = modal.Function.from_name(
        "auth0_sync",
        "process_auth0_events",
        environment_name=modal_environment,
    )

    result = auth0_event_handler.remote(event)
    print(f"Modal function result: {result}")

    return {"statusCode": 200, "body": "Event processed successfully"}
