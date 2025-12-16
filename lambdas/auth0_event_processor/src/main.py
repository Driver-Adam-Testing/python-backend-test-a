import json
import os
from typing import Any

from src.firewall_cert import init_firewall_cert

init_firewall_cert()

import botocore
from aws_secretsmanager_caching import SecretCache, SecretCacheConfig

# Initialize secrets manager client and cache at module level
sm_client = botocore.session.get_session().create_client("secretsmanager")
cache_config = SecretCacheConfig()
cache = SecretCache(config=cache_config, client=sm_client)

# Load Hatchet token
os.environ["HATCHET_CLIENT_TOKEN"] = cache.get_secret_string(os.getenv("HATCHET_CLIENT_TOKEN_SECRET_NAME"))

# Import Modal SDK after setting environment variables
from hatchet_sdk import Hatchet


class ProcessAuth0EventInput:
    event: dict


def handler(event: dict, context: Any) -> dict[str, Any]:
    """Process Auth0 events by invoking Modal function."""
    hatchet = Hatchet()
    auth0_process_event_task = hatchet.stubs.task(
        "process-auth0-event-workflow", input_validator=ProcessAuth0EventInput
    )
    result = auth0_process_event_task.run(ProcessAuth0EventInput(event=event))

    print(f"Hatchet function result: {result}")

    return {"statusCode": 200, "body": "Event processed successfully"}
