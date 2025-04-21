import hashlib
import os
from uuid import UUID

import requests
from onboarding.onboard_utils import AccessTokenError, upload_to_s3_with_metadata
from shared.interfaces.aws_client_config import AWSClientConfig
from shared.secret_management.aws_secret_management import (
    AWSSecretManagementStrategy,
    format_secret_name,
)
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select


def fetch_access_token(installation_id: str) -> str:
    print(f"Fetching group access token for installation ID {installation_id}")
    install_key = format_secret_name("GIT_PROVIDER_GAT_INSTALL_SECRET", installation_id)
    secrets_manager = AWSSecretManagementStrategy(
        AWSClientConfig(
            region_name=os.environ["AWS_REGION"],
            aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
            aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
        )
    )
    secret_value = secrets_manager.read_secret(install_key)
    if not secret_value:
        raise AccessTokenError("Access token not found")

    group_access_tokens = secret_value["token"]

    return group_access_tokens


def download_repo(base_url: str, repo_id: str, commit: str, access_token: str) -> bytes:
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(
        f"{base_url}/api/v4/projects/{repo_id}/repository/archive.zip?sha={commit}",
        headers=headers,
        timeout=120,
        allow_redirects=True,
    )
    response.raise_for_status()
    return response.content


def generate_codebase_metadata(
    org_id: str,
    full_repo_name: str,
    repo_id: str | int,
    provider: str,
    version_id: str | UUID,
    asset_name: str,
) -> dict:
    from database.models_v2_enums import PrimaryAssetKind

    return {
        "unhashed_organization_id": org_id,
        "full_repo_name": full_repo_name,  # NOTE: just used for debugging
        "provider": provider,
        "version_id": str(version_id),
        "repository_id": str(repo_id),  # NOTE: just used for debugging
        "asset_name": asset_name,
        "asset_kind": PrimaryAssetKind.CODEBASE,
    }


def download_and_upload_repo(
    org_id: str, repo: dict, access_token: str, is_push: bool = False
) -> str | None:
    from database.db import engine
    from database.models_v1 import GitProviderAppInstallation
    from database.models_v2 import (
        PrimaryAsset,
        Version,
    )
    from database.models_v2_enums import (
        PrimaryAssetKind,
        VersionStatus,
    )
    from sqlalchemy.exc import IntegrityError

    repo_id = repo["metadata"]["id"]
    repo_name = repo["repo_name"]
    commit = repo["latest_commit"]["commit"]["id"]
    installation_id = repo["installation_id"]

    try:
        with Session(engine) as session, session.begin():
            app_install = session.exec(
                select(GitProviderAppInstallation).where(
                    GitProviderAppInstallation.id == installation_id
                )
            ).one()
            base_url = app_install.git_provider_app.base_url

            if is_push:
                primary_asset = session.exec(
                    select(PrimaryAsset)
                    .where(
                        PrimaryAsset.organization_id == org_id,
                        PrimaryAsset.repository_id == repo["id"],
                    )
                    .options(selectinload(PrimaryAsset.versions))
                ).first()
                if not primary_asset:
                    print(
                        f"Failed to find primary asset for {repo} for org: {org_id}, unable to process push event, unable to process push event"
                    )
                    return repo
                primary_asset_id = primary_asset.id
                if all(
                    v.status == VersionStatus.CONNECTED for v in primary_asset.versions
                ):
                    new_version = Version(
                        primary_asset_id=primary_asset.id,
                        display_name=commit,
                        status=VersionStatus.CONNECTING,
                        previous_version_id=primary_asset.versions[
                            0
                        ].id,  # TODO: don't link this for connected only?
                    )
                    session.add(new_version)
                    version_id = new_version.id
                elif any(
                    v.status
                    in [
                        VersionStatus.GENERATING,
                        VersionStatus.GENERATION_COMPLETE,
                        VersionStatus.GENERATION_ERROR,
                    ]
                    for v in primary_asset.versions
                ):
                    # versions are in descending order of creation
                    for version in primary_asset.versions:
                        if version.status in [
                            VersionStatus.GENERATION_COMPLETE,
                            VersionStatus.GENERATION_ERROR,
                        ]:
                            new_version = Version(
                                primary_asset_id=primary_asset.id,
                                display_name=commit,
                                status=VersionStatus.GENERATING,  # Immediately jump to generating. This signals run_codebase_connection to start inspection after connection
                                previous_version_id=version.id,
                            )
                            session.add(new_version)
                            version_id = new_version.id
                            break
                        elif version.status == VersionStatus.GENERATING:
                            print(
                                f"Version already in generating state for {repo_name}, skipping..."
                            )
                            return repo
                elif primary_asset.versions[0].status == VersionStatus.CONNECTING:
                    print(
                        f"Version already in connecting state for {repo_name}, skipping..."
                    )
                    return repo
                else:
                    # TODO: any other cases to handle explicitly?
                    return repo

            else:
                primary_asset = PrimaryAsset(
                    display_name=repo_name,
                    organization_id=org_id,
                    kind=PrimaryAssetKind.CODEBASE,
                    repository_id=repo_id,
                    installation_id=installation_id,
                )
                session.add(primary_asset)
                primary_asset_id = primary_asset.id

                version = Version(
                    primary_asset_id=primary_asset.id,
                    display_name=commit,
                    status=VersionStatus.CONNECTING,
                    previous_version_id=None,
                )
                session.add(version)
                version_id = version.id
                print(
                    f"Creating primary asset and version for {repo_name}:{commit} for org: {org_id}. Version ID: {version_id}"
                )
    except IntegrityError:
        print(
            f"Failed to create primary asset and version {repo_name}:{commit} for org: {org_id}"
        )
        return repo
    full_repo_name = repo["metadata"]["path_with_namespace"]
    # TODO: update this with additional metadata
    metadata = generate_codebase_metadata(
        org_id,
        full_repo_name,
        repo_id,
        "gitlab_enterprise_self_managed",
        version_id,
        repo_name,
    )

    zip_content = download_repo(base_url, repo_id, commit, access_token)
    print("Repository downloaded successfully. Size: %d bytes", len(zip_content))

    org_hashed_id = hashlib.sha256(org_id.encode("utf-8")).hexdigest()[:63]
    upload_key = (
        f"assets/{org_hashed_id}/{primary_asset_id}/{version_id}/{repo_name}.zip"
    )
    upload_to_s3_with_metadata(zip_content, metadata, upload_key)
    print(f"Repository {repo_name} uploaded successfully to {upload_key}.")

    return None
