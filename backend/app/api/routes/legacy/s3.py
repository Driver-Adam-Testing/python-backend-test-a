import hashlib

import boto3

from app.core.config import settings


class S3BucketAccess:
    def __init__(self, organization_id: str, codebase_id: str):
        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
            endpoint_url=settings.AWS_S3_ENDPOINT_URL
            if settings.AWS_S3_ENDPOINT_URL
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
            Params={"Bucket": self.organization_id_hashed, "Key": file_path, "ContentType": "application/pdf"},
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
