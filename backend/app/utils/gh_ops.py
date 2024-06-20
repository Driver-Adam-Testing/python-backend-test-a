from typing import Any

import httpx
from app.core.config import settings


async def exchange_code_for_token(code: str) -> Any:
    url = 'https://github.com/login/oauth/access_token'
    payload = {
        'client_id': settings.GH_CLIENT_ID,
        'client_secret': settings.GH_CLIENT_SECRET,
        'code': code,
        'redirect_uri': settings.GH_REDIRECT_URI,
    }
    headers = {
        'Accept': 'application/json'
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, data=payload, headers=headers)
        response.raise_for_status()  # Raises an exception for 4XX/5XX responses

        token_data = response.json()
        if 'access_token' not in token_data:
            raise Exception('GitHub access token not found.')

        return token_data


# fetch user orgs


async def fetch_repos(token: str) -> list[dict[str, Any]]:
    url = 'https://api.github.com/user/repos'
    headers = {
        'Authorization': f'token {token}'
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()  # Raises an exception for 4XX/5XX responses

        return response.json()
