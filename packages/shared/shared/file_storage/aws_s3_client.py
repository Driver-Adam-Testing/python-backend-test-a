import hashlib
from pathlib import Path

import boto3
import httpx
from shared.interfaces.aws_client_config import AWSClientConfig


def org_id_to_hash(organization_id: str) -> str:
    return hashlib.sha256(organization_id.encode("utf-8")).hexdigest()[:63]


class AWSS3Client:
    def __init__(self, aws_config: AWSClientConfig) -> None:
        self.aws_config = aws_config
        self.s3_client = boto3.client(
            "s3",
            region_name=self.aws_config.region_name,
            aws_access_key_id=self.aws_config.aws_access_key_id,
            aws_secret_access_key=self.aws_config.aws_secret_access_key,
        )

    #
    def generate_get_presigned_url(
        self, key: str, bucket: str, expires: int = 3600
    ) -> str:
        return self.s3_client.generate_presigned_url(
            ClientMethod="get_object",
            Params={
                "Bucket": bucket,
                "Key": key,
            },
            ExpiresIn=expires,
        )

    def generate_put_presigned_url(
        self,
        key: str,
        bucket: str,
        content_type: str,
        metadata: dict | None = None,
        expires: int = 3600,
    ) -> str:
        return self.s3_client.generate_presigned_url(
            ClientMethod="put_object",
            Params={
                "Bucket": bucket,
                "Key": key,
                "ContentType": content_type,
                "Metadata": metadata,
            },
            ExpiresIn=expires,
        )

    def get_presigned_url(self, organization_id: str, path: str) -> str:
        org_id_hash = hashlib.sha256(organization_id.encode("utf-8")).hexdigest()[:63]

        return self.generate_get_presigned_url(key=path, bucket=org_id_hash)

    def upload_to_s3(
        self, zip_content: bytes, metadata: dict, upload_key: str, bucket: str
    ) -> bool:
        s3_url = self.generate_put_presigned_url(
            key=upload_key,
            bucket=bucket,
            content_type="application/zip",
            metadata=metadata,
        )
        print(f"Uploading to S3: {s3_url}")
        if not s3_url:
            print("Failed to generate S3 pre-signed URL.")
            return False

        headers = {
            "Content-Type": "application/zip",
            "Content-Length": str(len(zip_content)),
        }
        response = httpx.put(s3_url, content=zip_content, headers=headers, timeout=120)
        response.raise_for_status()
        return response.status_code == 200

    def upload_file_to_s3(
        self,
        file_path: Path,
        bucket: str,
        upload_key: str,
        metadata: dict | None,
        content_type: str | None,
    ) -> None:
        extra_args = {}
        if metadata:
            extra_args["Metadata"] = metadata
        if content_type:
            extra_args["ContentType"] = content_type
        self.s3_client.upload_file(
            Filename=str(file_path),
            Bucket=bucket,
            Key=upload_key,
            ExtraArgs=extra_args,
        )

    def download_file_from_presigned_url(
        self, presigned_url: str, download_destination: Path
    ) -> None:
        with httpx.stream("GET", presigned_url) as r:
            r.raise_for_status()
            with open(download_destination, "wb") as w_file:
                for chunk in r.iter_bytes():
                    w_file.write(chunk)
