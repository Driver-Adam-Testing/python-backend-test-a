from collections.abc import AsyncGenerator

from shared.v3 import LlmClient, LlmMessageHistory
from shared.v3.app.pipelines.pipeline_request import PipelineRequest
from shared.v3.app.pipelines.pipeline_response import PipelineResponse
from shared.v3.app.static.enums.format_kinds import FormatKind
from shared.v3.app.static.messages.copy_editor_messages import (
    CopyEditorSystemMessage,
)
from shared.v3.app.static.messages.format_kind_message import FormatKindMessage
from shared.v3.app.static.messages.software_expertise import SoftwareExpertiseMessage
from shared.v3.globals.global_messages import GlobalSystemMessage
from shared.v3.interfaces.llm_stream_response import (
    LlmStreamResponse,
)


class ReformatPipelineResponse(PipelineResponse):
    pass


class ReformatPipelineRequest(PipelineRequest):
    cursor_selection: str
    format_kind: FormatKind

    def _run(self, client: LlmClient = LlmClient.gpt_4_1()) -> ReformatPipelineResponse:
        response = client.single_shot(
            message_history=LlmMessageHistory(
                messages=[
                    GlobalSystemMessage.system_message(),
                    CopyEditorSystemMessage.system_message(),
                    SoftwareExpertiseMessage.system_message(),
                    FormatKindMessage.from_context(self.format_kind).to_message(),
                ]
            ),
            prompt=f"Reformat the following: {self.cursor_selection}",
        )

        return ReformatPipelineResponse(
            content=response.content,
            references=[],
        )

    async def _stream(
        self, client: LlmClient = LlmClient.o3_mini()
    ) -> AsyncGenerator[LlmStreamResponse, None]:
        async for chunk in client.single_shot_stream(
            message_history=LlmMessageHistory(
                messages=[
                    GlobalSystemMessage.system_message(),
                    CopyEditorSystemMessage.system_message(),
                    SoftwareExpertiseMessage.system_message(),
                    FormatKindMessage.from_context(self.format_kind).to_message(),
                ]
            ),
            prompt=f"Reformat the following: {self.cursor_selection}",
        ):
            yield chunk
