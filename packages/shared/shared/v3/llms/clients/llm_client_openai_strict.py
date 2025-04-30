import json
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING

import openai
from shared.v3.interfaces.llm_message import LlmMessage, MessageKind
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
        self.async_client = openai.AsyncOpenAI()

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

    async def _generate_stream(
        self,
        message_history: LlmMessageHistory,
        response_type: type | None,
        tool_types: list[type[LlmTool]] | None,
    ) -> AsyncGenerator[str, None] | AsyncGenerator[LlmMessage, None]:
        """
        Stream tokens (and eventual tool-call / assistant message) from a strict-mode
        completion.  During the stream we yield raw string deltas; when the stream
        finishes we yield either a Tool-Call request or the final LlmMessage that
        should be appended to history.
        """
        # Build kwargs exactly as in _generate, but for streaming
        completion_kwargs = {
            "model": self.config.llm_model_id,
            "messages": message_history.to_openai_strict(),
        }

        if tool_types:
            processed_tools = [openai.pydantic_function_tool(t) for t in tool_types]
            completion_kwargs["tools"] = processed_tools
            completion_kwargs["tool_choice"] = "auto"

        if response_type:
            completion_kwargs["response_format"] = response_type

        stream = await self.async_client.chat.completions.create(
            **completion_kwargs,
            stream=True,
        )

        tool_calls: list[dict] = []
        final_content: str = ""

        async for chunk in stream:
            delta = chunk.choices[0].delta

            # Token deltas
            if delta.content:
                final_content += delta.content
                yield delta.content

            # Tool-call deltas
            if delta.tool_calls:
                call = delta.tool_calls[0]
                idx = call.index
                if idx >= len(tool_calls):
                    tool_calls.append(
                        {
                            "id": call.id,
                            "name": call.function.name,
                            "arguments": call.function.arguments,
                        }
                    )
                else:
                    tool_calls[idx]["arguments"] += call.function.arguments

        if tool_calls:
            # Build a ToolCallRequest then yield it
            yield LlmMessage(
                tool_requests=[
                    LlmMessage.ToolCallRequest(
                        id=tc["id"],
                        name=tc["name"],
                        arguments=tc["arguments"],
                        parsed_tool=next(
                            (
                                tool(**json.loads(tc["arguments"]))
                                for tool in (tool_types or [])
                                if tool.__name__ == tc["name"]
                            ),
                            None,
                        ),
                    )
                    for tc in tool_calls
                ],
                message_kind=MessageKind.TOOL_CALL_REQUEST,
                content=None,
            )
        else:
            assistant_msg = LlmMessage(
                message_kind=MessageKind.ASSISTANT,
                content=final_content,
                parsed_content=(
                    response_type(**json.loads(final_content))
                    if response_type
                    else None
                ),
            )
            yield assistant_msg
