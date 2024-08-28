from pydantic import BaseModel
from typing import Literal
from uuid import UUID

class Instruction(BaseModel):
    call_id: str
    status: str = list(Literal["running", "completed", "expired", "failed"])
    response: None | str
    error: str
    references: list[str]


class ExecuteInstructionRequest(BaseModel):
    workspace_id: UUID
    codebase_id: UUID
    prompt: str


class ExecuteInstructionResponse(BaseModel):
    call_id: str


class InstructionResultRequest(BaseModel):
    call_id: str


class BatchInstructionResultsRequest(BaseModel):
    call_ids: list[str]


class InstructionResultsResponse(BaseModel):
    data: list[Instruction]
