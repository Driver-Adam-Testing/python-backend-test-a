from typing import Any

from pydantic import BaseModel, field_validator


class UploadRequestBase(BaseModel):
    file_path: str

    @field_validator("file_path")
    def must_be_zip(cls, v: Any) -> Any:
        if not v.lower().endswith(".zip"):
            raise ValueError("file_path must be a zip file")
        return v


class UploadCodebaseRequest(UploadRequestBase):
    pass


class UploadPDFRequest(UploadRequestBase):
    pass


class UploadResponse(BaseModel):
    upload_url: str
