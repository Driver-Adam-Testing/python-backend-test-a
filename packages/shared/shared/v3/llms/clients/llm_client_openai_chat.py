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


class OpenAiChatClient(LlmClient):
    """
    A client for OpenAI's Chat models.

    This client is designed to work with OpenAI's Chat models, which are designed to
    use system prompts to guide the model's behavior.
    They are capable of running tools natively using the tool_call chat response format in OpenAI.
    response_type is not supported, but can be cast to create parsed responses.
    """

    def __init__(self, config: LlmConfig) -> None:
        super().__init__(config)
        self.client = openai.OpenAI()

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

        if prompt:
            local_message_history.add_message(
                LlmMessage(message_kind=MessageKind.USER, content=prompt)
            )

        completion_kwargs = {
            "model": self.config.model_id,
            "messages": local_message_history.to_openai_strict(),
        }

        if tools:
            processed_tools = [openai.pydantic_function_tool(tool) for tool in tools]
            completion_kwargs["tools"] = processed_tools
            completion_kwargs["tool_choice"] = "auto"

        response: ChatCompletionMessage = (
            self.client.chat.completions.create(**completion_kwargs).choices[0].message
        )
        return LlmMessage.from_openai_chat_completion_message(
            response, response_type=response_type, tool_list=tools
        )
