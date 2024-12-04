import hashlib
import os
from pathlib import Path
from uuid import UUID, uuid4

import modal
from common import app

image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("tree")
    .copy_local_dir("../../driver_db/", remote_path="/driver_db")
    .copy_local_dir(local_path="../../packages/shared", remote_path="/packages/shared")
    .poetry_install_from_file(
        "pyproject.toml"
    )  # TODO clean this up since inspector doesn't use pyproject install
    .pip_install(
        "requests"
    )  # TODO shouldn't be needed... in pyproject.toml RESOLVE THIS
)


# TODO detect if we already have a version for the docs.


@app.function(
    image=image,
    secrets=[modal.Secret.from_name("aws-inspector-s3"), modal.Secret.from_name("db")],
    proxy=modal.Proxy.from_name("pg-proxy")
    if os.environ["MODAL_ENVIRONMENT"] != "staging"
    else None,
    timeout=60 * 60,
    region="us-east",
    concurrency_limit=5,
)
def run_codebase_onboarding(
    presigned_url: str,
    archive_name: str,
    org_id: str,
    creator_id: str,
    workspace_id: UUID,
    provider: str = "manual",
    override_codebase_name: str | None = None,
    version: str | None = None,
) -> tuple[str, str]:
    from database.db import (
        engine,  # We defer the import since we'll have the secrets set here
    )
    from database.models_v1 import (
        Codebase,
        DerivedContent,
        Enum_Codebase_Status,
        Enum_Derived_Content_Status,
        InspectionVersion,
        Workspace,
    )
    from sqlmodel import Session, select

    from onboarding.onboard_utils import (
        create_bucket_if_dne,
        download_file_from_presigned_url,
        get_source_content_type_uuid,
        is_on_blacklist,
        run_file_stats_and_reencode,
        unpack_archive,
        upload_file_to_s3,
    )

    if not version:
        version = "Unversioned"

    download_dest = Path(archive_name)
    download_file_from_presigned_url(presigned_url, download_dest)

    print(f"Downloaded {archive_name} from S3")

    if provider == "github":
        override_codebase_name = archive_name.rsplit(".", 1)[0]

    # Override so unpack from github doesn't have hash in name.
    extracted_path = unpack_archive(
        download_dest, override_codebase_name=override_codebase_name
    )
    codebase_name = str(extracted_path)
    print("Codebase name: ", codebase_name)
    print("Unpacked archive to: ", extracted_path)

    # TODO this code needs the bug fix for nodes that on develop

    # TODO so if they uploaded a zip and we find the codebase, what do we do w.r.t versioning? Below, we disallow it
    # and raise an exception. Namely, the previously onboarded zip won't have a version.
    with Session(engine) as session, session.begin():
        codebase_type_id = get_source_content_type_uuid("codebase")
        workspace = session.get(Workspace, workspace_id)
        if not workspace:
            raise ValueError(f"Workspace with id {workspace_id} not found")
        org_id = workspace.organization_id
        codebase = session.exec(
            select(Codebase).where(
                Codebase.codebase_name == codebase_name,
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
            version=version,
            display_name=version,
            previous_version_id=prior_version.id if prior_version else None,
        )
        session.add(version)
        version_id = version.id

        # TODO: this storage URL on codebase is WRONG. It can't be tied to a version!
        # but it seems we don't use storage url now anyways?

        if not codebase:
            codebase = Codebase(
                id=codebase_id,
                codebase_name=codebase_name,
                creator_id=creator_id,
                description="",
                storage_url=None,
                workspace_id=workspace_id,
                status=Enum_Codebase_Status.processing,
            )
            session.add(codebase)

        cb_sc = DerivedContent(
            codebase_id=codebase_id,
            relative_path=codebase_name,
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
            f"Codebase onboarding complete for codebase: {codebase_name} (cb id: {codebase_id}). "
            f"Version: {version_id} (for commit sha: {version}). "
            f"Prior version commit sha: {prior_version_name}."
        )
    else:
        print(
            f"Codebase onboarding complete for codebase: {codebase_name} (cb id: {codebase_id}). "
            f"Version: {version_id} (for commit sha: {version})"
        )

    return str(codebase_id), str(version_id)
