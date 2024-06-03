import hashlib
from urllib.parse import quote_plus

import boto3

from app.core.config import settings


class S3BucketAccess:
    def __init__(self, organization_id: str, codebase_id: str):
        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
        )
        self.bucket_name = settings.BUCKET_NAME
        self.organization_id_hashed = self._hash_organization_id(organization_id)
        self.codebase_id = codebase_id

    def _hash_organization_id(self, organization_id: str) -> str:
        return hashlib.sha256(organization_id.encode()).hexdigest()

    def get_file_path(self, relative_path: str, prefix: str = "/source") -> str:
        if prefix:
            relative_path = f"{prefix}/{relative_path.lstrip('/')}"
        # Ensure the leading slash is removed from the final path to avoid incorrect key generation
        return f"{self.organization_id_hashed}/{self.codebase_id}/{relative_path.lstrip('/')}"

    def download_file(self, relative_path: str, download_path: str) -> None:
        file_path = self.get_file_path(relative_path)
        self.s3_client.download_file(self.bucket_name, file_path, download_path)

    def upload_file(self, file_path: str, relative_path: str) -> None:
        s3_path = self.get_file_path(relative_path)
        self.s3_client.upload_file(file_path, self.bucket_name, s3_path)

    def list_files(self, prefix: str = "") -> list:
        full_prefix = f"{self.organization_id_hashed}/{self.codebase_id}/{prefix}"
        response = self.s3_client.list_objects_v2(
            Bucket=self.bucket_name, Prefix=full_prefix
        )
        return [
            obj["Key"]
            for obj in response.get("Contents", [])
            if obj["Key"] != full_prefix
        ]

    def get_signed_upload_url(self, relative_path: str, expiration=3600) -> str:
        """Generate a signed URL for uploading files. Expiration time is in seconds."""
        file_path = self.get_file_path(relative_path)
        # URL encode the file path to ensure special characters are correctly handled
        encoded_file_path = quote_plus(file_path)
        return self.s3_client.generate_presigned_url(
            "put_object",
            Params={"Bucket": self.bucket_name, "Key": encoded_file_path},
            ExpiresIn=expiration,
        )

    def get_file_content(self, relative_path: str, prefix: str = "/source") -> str:
        """Return the content of a file from S3."""
        file_path = self.get_file_path(relative_path, prefix)
        try:
            obj = self.s3_client.get_object(Bucket=self.bucket_name, Key=file_path)
            return obj["Body"].read().decode("utf-8")
        except self.s3_client.exceptions.NoSuchKey:
            print(
                f"The file at {file_path} does not exist in the bucket {self.bucket_name}."
            )
            return ""
