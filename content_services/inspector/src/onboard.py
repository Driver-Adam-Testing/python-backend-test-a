import hashlib
import os
from pathlib import Path
from uuid import UUID, uuid4

import modal
from common import app
from database.models_v1 import (
    Codebase,
    DerivedContent,
    Enum_Codebase_Status,
    Enum_Derived_Content_Status,
    InspectionVersion,
    Workspace,
)
from onboarding.onboard_utils import (
    create_bucket_if_dne,
    download_repo_zip,
    get_source_content_type_uuid,
    is_on_blacklist,
    run_file_stats_and_reencode,
    unpack_archive,
    upload_file_to_s3,
)
from sqlmodel import Session, select

image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("tree")
    .copy_local_dir("../../driver_db/", remote_path="/driver_db")
    .copy_local_dir(local_path="../../packages/shared", remote_path="/packages/shared")
    .poetry_install_from_file(
        "pyproject.toml"
    )  # TODO clean this up since inspector doesn't use pyproject install
)


# TODO detect if we already have a version for the docs.


@app.function(
    image=image,
    # Doesn't seem like these are needed
    mounts=[
        # modal.Mount.from_local_python_packages("utils"),
        # modal.Mount.from_local_dir(
        #     local_path="../../driver_db/certs/",
        #     remote_path="/root/data/",
        # ),
    ],
    secrets=[modal.Secret.from_name("aws-inspector-s3"), modal.Secret.from_name("db")],
    proxy=modal.Proxy.from_name("pg-proxy")
    if os.environ["MODAL_ENVIRONMENT"] != "staging"
    else None,
    timeout=60 * 60,
    region="us-east",
    concurrency_limit=5,
)
def run_codebase_onboarding(
    repo_url: str, commit: str, workspace_id: UUID
) -> tuple[str, str]:
    from database.db import (
        engine,  # We defer the import since we'll have the secrets set here
    )
    # Make sure there is a codebase, a new version (associated with a prior version if the codebase exists),
    # and a derived content record for the codebase.
    # TODO move to function

    # TODO this will need to be adjusted to support zip files from other sources again, but stay simple for now
    repo_name, download_root = download_repo_zip(repo_url, commit)

    # We could defer extraction if we know the repo name as we do here.
    extracted_path = unpack_archive(download_root, override_codebase_name=repo_name)
    print(f"Extracted {repo_url} for repo {repo_name} to {extracted_path}")
    # print(run_tree(extracted_path))

    with Session(engine) as session, session.begin():
        codebase_type_id = get_source_content_type_uuid("codebase")
        workspace = session.get(Workspace, workspace_id)
        if not workspace:
            raise ValueError(f"Workspace with id {workspace_id} not found")
        org_id = workspace.organization_id
        codebase = session.exec(
            select(Codebase).where(
                Codebase.codebase_name == repo_name,
                Codebase.workspace_id == workspace_id,
            )
        ).first()
        if codebase:
            # Get prior version; there should be one if the codebase exists and was onboarded since we added code diffs
            codebase_id = codebase.id
            statement = (
                select(InspectionVersion)
                .join(DerivedContent)
                .join(Workspace)
                .where(
                    DerivedContent.codebase_id == codebase_id,
                    Workspace.organization_id == org_id,
                    DerivedContent.content_type_id == codebase_type_id,
                    InspectionVersion.version.isnot(None),
                )
                # .distinct(InspectionVersion.id)
                .order_by(InspectionVersion.created_at.desc())
            )
            prior_version = session.exec(statement).first()
            if not prior_version:
                raise ValueError(
                    f"Codebase {codebase.codebase_name} has no prior version."
                )
            prior_version_name = prior_version.version
        else:
            prior_version = None
            prior_version_name = None
            codebase_id = uuid4()

        # TODO think about what happens when the file analysis fails. What do we do with the version record and uploaded content?
        # We can't just delete the whole codebase anymore since we have code diffs.

        version = InspectionVersion(
            id=uuid4(),
            version=commit,
            display_name=commit,
            previous_version_id=prior_version.id if prior_version else None,
        )
        session.add(version)
        version_id = version.id

        # TODO: this storage URL on codebase is WRONG. It can't be tied to a version!
        # but it seems we don't use storage url now anyways?

        if not codebase:
            codebase = Codebase(
                id=codebase_id,
                codebase_name=repo_name,
                creator_id=None,
                description="",
                storage_url=None,
                workspace_id=workspace_id,
                status=Enum_Codebase_Status.processing,
            )
            session.add(codebase)

        cb_sc = DerivedContent(
            codebase_id=codebase_id,
            relative_path=repo_name,
            content_type_id=codebase_type_id,
            workspace_id=workspace_id,
            misc_metadata={},
            status=Enum_Derived_Content_Status.generating,
            version_id=version_id,
        )
        session.add(cb_sc)

    org_id_bucket = hashlib.sha256(org_id.encode()).hexdigest()[:63]
    create_bucket_if_dne(org_id_bucket)

    # TODO need to handle dropzone location changes upstream of this. Not pertinent yet.
    version_fragment = f"{codebase_id}/version/{version_id}"
    s3_dest_root = Path(version_fragment) / "source"

    all_directories = []
    codebase_stats = {}
    for root, _, files in os.walk(extracted_path):
        all_directories.append(root)
        for filename in files:
            local_path = Path(root) / filename

            file_stats = run_file_stats_and_reencode(
                local_path,
            )
            codebase_stats[local_path] = file_stats
            if not codebase_stats[local_path]["is_blacklisted"]:
                uploaded_dest_path = upload_file_to_s3(
                    org_id_bucket, s3_dest_root, local_path
                )
                print(f"Uploaded {local_path} to {uploaded_dest_path}")

    with Session(engine) as session, session.begin():
        # Add directories source contents
        dir_sc_uuid = get_source_content_type_uuid("codebase-directory")
        for directory in all_directories:
            if not is_on_blacklist(Path(directory)):
                # TODO: analysis metadata for directories?
                # TODO: this is fragile - consider using DAG logic here
                dir_sc = DerivedContent(
                    codebase_id=codebase_id,
                    relative_path=directory,
                    content_type_id=dir_sc_uuid,
                    workspace_id=workspace_id,
                    misc_metadata={},
                    version_id=version_id,
                )
                session.add(dir_sc)
                print(f"Created but not committed source content for: {directory}.")

        # Add file source contents
        for file_path in codebase_stats:
            if not codebase_stats[file_path]["is_blacklisted"]:
                file_sc_type = get_source_content_type_uuid("codebase-file")
                file_sc = DerivedContent(
                    codebase_id=codebase_id,
                    relative_path=str(file_path),
                    content_type_id=file_sc_type,
                    workspace_id=workspace_id,
                    misc_metadata=codebase_stats[file_path],
                    version_id=version_id,
                )
                session.add(file_sc)

                print(
                    f"Created but not committed source content for: {file_path}. Processable: {codebase_stats[file_path]['is_analyzable']}. Stats: {codebase_stats[file_path]}"
                )
    if prior_version_name:
        print(
            f"Codebase onboarding complete for codebase: {repo_name} (cb id: {codebase_id}). "
            f"Version: {version_id} (for commit sha: {commit}). "
            f"Prior version commit sha: {prior_version_name}."
        )
    else:
        print(
            f"Codebase onboarding complete for codebase: {repo_name} (cb id: {codebase_id}). "
            f"Version: {version_id} (for commit sha: {commit})"
        )

    return str(codebase_id), str(version_id)
