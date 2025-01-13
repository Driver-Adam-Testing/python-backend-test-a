import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from uuid import uuid4

import modal
from common import app
from database.models_v2_enums import (
    ContentKind,
    NodeKind,
    PrimaryAssetKind,
    VersionStatus,
)

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
    provider: str = "manual",
    override_codebase_name: str | None = None,
    version_str: str | None = None,
    repository_id: str | None = None,
) -> str:
    from database.db import (
        engine,  # We defer the import since we'll have the secrets set here
    )
    from database.models_v1 import (
        DerivedContent,
        UsageEventType,
    )
    from database.models_v2 import (
        Node,
        PrimaryAsset,
        Version,
    )
    from onboarding.onboard_utils import (
        RunInProgressError,
        create_bucket_if_dne,
        download_file_from_presigned_url,
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
    driverignore = load_driverignore(codebase_root=extracted_path)

    # TODO so if they uploaded a zip and we find the codebase, what do we do w.r.t versioning? Below, we disallow it
    # and raise an exception. Namely, the previously onboarded zip won't have a version.
    with Session(engine) as session, session.begin():
        primary_asset = session.exec(
            select(PrimaryAsset).where(
                PrimaryAsset.display_name == codebase_name,
                PrimaryAsset.organization_id == org_id,
            )
        ).first()
        if primary_asset:
            # Get prior version; there should be one if the codebase exists and was onboarded since we added code diffs
            # TODO: VersionRow look up ONLY to check the status of the previous version is complete.
            primary_asset_id = primary_asset.id
            statement = (
                select(Version)
                .where(
                    PrimaryAsset.id == primary_asset_id,
                )
                .order_by(Version.created_at.desc())
            )
            prior_version = session.exec(statement).first()
            assert prior_version is not None, "Prior version should always be present"
            # TODO: check the provider - for manual providers we should not create a new version
            # if provider == "manual" and prior_version: raise
            prior_version_name = prior_version.display_name
            if prior_version.status == VersionStatus.GENERATING:
                print(
                    f"Codebase {primary_asset.display_name} has a prior version name: {prior_version_name}"
                    f" id: {prior_version.id}"
                    f" that is still being processed."
                )
                raise RunInProgressError()

        else:
            prior_version = None
            prior_version_name = None
            primary_asset_id = uuid4()

        is_new_primary_asset = False
        if primary_asset is None:
            is_new_primary_asset = True
            primary_asset = PrimaryAsset(
                id=primary_asset_id,
                display_name=codebase_name,
                organization_id=org_id,
                kind=PrimaryAssetKind.CODEBASE,
                repository_id=repository_id,
            )
            session.add(primary_asset)

        version = Version(
            primary_asset_id=primary_asset_id,
            display_name=version_str,
            status=VersionStatus.GENERATING,
            previous_version_id=prior_version.id if prior_version else None,
        )
        version_id = version.id
        session.add(version)

        usage_balance = UsageService(session).get_usage_balance(org_id)
    org_id_bucket = hashlib.sha256(org_id.encode()).hexdigest()[:63]
    create_bucket_if_dne(org_id_bucket)

    version_fragment = f"{primary_asset_id}/{version_id}"
    s3_dest_root = Path(version_fragment)

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
        # TODO: create nodes for directories
        for directory in all_directories:
            is_ignored = driverignore(directory) if driverignore is not None else False
            if not is_on_blacklist(Path(directory)) and not is_ignored:
                # TODO: analysis metadata for directories?
                # TODO: this is fragile - consider using DAG logic here
                formatted_dir = (
                    str(directory) + "/"
                    if not directory.endswith("/")
                    else str(directory)
                )
                dir_node = Node(
                    version_id=version_id,
                    relative_path=formatted_dir,
                    kind=NodeKind.CODEBASE_DIRECTORY,
                    misc_metadata={},
                )
                session.add(dir_node)
                print(f"Created but not committed source content for: {directory}.")

        codebase_sloc = 0
        codebase_size_in_bytes = 0  # TODO:  rename to cumulative_codebase_size_in_bytes
        # Add file source contents
        for file_path in codebase_stats:
            if (
                not codebase_stats[file_path]["is_blacklisted"]
                and not codebase_stats[file_path]["is_ignored"]
            ):
                node_id = uuid4()
                file_node = Node(
                    id=node_id,
                    version_id=version_id,
                    relative_path=str(file_path),
                    kind=NodeKind.CODEBASE_FILE,
                    misc_metadata=codebase_stats[file_path],
                )
                file_dc = DerivedContent(
                    content_type_id=None,
                    content_kind=ContentKind.CODEBASE_FILE,
                    node_id=node_id,
                    relative_path=str(
                        file_path
                    ),  # TODO: this should be removed from the model
                    content=None,
                    content_name=None,
                    misc_metadata=None,
                    status=None,
                )
                session.add(file_node)
                session.add(file_dc)
                # Only add to SLOC and size if the file is analyzable

                if codebase_stats[file_path]["is_analyzable"]:
                    codebase_sloc += codebase_stats[file_path]["sloc"]
                    codebase_size_in_bytes += codebase_stats[file_path]["size"]

                    if (
                        is_new_primary_asset is True
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
            f"Codebase onboarding complete for codebase: {codebase_name} (cb id: {primary_asset_id}). "
            f"Version ID: {version_id}. "
            f"Prior version commit sha: {prior_version_name}."
        )
    else:
        print(
            f"Codebase onboarding complete for codebase: {codebase_name} (cb id: {primary_asset_id}). "
            f"Version ID: {version_id}."
        )
        # TODO: do this inside the same transaction as creating the primary asset
        session_meta = UsageSessionMetadata(
            content_type="codebase",  # TODO enum
            content_id=str(primary_asset_id),
            content_name=codebase_name,
            version_id=str(version_id),
        )
        # need to get the real org id from the workspace since the org_id passed in is the hashed org_id

        with LLMUsageSession(org_id, creator_id, session_meta) as llm_session:
            usage_metric = UsageMetric(
                session_id=llm_session.session_id,
                organization_id=org_id,
                user_id=creator_id,
                event_source="codebase_onboarding",  # TODO make enum
                bytes_in=-codebase_size_in_bytes,
                bytes_out=0,
                tokens_in=0,
                tokens_out=0,
                timestamp=datetime.now(),  # TODO: enforce timezone aware datetime objects, always
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

    return str(version_id)
