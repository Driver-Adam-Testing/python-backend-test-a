from typing import Any
from uuid import UUID

from pydantic import BaseModel, field_validator


class UploadRequestBase(BaseModel):
    file_path: str


class UploadCodebaseRequest(UploadRequestBase):
    @field_validator("file_path")
    def must_be_zip(cls, v: Any) -> Any:  # noqa: ANN401
        if not v.lower().endswith(".zip"):
            raise ValueError("file_path must be a zip file")
        return v


class UploadPDFRequest(UploadRequestBase):
    @field_validator("file_path")
    def must_be_zip(cls, v: Any) -> Any:  # noqa: ANN401
        if not v.lower().endswith(".pdf"):
            raise ValueError("file_path must be a pdf file")
        return v


class UploadResponse(BaseModel):
    upload_url: str
    download_url: str


class PDFUploadResponse(BaseModel):
    upload_url: str
    source_content_id: UUID
