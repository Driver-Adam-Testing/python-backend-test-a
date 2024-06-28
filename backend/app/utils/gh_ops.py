import hashlib
from typing import Any
import httpx
from app.core.config import settings
from app.utils.aws_s3 import generate_put_presigned_url


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


async def is_token_valid(token):
    url = "https://api.github.com/user"
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        return response.status_code == 200


async def refresh_access_token(refresh_token):
    url = "https://github.com/login/oauth/access_token"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        'client_id': settings.GH_CLIENT_ID,
        'client_secret': settings.GH_CLIENT_SECRET,
    }
    headers = {"Accept": "application/json"}
    async with httpx.AsyncClient() as client:
        response = await client.post(url, data=data, headers=headers)
        return response.json()  # This should contain the new 'access_token' and optionally a new 'refresh_token'


# fetch user orgs
async def fetch_repos(token: str) -> list[dict[str, Any]]:
    url = 'https://api.github.com/user/repos'
    headers = {
        'Authorization': f'token {token}'
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()  # Raises an exception for 4XX/5XX responses
            return response.json()
    except Exception as e:
        print(f"Failed to fetch repositories: {e}")
        raise e


async def download_and_upload_repo(org_name: str, owner: str, org_id: str, workspace_id: str, repo: str,
                                   access_token: str, provider: str = 'github') -> bool:
    github_url = f"https://api.github.com/repos/{org_name}/{repo}/zipball"
    org_id_hash = hashlib.sha256(org_id.encode()).hexdigest()[:63]
    upload_key = f"codebases/{org_id_hash}/{repo}.zip"

    codebase_metadata = {
        'organization_id': org_id_hash,
        'org_bucket': org_id_hash,
        'org_name': org_name,
        'workspace_id': workspace_id,
        'creator_id': owner,
        'file_path': upload_key,
        'codebase_name': repo,
        'content_type': 'codebase',
        'provider': provider,
    }
    print(codebase_metadata)
    try:
        s3_url = generate_put_presigned_url(key=upload_key, content_type="application/zip", metadata=codebase_metadata)
        print(s3_url)
        async with httpx.AsyncClient(follow_redirects=True, timeout=None) as client:
            # Download repository ZIP from GitHub
            response = await client.get(github_url, headers={'Authorization': f'token {access_token}'}, timeout=None)
            response.raise_for_status()
            # print(str(len(response.content)))
            # Upload the ZIP to S3 using the pre-signed URL
            upload_response = await client.put(s3_url, content=response.content, headers={
                'Content-Type': 'application/zip',
                'Content-Length': str(len(response.content))
            })
            upload_response.raise_for_status()
            print(f"Repository {repo} uploaded successfully to {upload_key}.")
            return upload_response.status_code == 200
    except httpx.RequestError as e:
        print(e)
        print(f"Failed to download repository: {e}")
    except Exception as e:
        print(e)
        print(f"Failed to upload repository: {e}")

    return False
