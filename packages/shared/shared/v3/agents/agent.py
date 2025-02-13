import logging

from shared.interfaces.agents.data_scope import DataScope
from shared.v3.agents.agent_tool import (
    LlmTool,
    LlmToolContext,
    LlmToolResponse,
)
from shared.v3.agents.response_type import LlmResponseType
from shared.v3.llms.clients.llm_client import LlmClient
from shared.v3.llms.config.llm_config import LlmConfig
from shared.v3.messages.llm_message import (
    LlmMessage,
)
from shared.v3.messages.llm_message_history import LlmMessageHistory
from shared.v3.messages.llm_message_kind import MessageKind
from shared.v3.static.messages.global_iteration_messages import (
    MESSAGE_MULTI_ITERATION_SYSTEM,
    get_iteration_message,
)

logger = logging.getLogger(__name__)


class BaseAgent:
    def __init__(
        self,
        datascope: DataScope,
        config: LlmConfig,
        tools: list[type[LlmTool]] | None = None,
        response_type: type[LlmResponseType] | None = None,
        message_history: LlmMessageHistory | None = None,
    ) -> None:
        self.message_history = (
            message_history
            if message_history is not None
            else LlmMessageHistory(messages=[])
        )
        self.tools = tools if tools is not None else []
        self.client = LlmClient.from_config(config)
        self.datascope = datascope
        self.references = []
        self.response_type = response_type
        self.config = config

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
            if debug:
                logger.debug("Client response: %s", response)
            self.message_history.add_message(response)

            if response.tool_requests:
                for tool_call in response.tool_requests:
                    tool_response: LlmToolResponse = tool_call.parsed_tool.execute(
                        LlmToolContext(
                            datascope=self.datascope,
                            llm_config=self.config,
                            tool_call_id=tool_call.id,
                        )
                    )
                    self.message_history.add_message(tool_response.to_message())
                    self.references.extend(tool_response.to_references())
            else:
                return response
        raise RuntimeError(
            "Error: The agent invocation did not complete successfully in the allotted iterations."
        )
