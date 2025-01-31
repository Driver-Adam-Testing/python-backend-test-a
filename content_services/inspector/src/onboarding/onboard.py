import hashlib
import os
from pathlib import Path
from uuid import uuid4

import modal
from common import app
from database.models_v2_enums import (
    ContentKind,
    NodeKind,
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
)
def run_codebase_connection(
    presigned_url: str,
    archive_name: str,
    org_id: str,  # Not strictly necessary, but we can check that the version belongs to the org.
    provider: str = "manual",
    version_id: str | None = None,
) -> None:
    import tempfile

    from boto3 import resource
    from database.db import (
        engine,  # We defer the import since we'll have the secrets set here
    )
    from database.models_v1 import (
        DerivedContent,
    )
    from database.models_v2 import (
        Node,
        PrimaryAsset,
        Version,
    )
    from onboarding.onboard_utils import (
        create_bucket_if_dne,
        download_file_from_presigned_url,
        is_on_blacklist,
        load_driverignore,
        run_file_stats_and_reencode,
        unpack_archive,
    )
    from sqlalchemy.exc import IntegrityError
    from sqlmodel import Session, select, update

    download_dest = Path(archive_name)
    download_file_from_presigned_url(presigned_url, download_dest)

    print(f"Downloaded {archive_name} from S3")

    if provider == "github":
        override_codebase_name = archive_name.rsplit(".", 1)[0]

    with tempfile.TemporaryDirectory() as temp_dir:
        # Override so unpack from github doesn't have hash in name.
        extracted_path = unpack_archive(
            download_dest,
            override_codebase_name=override_codebase_name,
            extraction_path=temp_dir,
        )
        codebase_name = str(extracted_path.relative_to(temp_dir))
        print("Codebase name: ", codebase_name)
        print("Unpacked archive to: ", extracted_path)
        driverignore = load_driverignore(codebase_root=extracted_path)

        try:
            with Session(engine) as session, session.begin():
                primary_asset = session.exec(
                    select(PrimaryAsset)
                    .join(Version)
                    .where(
                        Version.id == version_id,
                        PrimaryAsset.organization_id == org_id,
                    )
                ).one()
                primary_asset.display_name = codebase_name
                primary_asset_id = primary_asset.id
                session.add(primary_asset)
        except IntegrityError:
            # TODO: send email
            print(
                f"Primary asset with name {codebase_name} already exists for org {org_id}. Setting status to connection failed."
            )
            with Session(engine) as session, session.begin():
                update_stmt = (
                    update(Version)
                    .where(Version.id == version_id)
                    .values(status=VersionStatus.CONNECTION_FAILED)
                )
                session.exec(update_stmt)
            return None

        org_id_bucket = hashlib.sha256(org_id.encode()).hexdigest()[:63]
        create_bucket_if_dne(org_id_bucket)

        version_fragment = f"{primary_asset_id}/{version_id}"
        s3_dest = Path(version_fragment) / f"{version_id}_source.zip"

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

        s3_resource = resource("s3", endpoint_url=os.environ.get("AWS_S3_ENDPOINT_URL"))
        s3_bucket = s3_resource.Bucket(org_id_bucket)
        s3_bucket.upload_file(Path(archive_name), str(s3_dest))
        print(f"Uploaded {archive_name} to {s3_dest}")
        with Session(engine) as session, session.begin():
            # Add directories source contents
            for directory in all_directories:
                directory_stats = {
                    "analyzable_bytes": 0,
                    "analyzable_files": 0,
                    "total_bytes": 0,
                    "total_files": 0,
                    "analyzable_files_by_type": {},
                    "analyzable_bytes_by_type": {},
                }
                is_ignored = (
                    driverignore(directory) if driverignore is not None else False
                )
                if not is_on_blacklist(Path(directory)) and not is_ignored:
                    directory_path = Path(directory).relative_to(temp_dir)
                    for file_path in codebase_stats:
                        if str(file_path).startswith(directory):
                            file_stats = codebase_stats[file_path]
                            directory_stats["total_bytes"] += file_stats["size"]
                            directory_stats["total_files"] += 1
                            if (
                                file_stats["is_analyzable"]
                                and not file_stats["is_blacklisted"]
                                and not file_stats.get("is_ignored", False)
                            ):
                                file_type = file_stats.get("language")
                                if file_type is None:
                                    file_type = "Other"
                                if (
                                    file_type
                                    not in directory_stats["analyzable_files_by_type"]
                                ):
                                    directory_stats["analyzable_files_by_type"][
                                        file_type
                                    ] = 0
                                    directory_stats["analyzable_bytes_by_type"][
                                        file_type
                                    ] = 0
                                directory_stats["analyzable_files_by_type"][
                                    file_type
                                ] += 1
                                directory_stats["analyzable_bytes_by_type"][
                                    file_type
                                ] += file_stats["size"]
                                directory_stats["analyzable_bytes"] += file_stats[
                                    "size"
                                ]
                                directory_stats["analyzable_files"] += 1
                    dir_node = Node(
                        version_id=version_id,
                        relative_path=str(directory_path),
                        kind=NodeKind.CODEBASE_DIRECTORY,
                        misc_metadata=directory_stats,
                    )
                    session.add(dir_node)
                    print(f"Created but not committed source content for: {directory}.")

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
                        relative_path=str(file_path.relative_to(temp_dir)),
                        kind=NodeKind.CODEBASE_FILE,
                        misc_metadata=codebase_stats[file_path],
                    )
                    # This is used to link the embeddings to the source code.
                    # TODO: There should be a cleaner way to do this.
                    file_dc = DerivedContent(
                        content_type_id=None,
                        content_kind=ContentKind.CODEBASE_FILE,
                        node_id=node_id,
                        relative_path=str(
                            file_path.relative_to(temp_dir)
                        ),  # TODO: this should be removed from the model
                        content=None,
                        content_name=None,
                        misc_metadata=None,
                        status=None,
                    )
                    session.add(file_node)
                    session.add(file_dc)

                    print(
                        f"Created but not committed source content for: {file_path}. Processable: {codebase_stats[file_path]['is_analyzable']}. Stats: {codebase_stats[file_path]}"
                    )
            update_stmt = (
                update(Version)
                .where(Version.id == version_id)
                .values(status=VersionStatus.CONNECTED)
            )
            session.exec(update_stmt)

    print(
        f"Codebase onboarding complete for codebase: {codebase_name} (cb id: {primary_asset_id}). "
        f"Version ID: {version_id}."
    )

    return None
