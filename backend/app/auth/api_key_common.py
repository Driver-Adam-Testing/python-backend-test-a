import time

from database.models_v2 import ApiKey


def create_api_key_payload(api_key: ApiKey) -> dict:
    """
    Create JWT-shaped payload from ApiKey model.
    This shared logic ensures sync and async versions return identical results.
    """
    now = int(time.time())
    return {
        "org_id": api_key.organization_id,
        "org_name": "",  # TODO: populate when available
        "sub": api_key.user_id,
        "iss": "api_key",
        "aud": [],
        "iat": now,
        "exp": now + 10 * 365 * 24 * 3600,  # 10 years
        "scope": "",
        "azp": "",
        "permissions": [],
        "user_email": "",
        "user_full_name": "",
    }
