from typing import Literal

from pydantic import BaseModel, Field, model_validator
from shared.usage.utils import bytes_to_sloc


class CodebaseAnalysisRequest(BaseModel):
    download_url: str


class CodebaseAnalysisResponse(BaseModel):
    call_id: str


class ModalFunctionCallResponse(BaseModel):
    call_id: str
    status: str = Literal["pending", "running", "completed", "error", "expired"]
    response: dict | None = None
    error: str = ""


class CodebaseAnalysisMetrics(BaseModel):
    analyzable_bytes: int
    analyzable_files: int
    total_bytes: int
    total_files: int
    analyzable_files_by_extension: dict[str, int]
    analyzable_bytes_by_extension: dict[str, int]
    analyzable_files_by_type: dict[str, int]
    analyzable_bytes_by_type: dict[str, int]
    # Compute the following metrics from the above data
    analyzable_sloc: int = Field(default=0, description="Computed analyzable sloc")
    total_sloc: int = Field(default=0, description="Computed total sloc")
    analyzable_sloc_by_type: dict[str, int, str] = Field(
        default={}, description="Computed analyzable sloc by type"
    )

    @model_validator(mode="before")
    def compute_analyzable_sloc(cls, values: dict) -> dict:
        values["analyzable_sloc"] = bytes_to_sloc(values["analyzable_bytes"])
        return values

    @model_validator(mode="before")
    def compute_total_sloc(cls, values: dict) -> dict:
        values["total_sloc"] = bytes_to_sloc(values["total_bytes"])
        return values

    @model_validator(mode="before")
    def compute_analyzable_sloc_by_type(cls, values: dict) -> dict:
        analyzable_bytes_by_type = values.get("analyzable_bytes_by_type", {})
        values["analyzable_sloc_by_type"] = {
            k: bytes_to_sloc(v) for k, v in analyzable_bytes_by_type.items()
        }
        return values


class CodebaseAnalysisResult(BaseModel):
    call_id: str
    status: str = Literal["pending", "running", "completed", "error", "expired"]
    result: CodebaseAnalysisMetrics | None = None
    error: str = ""
