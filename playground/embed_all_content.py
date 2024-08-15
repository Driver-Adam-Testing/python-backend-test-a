import hashlib
import os
from multiprocessing import Process

import boto3
from database.db import engine
from database.models_v1 import ChunkAndEmbedding, DerivedContent, DerivedContentType
from shared.chunking.text_splitter import split_text
from shared.embedding.text_embedder import batch_embed_text
from sqlalchemy.orm import selectinload
from sqlmodel import Session, delete, select

BATCH_SIZE = 1000


class S3BucketAccess:
    def __init__(self, organization_id: str, codebase_id: str):
        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_REGION"),
            endpoint_url=os.getenv("AWS_S3_ENDPOINT_URL")
            if os.getenv("AWS_S3_ENDPOINT_URL")
            else None,
        )
        self.organization_id_hashed = self._hash_organization_id(organization_id)
        self.codebase_id = codebase_id

    def _hash_organization_id(self, organization_id: str) -> str:
        # Hash the organization_id and take the first 63 characters to use as the bucket name
        return hashlib.sha256(organization_id.encode()).hexdigest()[:63]

    def get_file_path(self, relative_path: str, prefix: str = "/source") -> str:
        if prefix:
            relative_path = f"{prefix}/{relative_path.lstrip('/')}"
        # Ensure the leading slash is removed from the final path to avoid incorrect key generation
        return f"{self.codebase_id}/{relative_path.lstrip('/')}"

    def upload_file(self, file_path: str, relative_path: str) -> None:
        s3_path = self.get_file_path(relative_path)
        self.s3_client.upload_file(file_path, self.organization_id_hashed, s3_path)

    def list_files(self, prefix: str = "") -> list:
        full_prefix = f"{self.codebase_id}/{prefix}"
        response = self.s3_client.list_objects_v2(
            Bucket=self.organization_id_hashed, Prefix=full_prefix
        )
        return [
            obj["Key"]
            for obj in response.get("Contents", [])
            if obj["Key"] != full_prefix
        ]

    def get_signed_upload_url(self, relative_path: str, expiration=3600) -> str:
        """Generate a signed URL for uploading files. Expiration time is in seconds."""
        file_path = self.get_file_path(relative_path)
        return self.s3_client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": self.organization_id_hashed,
                "Key": file_path,
                "ContentType": "application/pdf",
            },
            ExpiresIn=expiration,
        )

    def get_signed_download_url(self, relative_path: str, expiration=3600) -> str:
        """Generate a signed URL for downloading files. Expiration time is in seconds."""
        file_path = self.get_file_path(relative_path, prefix="")
        return self.s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.organization_id_hashed, "Key": file_path},
            ExpiresIn=expiration,
        )

    def get_file_content(self, relative_path: str, prefix: str = "/source") -> str:
        """Return the content of a file from S3."""
        file_path = self.get_file_path(relative_path, prefix)
        try:
            obj = self.s3_client.get_object(
                Bucket=self.organization_id_hashed, Key=file_path
            )
            file_content = obj["Body"].read()
            if relative_path.endswith(".pdf"):
                return file_content
            else:
                return file_content.decode("utf-8", errors="replace")
        except self.s3_client.exceptions.NoSuchKey:
            print(
                f"The file at {file_path} does not exist in the bucket {self.organization_id_hashed}."
            )
            return ""


def process_derived_content(offset):
    with Session(engine) as session:
        derived_content_batch = session.exec(
            select(DerivedContent)
            .options(selectinload(DerivedContent.content_type))
            .options(selectinload(DerivedContent.workspace))
            .order_by(DerivedContent.created_at)
            .outerjoin(
                ChunkAndEmbedding, ChunkAndEmbedding.content_id == DerivedContent.id
            )
            .where(ChunkAndEmbedding.id.is_(None))
            .where(
                DerivedContent.content_type.has(
                    DerivedContentType.type_name.notin_(
                        [
                            "architecture_diagram",
                            "codebase-directory",
                            "supplemental-document",
                        ]
                    )
                )
            )
            .offset(offset)
            .limit(BATCH_SIZE)
        ).all()

        if not derived_content_batch:
            return False

        for content in derived_content_batch:
            # Delete existing ChunkAndEmbedding records that point at the current DerivedContent
            deleted_records = session.exec(
                delete(ChunkAndEmbedding).where(
                    ChunkAndEmbedding.content_id == content.id
                )
            )
            session.commit()
            if deleted_records.rowcount > 0:
                print(
                    f"Deleted {deleted_records.rowcount} ChunkAndEmbedding records for content ID {content.id}"
                )

            if not derived_content_batch:
                break
            text_content = content.content
            if content.misc_metadata and not content.misc_metadata.get(
                "is_analyzable", True
            ):
                continue
            if content.content_type.type_name == "symbol":
                text_content = content.misc_metadata.get("description", None)

            if content.source_content_id is None:
                if not text_content:
                    try:
                        s3_access = S3BucketAccess(
                            organization_id=content.workspace.organization_id,
                            codebase_id=content.codebase_id,
                        )
                        text_content = s3_access.get_file_content(
                            relative_path=content.relative_path
                        )
                        if not text_content:
                            print(
                                f"Failed to fetch content from S3 for {content.relative_path}"
                            )
                    except Exception as e:
                        print(
                            f"An error occurred while accessing S3 for {content.relative_path}: {e}"
                        )
                        text_content = None
            if not text_content:
                print(
                    f"ERROR: {content.content_type.type_name} : {content.relative_path}"
                )
                continue

            splits = split_text(str(text_content))

            embeds = batch_embed_text(splits)
            try:
                for i, split in enumerate(splits):
                    chunk_and_embedding = ChunkAndEmbedding(
                        content_id=content.id,
                        text=split.text,
                        text_embedding_3_small=embeds[i],
                        chunk_number=i,
                    )
                    session.add(chunk_and_embedding)
                session.commit()
                print(
                    f"{content.content_type.type_name} : {len(splits)} chunks. : {content.relative_path} "
                )
            except Exception as e:
                print(f"Error processing content {content.relative_path}: {e}")
                continue
        return True


def main():
    processes = []
    for _ in range(100):
        for i in range(20):
            offset = i * BATCH_SIZE
            p = Process(target=process_derived_content, args=(offset,))
            processes.append(p)
            p.start()

        for p in processes:
            p.join()


if __name__ == "__main__":
    main()
