import hashlib
import logging

import boto3
from app.core.config import settings

logger = logging.getLogger(__name__)


class S3BucketAccess:
    def __init__(
        self, organization_id: str, codebase_id: str, version_id: str | None = None
    ) -> None:
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
        self.version_id = version_id

    def _hash_organization_id(self, organization_id: str) -> str:
        # Hash the organization_id and take the first 63 characters to use as the bucket name
        return hashlib.sha256(organization_id.encode()).hexdigest()[:63]

    def get_file_path(self, relative_path: str, prefix: str = "source") -> str:
        # Ensure the leading slash is removed from the final path to avoid incorrect key generation
        if self.version_id:
            return f"{self.codebase_id}/version/{self.version_id}/{prefix}/{relative_path.lstrip('/')}"
        else:
            return f"{self.codebase_id}/{prefix}/{relative_path.lstrip('/')}"

    def upload_file(self, file_path: str, relative_path: str) -> None:
        s3_path = self.get_file_path(relative_path)
        self.s3_client.upload_file(file_path, self.organization_id_hashed, s3_path)

    def get_file_content(self, relative_path: str) -> str:
        """Return the content of a file from S3."""
        file_path = self.get_file_path(relative_path)
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
