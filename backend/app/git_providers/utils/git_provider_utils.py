from shared.file_storage.aws_s3_client import org_id_to_hash


def generate_codebase_metadata(
    org_id: str,
    org_name: str,
    repo: str,
    repo_id: str,
    owner: str,
    provider: str,
    commit: str,
    upload_key: str,
) -> dict:
    org_id_hash = org_id_to_hash(org_id)
    return {
        "unhashed_organization_id": org_id,
        "organization_id": org_id_hash,
        "org_bucket": org_id_hash,
        "org_name": org_name,
        "creator_id": owner,
        "file_path": upload_key,
        "codebase_name": repo,
        "content_type": "codebase",
        "provider": provider.lower(),
        "version": commit,
        "repository_id": repo_id,
    }
