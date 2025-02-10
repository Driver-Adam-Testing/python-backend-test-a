from typing import TYPE_CHECKING

import openai
from shared.v3.agents.agent_tool import LlmTool
from shared.v3.llms.clients.llm_client import LlmClient
from shared.v3.llms.config.llm_config import LlmConfig
from shared.v3.messages.llm_message import LlmMessage, MessageKind
from shared.v3.messages.llm_message_history import LlmMessageHistory

if TYPE_CHECKING:
    from openai.types.chat import ParsedChatCompletionMessage


class OpenAiStrictWithSystemClient(LlmClient):
    def __init__(self, config: LlmConfig) -> None:
        super().__init__(config)
        self.client = openai.OpenAI()

    def generate(
        self,
        prompt: str | None = None,
        response_type: type | None = None,
        message_history: LlmMessageHistory | None = None,
        tools: list[LlmTool] | None = None,
    ) -> LlmMessage:
        if message_history is None:
            message_history = LlmMessageHistory(messages=[])

        if prompt:
            message_history.add_message(
                LlmMessage(message_kind=MessageKind.USER, content=prompt)
            )

        completion_kwargs = {
            "model": self.config.model_id,
            "messages": message_history.to_openai_messagelist_gpt(),
        }

        if tools:
            processed_tools = [openai.pydantic_function_tool(tool) for tool in tools]
            completion_kwargs["tools"] = processed_tools
            completion_kwargs["tool_choice"] = "auto"

        if response_type:
            completion_kwargs["response_format"] = response_type

        response: ParsedChatCompletionMessage = (
            self.client.beta.chat.completions.parse(**completion_kwargs)
            .choices[0]
            .message
        )
        return LlmMessage.from_parsed_chat_completion_message(response)
