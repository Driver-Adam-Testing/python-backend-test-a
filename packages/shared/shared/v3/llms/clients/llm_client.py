from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, ClassVar

from shared.chunking.text_splitter import split_text
from shared.v3.globals.iteration_messages import (
    IterationMessage,
    MultiShotIterationContextMessage,
)
from shared.v3.interfaces.llm_message import LlmMessage, MessageKind
from shared.v3.interfaces.llm_message_history import LlmMessageHistory
from shared.v3.interfaces.llm_stream_response import (
    ErrorStreamResponse,
    LlmStreamResponse,
    LlmStreamResponseKind,
    ReferenceStreamResponse,
    ResponseChunkStreamResponse,
    ResponseFullStreamResponse,
    ToolStatusUpdateStreamResponse,
)
from shared.v3.llms.config.llm_config import ApiKind, LlmConfig

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Callable

    from shared.v3.interfaces.llm_response_type import LlmResponseType
    from shared.v3.interfaces.llm_tool import LlmTool
    from shared.v3.utils.datasource import DataSource


class LlmClient(ABC):
    _PRESETS: ClassVar[dict[str, Callable[[], LlmConfig]]] = {
        "gpt_4o": LlmConfig.gpt_4o,
        "gpt_4o_chat": LlmConfig.gpt_4o_chat,
        "gpt_4o_mini": LlmConfig.gpt_4o_mini,
        "gpt_4o_mini_chat": LlmConfig.gpt_4o_mini_chat,
        "o1": LlmConfig.o1,
        "o1_mini": LlmConfig.o1_mini,
        "o3_mini": LlmConfig.o3_mini,
        "claude_sonnet_3_5": LlmConfig.claude_sonnet_3_5,
        "claude_sonnet_3_7": LlmConfig.claude_sonnet_3_7,
        "claude_haiku_3_5": LlmConfig.claude_haiku_3_5,
        "gpt_4_1": LlmConfig.gpt_4_1,
        "gpt_4_1_mini": LlmConfig.gpt_4_1_mini,
        "o4_mini": LlmConfig.o4_mini,
    }

    def __init__(self, config: LlmConfig = LlmConfig.default()) -> None:
        self.config = config

    @classmethod
    def initialize_presets(cls) -> None:
        def _make(name: str, factory: Callable[[], LlmConfig]) -> LlmClient:
            def _preset(c: LlmClient) -> LlmClient:
                return c.from_config(factory())

            _preset.__name__ = name  # correct `inspect output
            return classmethod(_preset)

        for _name, _factory in cls._PRESETS.items():
            setattr(cls, _name, _make(_name, _factory))

    @classmethod
    def from_config(cls, config: LlmConfig) -> LlmClient:
        """Return the concrete client that matches *config*."""

        match config.api_kind:
            case ApiKind.OPENAI_STRICT:
                from shared.v3.llms.clients.llm_client_openai_strict import (
                    OpenAiStrictWithSystemClient,
                )

                return OpenAiStrictWithSystemClient(config)
            case ApiKind.OPENAI_O1:
                from shared.v3.llms.clients.llm_client_openai_o1 import (
                    OpenAiO1SeriesClient,
                )

                return OpenAiO1SeriesClient(config)
            case ApiKind.OPENAI_CHAT_WITH_TOOLS:
                from shared.v3.llms.clients.llm_client_openai_chat import (
                    OpenAiChatClient,
                )

                return OpenAiChatClient(config)
            case ApiKind.CLAUDE:
                from shared.v3.llms.clients.llm_client_claude import ClaudeClient

                return ClaudeClient(config)
            case _:
                raise ValueError(
                    f"Unsupported api_kind “{config.api_kind}” for provider “{config.provider}”."
                )

    @staticmethod
    def _init_history(
        message_history: LlmMessageHistory | None,
        prompt: str | None,
    ) -> LlmMessageHistory:
        history = message_history or LlmMessageHistory()
        if prompt:
            history.add_message(LlmMessage(MessageKind.USER, prompt))
        return history

    async def _execute_tools_async(
        self,
        tool_requests: list[LlmMessage],
        history: LlmMessageHistory,
        called_tools: list[LlmTool],
        datasource: DataSource | None,
    ) -> AsyncGenerator[LlmStreamResponse, None]:
        tasks = []
        for req in tool_requests:
            tool: LlmTool = req.parsed_tool
            called_tools.append(tool)
            yield ToolStatusUpdateStreamResponse(
                kind=LlmStreamResponseKind.TOOL_STATUS_UPDATE,
                content=tool.status,
            )
            tasks.append(
                asyncio.create_task(tool.aexecute(req.id, datasource=datasource))
            )

        for finished in asyncio.as_completed(tasks):
            try:
                tool_msg: LlmMessage = await finished
                tool_msg = self._truncate_message_content(tool_msg)
                history.add_message(tool_msg)
                tool = next(
                    (
                        t
                        for t in called_tools
                        if t.tool_call_id == tool_msg.tool_response.id
                    ),
                    None,
                )
                yield ToolStatusUpdateStreamResponse(
                    kind=LlmStreamResponseKind.TOOL_STATUS_UPDATE,
                    content=tool.status,
                )
            except Exception as exc:
                error_message = f"Error during tool execution: {exc!s}"
                history.add_message(
                    LlmMessage(
                        message_kind=MessageKind.TOOL_CALL_RESPONSE,
                        content=error_message,
                        tool_response=LlmMessage.ToolCallResponse(
                            id=tool_msg.tool_response.id if tool_msg.tool_response else None, name=tool.__class__.__name__
                        ),
                    )
                )
                yield ErrorStreamResponse(
                    kind=LlmStreamResponseKind.ERROR,
                    error_message=f"Tool failed: {exc!s}",
                )

    @abstractmethod
    def _generate(
        self,
        message_history: LlmMessageHistory,
        response_type: type[LlmResponseType] | None,
        tool_types: list[type[LlmTool]] | None,
    ) -> None:
        """Add the provider's response to *message_history* (synchronous)."""

    async def _generate_stream(
        self,
        message_history: LlmMessageHistory,
        response_type: type[LlmResponseType] | None,
        tool_types: list[type[LlmTool]] | None,
    ) -> AsyncGenerator[LlmMessage | str, None]:
        """Default streaming implementation calls the sync variant once."""

        self._generate(message_history, response_type, tool_types)
        yield message_history.last()

    def single_shot(
        self,
        prompt: str | None = None,
        response_type: type[LlmResponseType] | None = None,
        message_history: LlmMessageHistory | None = None,
    ) -> LlmMessage:
        history = self._init_history(message_history, prompt)
        self._generate(history, response_type, None)
        return history.last()

    async def single_shot_stream(
        self,
        prompt: str | None = None,
        response_type: type[LlmResponseType] | None = None,
        message_history: LlmMessageHistory | None = None,
    ) -> AsyncGenerator[LlmStreamResponse, None]:
        async for chunk in self._generate_stream(
            message_history=self._init_history(message_history, prompt),
            response_type=response_type,
            tool_types=None,
        ):
            if isinstance(chunk, LlmMessage):
                yield ResponseFullStreamResponse(
                    kind=LlmStreamResponseKind.RESPONSE_FULL,
                    content=chunk.content,
                )
            else:
                yield chunk

    def _truncate_message_content(self, message: LlmMessage) -> LlmMessage:
        if message.content:
            message.content = split_text(
                text=message.content,
                model=self.config.llm_model_id,
                chunk_size=int(self.config.max_output_tokens * 0.7),
                chunk_overlap=0,
            )[0].text
        return message

    def multi_shot(
        self,
        prompt: str | None = None,
        iterations: int = 2,
        response_type: type[LlmResponseType] | None = None,
        tool_types: list[type[LlmTool]] | None = None,
        message_history: LlmMessageHistory | None = None,
        datasource: DataSource | None = None,
    ) -> tuple[LlmMessage, list[LlmTool]]:
        called_tools: list[LlmTool] = []
        history = self._init_history(message_history, prompt)
        history.add_message(MultiShotIterationContextMessage())

        for index in range(iterations):
            history.add_message(IterationMessage.from_context(index + 1, iterations))
            self._generate(
                message_history=history,
                response_type=response_type,
                tool_types=tool_types if index < iterations - 1 else None,
            )

            last = history.last()
            if last.message_kind == MessageKind.TOOL_CALL_REQUEST:
                for call in last.tool_requests:
                    tool: LlmTool = call.parsed_tool
                    called_tools.append(tool)
                    history.add_message(tool.execute(call.id, datasource=datasource))
            else:
                break

        return history.last(), called_tools

    async def multi_shot_stream(
        self,
        prompt: str | None = None,
        iterations: int = 2,
        response_type: type[LlmResponseType] | None = None,
        tool_types: list[type[LlmTool]] | None = None,
        message_history: LlmMessageHistory | None = None,
        datasource: DataSource | None = None,
    ) -> AsyncGenerator[LlmStreamResponse, None]:
        called_tools: list[LlmTool] = []
        history = self._init_history(message_history, prompt)
        history.add_message(MultiShotIterationContextMessage())

        should_continue = True
        for index in range(iterations):
            if not should_continue:
                break

            history.add_message(IterationMessage.from_context(index + 1, iterations))

            # Stream provider response for *this* iteration
            async for chunk in self._generate_stream(
                message_history=history,
                response_type=response_type,
                tool_types=tool_types if index < iterations - 1 else None,
            ):
                if isinstance(chunk, str):
                    yield ResponseChunkStreamResponse(
                        kind=LlmStreamResponseKind.RESPONSE_CHUNK,
                        content=chunk,
                    )
                    continue

                if (
                    isinstance(chunk, LlmMessage)
                    and chunk.message_kind == MessageKind.TOOL_CALL_REQUEST
                ):
                    history.add_message(chunk)
                    async for status in self._execute_tools_async(
                        chunk.tool_requests,
                        history,
                        called_tools,
                        datasource,
                    ):
                        yield status
                    break

                if (
                    isinstance(chunk, LlmMessage)
                    and chunk.message_kind == MessageKind.ASSISTANT
                ):
                    history.add_message(chunk)
                    yield ReferenceStreamResponse(
                        kind=LlmStreamResponseKind.REFERENCES,
                        references=[
                            ref for tool in called_tools for ref in tool.references
                        ],
                    )
                    yield ResponseFullStreamResponse(
                        kind=LlmStreamResponseKind.RESPONSE_FULL,
                        content=chunk.content,
                    )
                    await asyncio.sleep(
                        0.05
                    )  # 50ms pause to avoid race condition on client read
                    should_continue = False
                    continue

                yield ErrorStreamResponse(
                    kind=LlmStreamResponseKind.ERROR,
                    error_message=f"Unexpected type: {type(chunk)}",
                )
                raise ValueError(f"Unexpected type: {type(chunk)}")


LlmClient.initialize_presets()
__all__ = [
    "LlmClient",
]
