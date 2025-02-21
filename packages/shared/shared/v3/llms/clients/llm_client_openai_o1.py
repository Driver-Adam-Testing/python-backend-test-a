from typing import TYPE_CHECKING

import openai
from shared.v3.interfaces.llm_message import LlmMessage, MessageKind
from shared.v3.interfaces.llm_message_history import LlmMessageHistory
from shared.v3.interfaces.llm_response_type import LlmResponseType
from shared.v3.interfaces.llm_tool import LlmTool
from shared.v3.llms.clients.llm_client import LlmClient
from shared.v3.llms.config.llm_config import LlmConfig

if TYPE_CHECKING:
    from openai.types.chat import ChatCompletionMessage


class OpenAiO1SeriesClient(LlmClient):
    """
    OpenAiOSeriesClient is a specialized LLM client that interacts with OpenAI's O-Series models.

    Key Characteristics:
    - System prompts are not used; instead, they are cast to developer messages.
    - Enforces JSON strictness on the output to ensure valid JSON responses.
    - Tools are executed as optional single instances, allowing for flexible tool integration.
    """

    def __init__(self, config: LlmConfig) -> None:
        super().__init__(config)
        self.client = openai.OpenAI()

    def generate(
        self,
        prompt: str | None = None,
        response_type: type[LlmResponseType] | None = None,
        message_history: LlmMessageHistory | None = None,
        tools: list[LlmTool] | None = None,
    ) -> LlmMessage:
        # Create a copy of the message history to avoid mutating the original
        local_message_history = LlmMessageHistory(
            messages=message_history.messages.copy() if message_history else []
        )

        if response_type:
            local_message_history.add_message(
                response_type.to_parsing_description_message()
            )

        for tool in tools if tools else []:
            local_message_history.add_message(tool.to_parsing_description_message())

        if prompt:
            local_message_history.add_message(
                LlmMessage(message_kind=MessageKind.USER, content=prompt)
            )

        completion_kwargs = {
            "model": self.config.model_id,
            "messages": local_message_history.to_openai_o1(),
        }

        response: ChatCompletionMessage = (
            self.client.chat.completions.create(**completion_kwargs).choices[0].message
        )
        return LlmMessage.from_openai_chat_completion_message(
            response, response_type=response_type, tool_list=tools
        )
