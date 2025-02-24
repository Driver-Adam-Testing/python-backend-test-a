from typing import TYPE_CHECKING

import anthropic
from shared.v3.interfaces.llm_message import LlmMessage, MessageKind
from shared.v3.interfaces.llm_message_history import LlmMessageHistory
from shared.v3.interfaces.llm_response_type import LlmResponseType
from shared.v3.interfaces.llm_tool import LlmTool
from shared.v3.llms.clients.llm_client import LlmClient
from shared.v3.llms.config.llm_config import LlmConfig

if TYPE_CHECKING:
    from anthropic.types import Message


class ClaudeClient(LlmClient):
    """
    A client for Anthropic's Claude models.

    This client is designed to work with Anthropic's Claude models, which support
    system prompts and a messages-based API format. The messages are converted from
    the shared LlmMessage format to Anthropic's expected format.
    """

    def __init__(self, config: LlmConfig) -> None:
        super().__init__(config)
        self.client = anthropic.Anthropic()

    def generate(
        self,
        prompt: str | None = None,
        response_type: LlmResponseType | None = None,
        message_history: LlmMessageHistory | None = None,
        tools: list[LlmTool] | None = None,
    ) -> LlmMessage:
        local_message_history = LlmMessageHistory(
            messages=message_history.messages.copy() if message_history else []
        )

        if response_type:
            local_message_history.add_message(
                response_type.to_parsing_description_message()
            )
        if tools:
            for tool in tools:
                local_message_history.add_message(tool.to_parsing_description_message())

        if prompt:
            local_message_history.add_message(
                LlmMessage(message_kind=MessageKind.USER, content=prompt)
            )

        messages, system_message = local_message_history.to_anthropic()

        completion_kwargs = {
            "model": self.config.model_id,
            "max_tokens": self.config.max_output_tokens,
        }

        if system_message:
            completion_kwargs["system"] = system_message

        completion_kwargs["messages"] = messages

        response: Message = self.client.messages.create(**completion_kwargs)
        return LlmMessage.from_anthropic_message(
            response, response_type=response_type, tool_list=tools
        )
