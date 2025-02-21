import logging

from shared.interfaces.agents.data_scope import DataScope
from shared.v3.globals.iteration_messages import (
    IterationMessage,
    MultiShotSystemMessage,
)
from shared.v3.interfaces.llm_message import (
    LlmMessage,
)
from shared.v3.interfaces.llm_message_history import LlmMessageHistory
from shared.v3.interfaces.llm_message_kind import MessageKind
from shared.v3.interfaces.llm_response_type import LlmResponseType
from shared.v3.interfaces.llm_tool import (
    LlmTool,
)
from shared.v3.llms.clients.llm_client import LlmClient
from shared.v3.llms.config.llm_config import LlmConfig
from shared.v3.utils.references import ReferenceSet

logger = logging.getLogger(__name__)


class MultiShotLlmClient:
    def __init__(
        self,
        datascope: DataScope,
        config: LlmConfig,
        tools: list[type[LlmTool]] | None = None,
        message_history: LlmMessageHistory | None = None,
        references: ReferenceSet | None = None,
    ) -> None:
        self.message_history = (
            message_history
            if message_history is not None
            else LlmMessageHistory(messages=[])
        )
        self.tools: list[type[LlmTool]] = tools if tools is not None else []
        self.client: LlmClient = LlmClient.from_config(config)
        self.datascope: DataScope = datascope
        self.config: LlmConfig = config
        self.called_tools: list[LlmTool] = []
        self._references: ReferenceSet = (
            references if references is not None else ReferenceSet(references=[])
        )

    @property
    def references(self) -> ReferenceSet:
        self._references + [called_tool.references for called_tool in self.called_tools]
        return self._references

    def invoke(
        self,
        prompt: str | None = None,
        iterations: int = 1,
        response_type: type[LlmResponseType] | None = None,
        debug: bool = False,
    ) -> LlmMessage:
        # prompting twice here
        if prompt:
            self.message_history.add_message(
                LlmMessage(message_kind=MessageKind.USER, content=prompt)
            )
        if iterations > 1:
            self.message_history.add_message(MultiShotSystemMessage())
        for i in range(iterations):
            self.message_history.add_message(
                IterationMessage.from_context(i + 1, iterations)
            )
            response = self.client.generate(
                prompt=prompt,
                message_history=self.message_history,
                tools=self.tools if i < iterations - 1 else None,
                response_type=response_type,
            )
            self.message_history.add_message(response)

            if response.tool_requests:
                for tool_call in response.tool_requests:
                    called_tool: LlmTool = tool_call.parsed_tool
                    self.called_tools.append(called_tool)
                    self.message_history.add_message(
                        called_tool.execute(
                            tool_call_id=tool_call.id,
                            datascope=self.datascope,
                        )
                    )
            else:
                return response
        raise RuntimeError(
            "Error: The agent invocation did not complete successfully in the allotted iterations."
        )
