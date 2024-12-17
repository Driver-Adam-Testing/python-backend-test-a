import hashlib
import json
import os
from datetime import datetime
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
    mounts=[
        modal.Mount.from_local_file(
            "src/onboarding/languages.yml", "/linguist/languages.yml"
        ),
    ],
    secrets=[modal.Secret.from_name("aws-inspector-s3"), modal.Secret.from_name("db")],
    proxy=modal.Proxy.from_name("pg-proxy")
    if os.environ["MODAL_ENVIRONMENT"] != "staging"
    else None,
    timeout=60 * 60,
    region="us-east",
    concurrency_limit=5,
    keep_warm=1,
)
def run_pre_codebase_analysis(
    presigned_url: str,
) -> str:
    from onboarding.onboard_utils import (
        delete_file_from_s3,
        download_file_from_presigned_url,
        get_file_type_from_extension,
        get_file_type_from_filename,
        load_driverignore,
        parse_presigned_url,
        run_file_stats_and_reencode,
        unpack_archive,
        wait_for_guard_duty_tag,
    )

    bucket, key = parse_presigned_url(presigned_url)
    if not wait_for_guard_duty_tag(bucket, key):
        print("GuardDuty found an issue with this codebase.")
        print("Deleting file from s3...")
        delete_file_from_s3(bucket, key)
        raise Exception("GuardDuty found an issue with this codebase.")

    temp_archive_name = "temp.zip"
    download_dest = Path(temp_archive_name)
    download_file_from_presigned_url(presigned_url, download_dest)

    print(f"Downloaded {temp_archive_name} from S3")

    # Override so unpack from github doesn't have hash in name.
    extracted_path = unpack_archive(download_dest)
    codebase_name = str(extracted_path)
    print("Codebase name : ", codebase_name)
    print("Unpacked archive to: ", extracted_path)

    driverignore = load_driverignore(codebase_root=extracted_path)

    codebase_stats = {
        "analyzable_bytes": 0,
        "analyzable_files": 0,
        "total_bytes": 0,
        "total_files": 0,
        "analyzable_files_by_extension": {},
        "analyzable_bytes_by_extension": {},
        "analyzable_files_by_type": {},
        "analyzable_bytes_by_type": {},
    }
    for root, _, files in os.walk(extracted_path):
        for filename in files:
            local_path = Path(root) / filename
            print(f"Analyzing {local_path}")
            file_stats = run_file_stats_and_reencode(
                local_path, driverignore=driverignore
            )

            if (
                file_stats["is_analyzable"]
                and not file_stats["is_blacklisted"]
                and not file_stats["is_ignored"]
            ):
                file_type = get_file_type_from_extension(file_stats["extension"])
                if not file_type:
                    file_type = get_file_type_from_filename(filename)
                if not file_type:
                    file_type = "Other"

                codebase_stats["analyzable_bytes"] += file_stats["size"]
                codebase_stats["analyzable_files"] += 1
                codebase_stats["total_bytes"] += file_stats["size"]
                codebase_stats["total_files"] += 1

                if (
                    file_stats["extension"]
                    not in codebase_stats["analyzable_files_by_extension"]
                ):
                    codebase_stats["analyzable_files_by_extension"][
                        file_stats["extension"]
                    ] = 0

                    codebase_stats["analyzable_bytes_by_extension"][
                        file_stats["extension"]
                    ] = 0
                codebase_stats["analyzable_files_by_extension"][
                    file_stats["extension"]
                ] += 1
                codebase_stats["analyzable_bytes_by_extension"][
                    file_stats["extension"]
                ] += file_stats["size"]

                if file_type not in codebase_stats["analyzable_files_by_type"]:
                    codebase_stats["analyzable_files_by_type"][file_type] = 0
                    codebase_stats["analyzable_bytes_by_type"][file_type] = 0
                codebase_stats["analyzable_files_by_type"][file_type] += 1
                codebase_stats["analyzable_bytes_by_type"][file_type] += file_stats[
                    "size"
                ]
            else:
                codebase_stats["total_bytes"] += file_stats["size"]
                codebase_stats["total_files"] += 1

    return json.dumps(codebase_stats)


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
    version_str: str | None = None,
    repository_id: str | None = None,
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
        UsageEventType,
        Workspace,
    )
    from onboarding.onboard_utils import (
        RunInProgressError,
        create_bucket_if_dne,
        download_file_from_presigned_url,
        get_codebase_content_record_status_for,
        get_org_id_from_workspace,
        get_source_content_type_uuid,
        is_on_blacklist,
        load_driverignore,
        run_file_stats_and_reencode,
        unpack_archive,
        upload_file_to_s3,
    )
    from shared.interfaces.usage.event_metadata import (
        UsageEventMetadata,
        UsageMetric,
        UsageSessionMetadata,
    )
    from shared.usage.llm_session import LLMUsageSession
    from shared.usage.usage_service import UsageService
    from shared.usage.utils import bytes_to_sloc
    from sqlmodel import Session, select

    if not version_str:
        version_str = "Unversioned"

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
    real_org_id = get_org_id_from_workspace(workspace_id)
    driverignore = load_driverignore(codebase_root=extracted_path)

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

            (
                prior_version_status,
                prior_version_id,
            ) = get_codebase_content_record_status_for(
                codebase_id=codebase_id, version_id=prior_version.id
            )
            if prior_version_status == Enum_Derived_Content_Status.generating:
                print(
                    f"Codebase {codebase.codebase_name} has a prior version name: {prior_version_name}"
                    f" id: {prior_version_id}"
                    f" that is still being processed or failed."
                )
                raise RunInProgressError()

        else:
            prior_version = None
            prior_version_name = None
            codebase_id = uuid4()

        # TODO think about what happens when the file analysis fails. What do we do with the version record and uploaded content?
        # We can't just delete the whole codebase anymore since we have code diffs.

        version = InspectionVersion(
            id=uuid4(),
            version=version_str,
            display_name=version_str,
            previous_version_id=prior_version.id if prior_version else None,
        )
        session.add(version)
        version_id = version.id

        # TODO: this storage URL on codebase is WRONG. It can't be tied to a version!
        # but it seems we don't use storage url now anyways?
        is_new_codebase = False
        if not codebase:
            is_new_codebase = True
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

        metadata = (
            {} if repository_id is None else {"github_repository_id": repository_id}
        )
        cb_sc = DerivedContent(
            codebase_id=codebase_id,
            relative_path=codebase_name,
            content_type_id=codebase_type_id,
            workspace_id=workspace_id,
            misc_metadata=metadata,
            status=Enum_Derived_Content_Status.generating,
            version_id=version_id,
        )
        session.add(cb_sc)
        usage_balance = UsageService(session).get_usage_balance(real_org_id)
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
                local_path=local_path,
                driverignore=driverignore,
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
            is_ignored = driverignore(directory) if driverignore is not None else False
            if not is_on_blacklist(Path(directory)) and not is_ignored:
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

        codebase_sloc = 0
        codebase_size_in_bytes = 0  # TODO:  rename to cumulative_codebase_size_in_bytes
        # Add file source contents
        for file_path in codebase_stats:
            if (
                not codebase_stats[file_path]["is_blacklisted"]
                and not codebase_stats[file_path]["is_ignored"]
            ):
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
                # Only add to SLOC and size if the file is analyzable
                if codebase_stats[file_path]["is_analyzable"]:
                    codebase_sloc += codebase_stats[file_path]["sloc"]
                    codebase_size_in_bytes += codebase_stats[file_path]["size"]

                    if (
                        is_new_codebase is True
                        and usage_balance.balance
                        < bytes_to_sloc(codebase_size_in_bytes)
                    ):
                        raise ValueError(
                            f"Insufficient balance to onboard codebase. "
                            f"Codebase size: {codebase_size_in_bytes}. "
                            f"Balance: {usage_balance.balance}"
                        )

                print(
                    f"Created but not committed source content for: {file_path}. Processable: {codebase_stats[file_path]['is_analyzable']}. Stats: {codebase_stats[file_path]}"
                )
    if prior_version_name:
        print(
            f"Codebase onboarding complete for codebase: {codebase_name} (cb id: {codebase_id}). "
            f"Version ID: {version_id}. "
            f"Prior version commit sha: {prior_version_name}."
        )
    else:
        print(
            f"Codebase onboarding complete for codebase: {codebase_name} (cb id: {codebase_id}). "
            f"Version ID: {version_id}."
        )
        session_meta = UsageSessionMetadata(
            content_type="codebase",
            content_id=str(codebase_id),
            content_name=codebase_name,
            version_id=str(version_id),
        )
        # need to get the real org id from the workspace since the org_id passed in is the hashed org_id

        with LLMUsageSession(real_org_id, creator_id, session_meta) as llm_session:
            usage_metric = UsageMetric(
                session_id=llm_session.session_id,
                organization_id=real_org_id,
                user_id=creator_id,
                event_source="codebase_onboarding",
                bytes_in=-codebase_size_in_bytes,
                bytes_out=0,
                tokens_in=0,
                tokens_out=0,
                timestamp=datetime.now(),
                event_type=UsageEventType.ONBOARDING_USAGE_DEBIT,
                event_metadata=UsageEventMetadata(
                    model="None",
                    provider="None",
                    input={},
                    output="",
                    sloc=codebase_sloc,
                ),
            )
            llm_session.send_event(usage_metric)
            # TODO: check usage balance guardrails here

    return str(codebase_id), str(version_id)
