import os
import re
import subprocess
import uuid
from pathlib import Path
from urllib.parse import urlparse


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

    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)
    if check and result.returncode != 0:
        raise subprocess.CalledProcessError(result.returncode, cmd)
    return result


async def push_docs(version_id: uuid.UUID) -> None:
    # import boto3
    import hashlib
    import shutil
    import tempfile

    from database.db import engine
    from database.models_v1 import GitProviderAppInstallation
    from onboarding import gh_ops, gitlab_ops
    from onboarding.onboard_utils import (
        unpack_archive_to_finalized_path,
    )
    from sqlmodel import Session, select
    from utils.db import get_version_by_id
    # parsed_values = extract_values_from_presigned_url(presigned_url)

    version = await get_version_by_id(version_id)
    primary_asset_id = version.primary_asset.id
    repo_id = version.primary_asset.repository_id
    repo_name = version.primary_asset.display_name
    org_id = version.primary_asset.organization_id
    org_id_hash = hashlib.sha256(org_id.encode()).hexdigest()[:63]

    is_github = version.primary_asset.installation_id is None

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
        if is_github:
            access_token = gh_ops.fetch_app_access_token(install_id)
            clone_url, full_name = gh_ops.get_repo_clone_info_from_id(
                repo_id, access_token
            )
        else:
            with Session(engine) as session:
                installation_id = version.primary_asset.installation_id
                app_install = session.exec(
                    select(GitProviderAppInstallation).where(
                        GitProviderAppInstallation.id == installation_id
                    )
                ).one()
                if app_install is None:
                    raise ValueError(f"Installation ID {installation_id} not found.")
                base_url = app_install.git_provider_app.base_url
            access_token = gitlab_ops.fetch_access_token(install_id)
            clone_url, full_name = gitlab_ops.get_repo_clone_info_from_id(
                base_url, repo_id, access_token
            )

        repo_dir = Path(temp_dir) / full_name
        target_dir = "driver_docs"
        if not os.path.exists(repo_dir):
            run(f"git clone {clone_url} {repo_dir}")

        run(f"git checkout -B {branch}", cwd=repo_dir)
        src_path = os.path.abspath(extracted_path)

        driver_docs_path = repo_dir / "driver_docs"
        if os.path.exists(driver_docs_path):
            # NOTE: only need to do this because previous iteration of export landed
            # directly in `driver_docs`. Once we start exporting other content,
            # we'll need a different approach.
            print(f"Removing existing driver_docs directory: {driver_docs_path}")
            shutil.rmtree(driver_docs_path)

        dst_path = repo_dir / "driver_docs" / repo_name
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

        if is_github:
            # Create a pull request after successful push
            gh_ops.create_pull_request(full_name, branch, access_token, commit_slug)
        else:
            # Create a merge request after successful push
            gitlab_ops.create_pull_request(
                base_url, repo_id, access_token, branch, commit_slug
            )


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
