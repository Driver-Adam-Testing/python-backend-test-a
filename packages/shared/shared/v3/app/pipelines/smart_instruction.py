from collections.abc import AsyncGenerator

from shared.v3.app.pipelines.pipeline_request import PipelineRequest
from shared.v3.app.pipelines.pipeline_response import PipelineResponse
from shared.v3.interfaces.llm_stream_response import (
    LlmStreamResponse,
)


class SmartInstructionPipelineResponse(PipelineResponse):
    pass


class SmartInstructionPipelineRequest(PipelineRequest):
    user_prompt: str
    page_content_before_cursor: str
    page_content_after_cursor: str
    selected_text: str

    def run(self) -> SmartInstructionPipelineResponse:
        return SmartInstructionPipelineResponse()

    def stream(self) -> AsyncGenerator[LlmStreamResponse, None]:
        pass
