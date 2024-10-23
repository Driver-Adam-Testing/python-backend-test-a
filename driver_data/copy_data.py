import argparse
import hashlib
import os
import shutil
import time
from uuid import UUID

import boto3
from database.models_v1 import (
    ChunkAndEmbedding,
    Codebase,
    DerivedContent,
    DerivedContentType,
    Workspace,
)
from dotenv import load_dotenv
from sqlmodel import Session, create_engine, select


def generate_content_type_mapping(
    source_session: Session, destination_session: Session
) -> dict:
    """Generate a mapping of content_type_id from source to destination based on type_name."""
    source_content_types = source_session.exec(select(DerivedContentType)).all()
    destination_content_types = destination_session.exec(
        select(DerivedContentType)
    ).all()

    source_to_destination_mapping = {}

    destination_mapping = {dct.type_name: dct.id for dct in destination_content_types}

    for sct in source_content_types:
        if sct.type_name in destination_mapping:
            source_to_destination_mapping[sct.id] = destination_mapping[sct.type_name]
        else:
            raise ValueError(
                f"Content type '{sct.type_name}' (ID {sct.id}) found in source "
                f"but not in destination"
            )
    return source_to_destination_mapping


def update_content_types(
    derived_contents: list[DerivedContent], content_type_mapping: dict
) -> None:
    for content in derived_contents:
        if content.content_type_id in content_type_mapping:
            content.content_type_id = content_type_mapping[content.content_type_id]
        else:
            raise ValueError(
                f"Content type ID '{content.content_type_id}' not found in the mapping"
            )


def copy_codebase(
    destination_session: Session,
    codebase: Codebase,
    new_workspace_id: UUID,
    new_storage_url: str,
    new_creator_id: str,
) -> None:
    codebase.workspace_id = new_workspace_id
    codebase.storage_url = new_storage_url
    codebase.creator_id = new_creator_id

    new_codebase = Codebase(**codebase.__dict__)
    destination_session.add(new_codebase)
    destination_session.flush()


def copy_derived_content(
    destination_session: Session,
    derived_contents: list[DerivedContent],
    new_workspace_id: UUID,
) -> None:
    # Group 1: Records with source_content_id as null (no dependency)
    no_source_content = [
        content for content in derived_contents if content.source_content_id is None
    ]

    # Group 2: Records with source_content_id not null (depends on earlier insertions)
    has_source_content = [
        content for content in derived_contents if content.source_content_id is not None
    ]

    for content in no_source_content:
        content.workspace_id = new_workspace_id
        new_dc = DerivedContent(**content.__dict__)
        destination_session.add(new_dc)

    destination_session.flush()

    for content in has_source_content:
        content.workspace_id = new_workspace_id
        new_dc = DerivedContent(**content.__dict__)
        destination_session.add(new_dc)

    destination_session.flush()


def copy_chunks_and_embeddings(
    source_session: Session,
    destination_session: Session,
    derived_content_ids: list[UUID],
) -> None:
    for i, derived_content_id in enumerate(derived_content_ids):
        print(
            f"Copying chunks for derived content ID {derived_content_id} ({i + 1}/{len(derived_content_ids)})"
        )

        chunks = source_session.exec(
            select(ChunkAndEmbedding).where(
                ChunkAndEmbedding.content_id == derived_content_id
            )
        ).all()
        print(f"Got {len(chunks)} chunks for derived content ID {derived_content_id}")
        new_chunks = [ChunkAndEmbedding(**chunk.__dict__) for chunk in chunks]
        destination_session.add_all(new_chunks)

    destination_session.flush()


def migrate_codebase_data(
    source_session: Session,
    destination_session: Session,
    codebase_id: UUID,
    new_workspace_id: UUID,
    new_storage_url: str,
    new_creator_id: str,
) -> None:
    """Migrate a single codebase and its related content from source to destination."""
    try:
        # Step 1: Generate the content type mapping from source to destination
        content_type_mapping_src_to_dest_id = generate_content_type_mapping(
            source_session, destination_session
        )

        type_names_to_embed = [
            "long_description",
            "symbol",
        ]
        types_ids_to_embed = source_session.exec(
            select(DerivedContentType.id).where(
                DerivedContentType.type_name.in_(type_names_to_embed)
            )
        ).all()
        assert (
            len(types_ids_to_embed) == 2
        ), f"Expected 2 types to embed, got {len(types_ids_to_embed)}"

        # Step 2: Fetch the codebase and associated derived content from the source
        codebase = source_session.exec(
            select(Codebase).where(Codebase.id == codebase_id)
        ).first()
        assert (
            codebase is not None
        ), f"Codebase with ID {codebase_id} not found in source"
        print("Fetched codebase:", codebase)

        start = time.time()

        columns = [
            DerivedContent.id,
            DerivedContent.content_type_id,
            DerivedContent.workspace_id,
            DerivedContent.source_content_id,
            DerivedContent.codebase_id,
            DerivedContent.relative_path,
            DerivedContent.content,
            DerivedContent.content_name,
            DerivedContent.misc_metadata,
            DerivedContent.status,
            DerivedContent.created_at,
            DerivedContent.updated_at,
            DerivedContent.order,
        ]
        column_names = [
            "id",
            "content_type_id",
            "workspace_id",  #: DerivedContent.workspace_id,
            "source_content_id",  #: DerivedContent.source_content_id,
            "codebase_id",  #: DerivedContent.codebase_id,
            "relative_path",  #: DerivedContent.relative_path,
            "content",  #: DerivedContent.content,
            "content_name",  # DerivedContent.content_name,
            "misc_metadata",  #: DerivedContent.misc_metadata,
            "status",  #: DerivedContent.status,
            "created_at",  #: DerivedContent.created_at,
            "updated_at",  #: DerivedContent.updated_at,
            "order",  #: DerivedContent
        ]

        fake_dc = source_session.exec(
            select(*columns).where(DerivedContent.codebase_id == codebase_id)
        ).all()

        derived_contents = [
            DerivedContent(**dict(zip(column_names, dc))) for dc in fake_dc
        ]
        derived_contents_to_embed = [
            dc for dc in derived_contents if dc.content_type_id in types_ids_to_embed
        ]

        print(f"Time taken to fetch derived content: {time.time() - start:.2f} seconds")

        derived_content_ids = [content.id for content in derived_contents]
        derived_content_ids_to_embed = [
            content.id for content in derived_contents_to_embed
        ]
        print(f"Derived content len: {len(derived_content_ids)}")

        # # Step 3: Update the content type IDs in derived content.
        update_content_types(derived_contents, content_type_mapping_src_to_dest_id)

        # Step 4: Copy the codebase with updated fields
        print("Step 4 starting...")
        copy_codebase(
            destination_session,
            codebase,
            new_workspace_id,
            new_storage_url,
            new_creator_id,
        )

        print("Step 5 starting...")
        # Step 5: Copy the derived content associated with the codebase (in proper order)
        copy_derived_content(destination_session, derived_contents, new_workspace_id)
        print("Step 6 starting...")
        # Step 6: Copy the chunks and embeddings for each derived content
        copy_chunks_and_embeddings(
            source_session, destination_session, derived_content_ids_to_embed
        )

        print("Migration complete!")

    except Exception as e:
        # In case of any failure, SQLAlchemy automatically rolls back the transaction
        destination_session.rollback()  # Roll back any changes made so far
        raise e
    destination_session.commit()


# TODO: This downloads S3 objects to local disk to get around cross-account
# permissions. This could fill up disk quickly (theory is that a single codebase
# at a time isn't likely to run into this as an issue - and everything
# is cleaned up after completion.)
def sync_s3_to_minio(bucket_name: str, codebase_id: UUID) -> None:
    src_session = boto3.Session(
        aws_access_key_id=os.getenv("SRC_AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("SRC_AWS_SECRET_ACCESS_KEY"),
    )
    target_session = boto3.Session(
        aws_access_key_id=os.getenv("TARGET_AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("TARGET_AWS_SECRET_ACCESS_KEY"),
    )
    src_s3 = src_session.resource("s3")
    src_bucket = src_s3.Bucket(bucket_name)
    target_s3 = target_session.client(
        service_name="s3",
        endpoint_url=os.getenv("TARGET_AWS_S3_ENDPOINT_URL"),
    )
    src_files = []
    for obj in src_bucket.objects.filter(Prefix=f"{codebase_id}"):
        print(f"Downloading {obj.key}")
        if not os.path.exists(os.path.dirname(obj.key)):
            os.makedirs(os.path.dirname(obj.key))
        src_bucket.download_file(obj.key, obj.key)
        src_files.append(obj.key)
    try:
        target_s3.head_bucket(Bucket=bucket_name)
        print("Bucket exists")
    except target_s3.exceptions.ClientError as e:
        error_code = int(e.response["Error"]["Code"])
        if error_code == 404:
            print("Bucket does not exist")
            target_s3.create_bucket(Bucket=bucket_name)
        else:
            print("Error checking for existence of target S3 bucket.")
    for src_file in src_files:
        print(f"Uploading {src_file}")
        target_s3.upload_file(src_file, bucket_name, src_file)

    print("Cleaning up...")
    shutil.rmtree(codebase_id)


def main(org_id: str, codebase_id: UUID) -> None:
    # Define the source and target database URLs
    source_database_url = os.getenv("SOURCE_DATABASE_URL")
    target_database_url = os.getenv("TARGET_DATABASE_URL")
    print(
        f"Migrating Org ID: {org_id} Codebase ID: {codebase_id} from \n\n{source_database_url}  \n\nto \n\n{target_database_url}\n\n"
    )

    # TODO: Download from S3 too
    bucket_name = hashlib.sha256(org_id.encode()).hexdigest()[:63]
    new_storage_url = f"http://localhost:9000/{bucket_name}/{codebase_id!s}"
    new_creator_id = "DRIVER_DATA_COPY"

    source_engine = create_engine(source_database_url)
    dest_engine = create_engine(target_database_url)

    with (
        Session(source_engine) as source_session,
        Session(dest_engine) as destination_session,
    ):
        destination_session.begin()
        with source_session.no_autoflush, destination_session.no_autoflush:
            default_workspace = destination_session.exec(
                select(Workspace)
                .where(Workspace.organization_id == org_id)
                .where(Workspace.display_name == "Default")
            ).first()
            if default_workspace is None:
                default_workspace = Workspace(
                    organization_id=org_id,
                    display_name="Default",
                    creator_id=new_creator_id,
                )
                destination_session.add(default_workspace)
                destination_session.commit()
                destination_session.refresh(default_workspace)
            migrate_codebase_data(
                source_session,
                destination_session,
                codebase_id,
                default_workspace.id,
                new_storage_url,
                new_creator_id,
            )
    sync_s3_to_minio(bucket_name, codebase_id)


if __name__ == "__main__":
    load_dotenv()
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--org-id",
        help="Organization ID to copy data from",
        required=True,
    )
    parser.add_argument(
        "--codebase-id",
        help="Codebase ID to copy data from",
        required=True,
    )
    args = parser.parse_args()
    main(args.org_id, args.codebase_id)
