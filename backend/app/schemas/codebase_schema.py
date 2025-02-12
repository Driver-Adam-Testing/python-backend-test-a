import uuid
from typing import Literal

from pydantic import BaseModel, computed_field
from shared.usage.utils import bytes_to_sloc


class CodebaseAnalysisRequest(BaseModel):
    download_url: str


class CodebaseGenerationRequest(BaseModel):
    version_ids: list[uuid.UUID]


class CodebaseGenerationResponse(BaseModel):
    call_id: str


class CodebaseAnalysisResponse(BaseModel):
    call_id: str
    codebase_object_key: str


class ModalFunctionCallResponse(BaseModel):
    call_id: str
    status: str = Literal["pending", "running", "completed", "error", "expired"]
    response: dict | None = None
    error: str | None = None


class CodebaseAnalysisMetrics(BaseModel):
    analyzable_bytes: int
    total_bytes: int
    analyzable_files: int
    total_files: int
    analyzable_files_by_extension: dict[str, int]
    analyzable_files_by_type: dict[str, int]
    analyzable_bytes_by_extension: dict[str, int]
    analyzable_bytes_by_type: dict[str, int]

    @computed_field
    @property
    def analyzable_sloc(self) -> int:
        return bytes_to_sloc(self.analyzable_bytes)

    @computed_field
    @property
    def total_sloc(self) -> int:
        return bytes_to_sloc(self.total_bytes)

    @computed_field
    @property
    def analyzable_sloc_by_extension(self) -> dict[str, int]:
        values = {
            k: bytes_to_sloc(v) for k, v in self.analyzable_bytes_by_extension.items()
        }
        return values

    @computed_field
    @property
    def analyzable_sloc_by_type(self) -> dict:
        values = {k: bytes_to_sloc(v) for k, v in self.analyzable_bytes_by_type.items()}
        return values

    class Config:
        frozen = True


class CodebaseAnalysisResult(BaseModel):
    call_id: str
    status: str = Literal["pending", "running", "completed", "error", "expired"]
    result: CodebaseAnalysisMetrics | None = None
    error: str | None = None


class CodebaseOnboardRequest(BaseModel):
    codebase_object_key: str
    call_id: str
