from typing import TYPE_CHECKING

import openai
from shared.v3.interfaces.llm_message import LlmMessage
from shared.v3.interfaces.llm_message_history import LlmMessageHistory
from shared.v3.interfaces.llm_tool import LlmTool
from shared.v3.llms.clients.llm_client import LlmClient
from shared.v3.llms.config.llm_config import LlmConfig

if TYPE_CHECKING:
    from openai.types.chat import (
        ParsedChatCompletionMessage,
    )


class OpenAiStrictWithSystemClient(LlmClient):
    def __init__(self, config: LlmConfig) -> None:
        super().__init__(config)
        self.client = openai.OpenAI()

    def _generate(
        self,
        message_history: LlmMessageHistory,
        response_type: type | None,
        tool_types: list[type[LlmTool]] | None,
    ) -> LlmMessage:
        completion_kwargs = {
            "model": self.config.llm_model_id,
            "messages": message_history.to_openai_strict(),
        }

        if tool_types:
            processed_tools = [
                openai.pydantic_function_tool(tool) for tool in tool_types
            ]
            completion_kwargs["tools"] = processed_tools
            completion_kwargs["tool_choice"] = "auto"

        if response_type:
            completion_kwargs["response_format"] = response_type

        response: ParsedChatCompletionMessage = (
            self.client.beta.chat.completions.parse(**completion_kwargs)
            .choices[0]
            .message
        )

        result = LlmMessage.from_openai_parsed_chat_completion_message(response)
        message_history.add_message(result)
        return result


def print_message_from_chat_completion_params(completion_kwargs: dict) -> None:
    sent_messages = completion_kwargs.get("messages", [])
    print(len(sent_messages))
    for i, message in enumerate(sent_messages):
        print("--------------------------------")
        print(f"Message {i}: {message['role']}")
        content = message.get("content", "")
        if content:
            print(f" content: {content[:100]}")
        else:
            pass

        tool_calls = message.get("tool_calls", "")
        if tool_calls:
            print(f" tool_calls: {tool_calls}")
        else:
            pass

        tool_call_id = message.get("tool_call_id", "")
        if tool_call_id:
            print(f" tool_call_id: {tool_call_id}")
        else:
            pass
