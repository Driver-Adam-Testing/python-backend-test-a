import json
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Any

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
        self.async_client = openai.AsyncOpenAI()

    def _make_kwargs(
        self,
        message_history: LlmMessageHistory,
        response_type: type[LlmResponseType] | None,
        tool_types: list[type[LlmTool]] | None,
    ) -> dict[str, Any]:
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

        return completion_kwargs

    def _generate(
        self,
        message_history: LlmMessageHistory,
        response_type: type[LlmResponseType] | None,
        tool_types: list[type[LlmTool]] | None,
    ) -> LlmMessage:
        openai_message_history: LlmMessageHistory = message_history.copy()
        completion_kwargs = self._make_kwargs(
            openai_message_history, response_type, tool_types
        )
        response: ChatCompletionMessage = (
            self.client.chat.completions.create(**completion_kwargs).choices[0].message
        )

        result = LlmMessage.from_openai_chat_completion_message(
            response, response_type=response_type, tool_types=tool_types
        )
        message_history.add_message(result)
        return result

    async def _generate_stream(
        self,
        message_history: LlmMessageHistory,
        response_type: type[LlmResponseType] | None,
        tool_types: list[type[LlmTool]] | None,
    ) -> AsyncGenerator[str, None] | AsyncGenerator[LlmMessage, None]:
        openai_message_history: LlmMessageHistory = message_history.copy()
        completion_kwargs = self._make_kwargs(
            openai_message_history, response_type, tool_types
        )
        stream = await self.async_client.chat.completions.create(
            **completion_kwargs,
            stream=True,
        )

        tool_calls: list[dict] = []
        final_content = ""
        async for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                final_content += delta.content
                yield delta.content
            if delta.tool_calls:
                if delta.tool_calls[0].id:
                    tool_calls.append(
                        {
                            "id": delta.tool_calls[0].id,
                            "name": delta.tool_calls[0].function.name,
                            "arguments": delta.tool_calls[0].function.arguments,
                        }
                    )
                tool_calls[delta.tool_calls[0].index]["arguments"] += delta.tool_calls[
                    0
                ].function.arguments

        if tool_calls:
            yield LlmMessage(
                tool_requests=[
                    LlmMessage.ToolCallRequest(
                        id=tool_call["id"],
                        name=tool_call["name"],
                        arguments=tool_call["arguments"],
                        parsed_tool=next(
                            (
                                tool(**json.loads(tool_call["arguments"]))
                                for tool in tool_types
                                if tool.__name__ == tool_call["name"]
                            ),
                            None,
                        ),
                    )
                    for tool_call in tool_calls
                ],
                message_kind=MessageKind.TOOL_CALL_REQUEST,
                content=None,
            )
        else:
            final_response = LlmMessage(
                message_kind=MessageKind.ASSISTANT,
                content=final_content,
                parsed_content=response_type(**json.loads(final_content))
                if response_type
                else None,
            )
            yield final_response
