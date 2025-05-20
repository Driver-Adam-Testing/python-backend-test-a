import asyncio
import os
import re
import subprocess
import uuid
from pathlib import Path
from urllib.parse import urlparse

import httpx
from onboarding.gh_ops import fetch_github_default_branch_name


def extract_values_from_presigned_url(url: str) -> dict:
    parsed = urlparse(url)
    path = parsed.path.strip("/")

    pattern = r"^driver_docs/([^/]+)/([^/]+)/([^/]+)/([^/]+\.zip)$"
    match = re.match(pattern, path)

    if not match:
        raise ValueError("URL path does not match the expected structure.")

    primary_asset_id, version_id, filename = match.groups()

    return {
        "primary_asset_id": primary_asset_id,
        "version_id": version_id,
        "filename": filename,
    }


def run(
    cmd: str, cwd: str | None = None, check: bool = True
) -> subprocess.CompletedProcess:
    import subprocess

    print(f"> {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)
    if check and result.returncode != 0:
        raise subprocess.CalledProcessError(result.returncode, cmd)
    return result


def create_pull_request(
    full_name: str, branch: str, access_token: str, commit_slug: str
) -> None:
    """Create a pull request for the driver docs changes."""
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.github+json",
    }

    # First check for existing PRs for this branch
    with httpx.Client() as client:
        # Get existing PRs
        default_branch = fetch_github_default_branch_name(full_name, access_token)
        response = client.get(
            f"https://api.github.com/repos/{full_name}/pulls",
            headers=headers,
            params={"state": "open", "head": f"{full_name.split('/')[0]}:{branch}"},
        )
        response.raise_for_status()
        existing_prs = response.json()

        if existing_prs:
            # Update existing PR
            pr_number = existing_prs[0]["number"]
            update_response = client.patch(
                f"https://api.github.com/repos/{full_name}/pulls/{pr_number}",
                headers=headers,
                json={
                    "title": f"Update driver docs for version {commit_slug}",
                    "body": f"Automated update of driver documentation for version {commit_slug}",
                },
            )
            update_response.raise_for_status()
            print(f"✅ Updated existing PR: {existing_prs[0]['html_url']}")
            return

        # Create new PR if none exists
        pr_data = {
            "title": f"Update driver docs for commit {commit_slug}",
            "body": f"Automated update of driver documentation for commit {commit_slug}",
            "head": branch,
            "base": default_branch,
        }

        try:
            response = client.post(
                f"https://api.github.com/repos/{full_name}/pulls",
                headers=headers,
                json=pr_data,
            )
            response.raise_for_status()
            print(f"✅ Created PR: {response.json()['html_url']}")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 422:
                print("⚠️ No changes to create PR for - branch is up to date with main")
            else:
                raise


async def push_docs(version_id: uuid.UUID) -> None:
    # import boto3
    import hashlib
    import tempfile

    from onboarding.gh_ops import fetch_app_access_token, get_repo_clone_info_from_id
    from onboarding.onboard_utils import (
        unpack_archive_to_finalized_path,
    )
    from utils.db import get_version_by_id

    # parsed_values = extract_values_from_presigned_url(presigned_url)

    version = await get_version_by_id(version_id)
    primary_asset_id = version.primary_asset.id
    repo_id = version.primary_asset.repository_id
    org_id = version.primary_asset.organization_id
    org_id_hash = hashlib.sha256(org_id.encode()).hexdigest()[:63]

    with (
        tempfile.TemporaryDirectory() as temp_dir,
        tempfile.NamedTemporaryFile("w", suffix=".zip") as temp_file,
    ):
        # Override so unpack from github doesn't have hash in name.
        object_key = f"{primary_asset_id}/{version_id}/{version_id}_tech_docs.zip"
        download_meta = download_file_from_s3(org_id_hash, object_key, temp_file.name)
        # print(download_meta)
        install_id = download_meta["install_id"]

        extracted_path = unpack_archive_to_finalized_path(
            archive_path=Path(temp_file.name), extraction_root=Path(temp_dir)
        )
        commit_slug = version.display_name[:7]
        branch = f"docs_{commit_slug}"
        access_token = fetch_app_access_token(install_id)
        clone_url, full_name = get_repo_clone_info_from_id(repo_id, access_token)
        repo_dir = Path(temp_dir) / full_name
        target_dir = "driver_docs"
        if not os.path.exists(repo_dir):
            run(f"git clone {clone_url} {repo_dir}")

        run(f"git checkout -B {branch}", cwd=repo_dir)
        src_path = os.path.abspath(extracted_path)
        dst_path = repo_dir / "driver_docs"
        COMMIT_MESSAGE = "Bot: update driver docs for commit: " + commit_slug
        sync_directory(src_path, dst_path)

        run('git config user.name "docs-bot"', cwd=repo_dir)
        run('git config user.email "bot@example.com"', cwd=repo_dir)
        run(f"git add {target_dir}", cwd=repo_dir)

        diff = run("git diff --cached --quiet", cwd=repo_dir, check=False)
        if diff.returncode == 0:
            print("✅ No changes to commit.")
            return

        run(f'git commit -m "{COMMIT_MESSAGE}"', cwd=repo_dir)
        run(f"git push --force {clone_url} {branch}", cwd=repo_dir)
        print(f"✅ Pushed `{target_dir}` to `{branch}`")

        # Create a pull request after successful push
        create_pull_request(full_name, branch, access_token, commit_slug)


def sync_directory(src: str, dest: str) -> None:
    import shutil

    if os.path.exists(dest):
        shutil.rmtree(dest)
    shutil.copytree(src, dest)
    print(f"✅ Synced `{src}` to `{dest}`")


def download_file_from_s3(
    bucket_name: str, object_key: str, local_file_path: str
) -> dict:
    import boto3

    # Create an S3 client
    s3 = boto3.client("s3")
    response = s3.head_object(Bucket=bucket_name, Key=object_key)

    # Extract and print metadata
    metadata = response.get("Metadata", {})
    print(metadata)
    # Download the ZIP file
    s3.download_file(bucket_name, object_key, local_file_path)

    print(f"Downloaded {object_key} from bucket {bucket_name} to {local_file_path}")
    return metadata


def build_s3_path(org_id_hash: str, primary_asset_id: str, version_id: str) -> str:
    return f"driver_docs/{org_id_hash}/{primary_asset_id}/{version_id}/driver_docs.zip"


# pass a version_id to push_docs
# load the version from the db
# with the version you can derive the s3 path


async def main() -> None:
    # print(os.environ["ASYNC_DATABASE_URL"])
    # from onboard_utils import generate_get_presigned_url, upload_to_s3_with_metadata
    # from src.utils.db import get_version_by_id

    version_id = "d8b460f4-060c-4d24-abd5-cd5bc3c1d0eb"
    # local_docs_path = "/Users/ghostmac/Downloads/driver_docs.zip"
    # tech_docs_path = "64647130-650d-4c00-9104-799dc97be024/d8b460f4-060c-4d24-abd5-cd5bc3c1d0eb/d8b460f4-060c-4d24-abd5-cd5bc3c1d0eb_tech_docs.zip"
    # parsed_values = extract_values_from_presigned_url(tech_docs_path)
    # print(parsed_values)
    # version = await get_version_by_id(uuid.UUID(version_id))
    # primary_asset_id = version.primary_asset_id
    # org_id = version.primary_asset.organization_id
    # org_id_hash = hashlib.sha256(org_id.encode()).hexdigest()[:63]

    # with open(local_docs_path, "rb") as f:
    #     zip_content = f.read()
    # upload_key = build_s3_path(org_id_hash, primary_asset_id, version_id)
    # metadata = {
    #     "version_id": str(version_id),
    #     "provider": "github",
    #     "unhashed_organization_id": org_id,
    #     "installation_id": "65566326",
    # }
    # upload_to_s3_with_metadata(
    #     zip_content=zip_content, metadata=metadata, upload_key=upload_key
    # )
    # bucket = os.environ["DROPZONE_BUCKET_NAME"]
    # download_url = generate_get_presigned_url(bucket, upload_key)
    # print(f"Download URL: {download_url}")
    await push_docs(version_id)


if __name__ == "__main__":
    asyncio.run(main())
