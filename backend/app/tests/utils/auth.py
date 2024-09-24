import requests
from app.core.config import settings


def get_auth0_token():
    url = f"https://{settings.AUTH0_DOMAIN}/oauth/token"
    payload = {
        "grant_type": "client_credentials",
        "client_id": settings.AUTH0_MGMT_API_CLIENT_ID,
        "client_secret": settings.AUTH0_MGMT_API_CLIENT_SECRET,
        "audience": settings.AUTH0_AUDIENCE,
        "organization": 'org_s76pU1v8LAYhTOWB'
    }
    headers = {"content-type": "application/json"}

    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()["access_token"]
