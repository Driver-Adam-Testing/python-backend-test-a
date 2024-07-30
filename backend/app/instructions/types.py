from pydantic import BaseModel
from typing import List


class Instruction(BaseModel):
    call_id: str = None
    status: str = None
    response: str = None
    error: str = None
    references: List[str] = None


class ExecuteInstructionRequest(BaseModel):
    workspace_id: str
    codebase_id: str
    prompt: str


class ExecuteInstructionResponse(BaseModel):
    call_id: str = None


class InstructionResultRequest(BaseModel):
    call_id: str = None


class BatchInstructionResultsRequest(BaseModel):
    call_ids: List[str]


class InstructionResultsResponse(BaseModel):
    data: List[Instruction]
