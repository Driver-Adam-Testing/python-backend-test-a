import logging

from shared.interfaces.agents.data_scope import DataScope
from shared.v3.interfaces.llm_message import (
    LlmMessage,
)
from shared.v3.interfaces.llm_message_history import LlmMessageHistory
from shared.v3.interfaces.llm_message_kind import MessageKind
from shared.v3.interfaces.llm_response_type import LlmResponseType
from shared.v3.interfaces.llm_tool import (
    LlmTool,
    LlmToolContext,
)
from shared.v3.llms.clients.llm_client import LlmClient
from shared.v3.llms.config.llm_config import LlmConfig
from shared.v3.static.messages.global_iteration_messages import (
    MESSAGE_MULTI_ITERATION_SYSTEM,
    get_iteration_message,
)
from shared.v3.utils.references import ReferenceHistory

logger = logging.getLogger(__name__)


class MultiShotLlmClient:
    def __init__(
        self,
        datascope: DataScope,
        config: LlmConfig,
        tools: list[type[LlmTool]] | None = None,
        response_type: type[LlmResponseType] | None = None,
        message_history: LlmMessageHistory | None = None,
        reference_history: ReferenceHistory | None = None,
    ) -> None:
        self.message_history = (
            message_history
            if message_history is not None
            else LlmMessageHistory(messages=[])
        )
        self.tools: list[type[LlmTool]] = tools if tools is not None else []
        self.client: LlmClient = LlmClient.from_config(config)
        self.datascope: DataScope = datascope
        self.response_type: type[LlmResponseType] = response_type
        self.config: LlmConfig = config
        self.called_tools: list[LlmTool] = []
        self.reference_history: ReferenceHistory = (
            reference_history
            if reference_history is not None
            else ReferenceHistory(references=[])
        )

    def invoke(
        self, prompt: str | None = None, iterations: int = 1, debug: bool = False
    ) -> LlmMessage:
        if prompt:
            self.message_history.add_message(
                LlmMessage(message_kind=MessageKind.USER, content=prompt)
            )
        if iterations > 1:
            self.message_history.add_message(MESSAGE_MULTI_ITERATION_SYSTEM)
        for i in range(iterations):
            self.message_history.add_message(get_iteration_message(i + 1, iterations))
            response = self.client.generate(
                prompt=prompt,
                message_history=self.message_history,
                tools=self.tools if i < iterations - 1 else None,
                response_type=self.response_type,
            )
            self.message_history.add_message(response)

            if response.tool_requests:
                for tool_call in response.tool_requests:
                    called_tool: LlmTool = tool_call.parsed_tool
                    self.called_tools.append(called_tool)
                    self.message_history.add_message(
                        called_tool.execute(
                            LlmToolContext(
                                datascope=self.datascope,
                                llm_config=self.config,
                                tool_call_id=tool_call.id,
                            )
                        )
                    )
            else:
                return response
        raise RuntimeError(
            "Error: The agent invocation did not complete successfully in the allotted iterations."
        )
