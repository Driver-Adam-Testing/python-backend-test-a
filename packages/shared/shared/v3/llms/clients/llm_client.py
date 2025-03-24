from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator

from shared.v3.globals.iteration_messages import (
    IterationMessage,
    MultiShotIterationContextMessage,
)
from shared.v3.interfaces.llm_message import LlmMessage, MessageKind
from shared.v3.interfaces.llm_message_history import LlmMessageHistory
from shared.v3.interfaces.llm_response_type import LlmResponseType
from shared.v3.interfaces.llm_stream_response import (
    ErrorStreamResponse,
    LlmStreamResponse,
    LlmStreamResponseKind,
    ResponseChunkStreamResponse,
    ResponseFullStreamResponse,
    ToolStatusUpdateStreamResponse,
)
from shared.v3.interfaces.llm_tool import LlmTool
from shared.v3.llms.config.llm_config import ApiKind, LlmConfig
from shared.v3.utils.datasource import DataSource


class LlmClient(ABC):
    def __init__(self, config: LlmConfig) -> None:
        """
        Initializes the LlmClient with the given configuration.

        :param config: The LlmConfig object containing configuration details.
        """
        self.config = config

    @classmethod
    def from_config(cls, config: LlmConfig) -> "LlmClient":
        """
        Determines the best subclass of LlmClient to return based on the provided configuration.

        :param config: The LlmConfig object containing configuration details.
        :return: An instance of a subclass of LlmClient.
        """
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
                    f"No suitable LlmClient subclass found for provider {config.provider} and API kind {config.api_kind}."
                )

    @classmethod
    def gpt_4o(cls) -> "LlmClient":
        return cls.from_config(LlmConfig.gpt_4o())

    @classmethod
    def gpt_4o_chat(cls) -> "LlmClient":
        return cls.from_config(LlmConfig.gpt_4o_chat())

    @classmethod
    def gpt_4o_mini(cls) -> "LlmClient":
        return cls.from_config(LlmConfig.gpt_4o_mini())

    @classmethod
    def gpt_4o_mini_chat(cls) -> "LlmClient":
        return cls.from_config(LlmConfig.gpt_4o_mini_chat())

    @classmethod
    def o1(cls) -> "LlmClient":
        return cls.from_config(LlmConfig.o1())

    @classmethod
    def o1_mini(cls) -> "LlmClient":
        return cls.from_config(LlmConfig.o1_mini())

    @classmethod
    def o3_mini(cls) -> "LlmClient":
        return cls.from_config(LlmConfig.o3_mini())

    @classmethod
    def gpt_4_5(cls) -> "LlmClient":
        return cls.from_config(LlmConfig.gpt_4_5())

    @classmethod
    def claude_sonnet_3_5(cls) -> "LlmClient":
        return cls.from_config(LlmConfig.claude_sonnet_3_5())

    @classmethod
    def claude_sonnet_3_7(cls) -> "LlmClient":
        return cls.from_config(LlmConfig.claude_sonnet_3_7())

    @classmethod
    def claude_haiku_3_5(cls) -> "LlmClient":
        return cls.from_config(LlmConfig.claude_haiku_3_5())

    @abstractmethod
    def _generate(
        self,
        message_history: LlmMessageHistory,
        response_type: type[LlmResponseType] | None,
        tool_types: list[type[LlmTool]] | None,
    ) -> None:
        """
        This method is used to generate a response from the LLM.

        :param message_history: The message history to use for the generation.
        :param response_type: The response type to use for the generation.
        :param tool_types: The tool types to use for the generation.

        this method assumes that the message history contains no model-specific messages.
        Model-specific messages must be added in the implementation of _generate.
        The implementation of _generate must copy the message history when appending model-specific messages so that it is not mutated.
        """
        raise NotImplementedError("This method needs to be implemented by subclasses.")

    async def _generate_stream(
        self,
        message_history: LlmMessageHistory,
        response_type: type[LlmResponseType] | None,
        tool_types: list[type[LlmTool]] | None,
    ) -> AsyncGenerator[LlmMessage | str, None]:
        """
        This is the default implementation of _generate_stream.
        It yields the last message in the message history.

        This method is intended to be overridden by subclasses that need to yield additional messages.
        """
        self._generate(
            message_history=message_history,
            response_type=response_type,
            tool_types=tool_types,
        )
        yield message_history.last()

    def single_shot(
        self,
        prompt: str | None = None,
        response_type: type[LlmResponseType] | None = None,
        message_history: LlmMessageHistory | None = None,
    ) -> LlmMessage:
        """
        This method is used to generate a single response from the LLM.

        :param prompt: The prompt to use for the generation.
        :param response_type: The response type to use for the generation.
        :param message_history: The message history to use for the generation.
        :return: The generated response.
        """
        if message_history is None:
            message_history = LlmMessageHistory(messages=[])
        if prompt:
            message_history.add_message(
                LlmMessage(message_kind=MessageKind.USER, content=prompt)
            )
        self._generate(
            message_history=message_history,
            response_type=response_type,
            tool_types=None,
        )
        return message_history.last()

    def multi_shot(
        self,
        prompt: str | None = None,
        iterations: int = 2,
        response_type: type[LlmResponseType] | None = None,
        tool_types: list[type[LlmTool]] | None = None,
        message_history: LlmMessageHistory | None = None,
        datasource: DataSource | None = None,
    ) -> tuple[LlmMessage, list[LlmTool]]:
        """
        This method is used to generate a response from the LLM, allowing for tool calls and multiple iterations.

        :param prompt: The prompt to use for the generation.
        :param iterations: The number of iterations to use for the generation.
        :param response_type: The response type to use for the generation.
        :param tool_types: The tool types to use for the generation.
        :param message_history: The message history to use for the generation.
        :param datasource: The datasource to use for the generation.
        :return: A tuple containing the generated response, the list of called tools.

        The message history is mutated in place.
        This method appends iteration messages.
        """
        called_tools: list[LlmTool] = []
        if message_history is None:
            message_history = LlmMessageHistory()
        message_history.add_message(MultiShotIterationContextMessage())
        if prompt:
            message_history.add_message(
                LlmMessage(message_kind=MessageKind.USER, content=prompt)
            )

        for i in range(iterations):
            message_history.add_message(
                IterationMessage.from_context(i + 1, iterations)
            )
            self._generate(
                message_history=message_history,
                response_type=response_type,
                tool_types=tool_types,
            )
            if message_history.last().message_kind == MessageKind.TOOL_CALL_REQUEST:
                for tool_call in message_history.last().tool_requests:
                    called_tool: LlmTool = tool_call.parsed_tool
                    called_tools.append(called_tool)
                    message_history.add_message(
                        called_tool.execute(
                            tool_call_id=tool_call.id,
                            datasource=datasource,
                        )
                    )
            else:
                break
        return message_history.last(), called_tools

    # TODO: This is bringing up: do these generations return an LlmMessage, or do they append the message_history?
    # Since this is yielding LlmStreamResponse, but the final assistant message doesn't make sense to redundantly return as a full message
    # TODO: get references from the tool calls
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
        if message_history is None:
            message_history = LlmMessageHistory()
        message_history.add_message(MultiShotIterationContextMessage())
        if prompt:
            message_history.add_message(
                LlmMessage(message_kind=MessageKind.USER, content=prompt)
            )
        should_continue = True
        for iteration_index in range(iterations):
            if not should_continue:
                break

            # Add iteration context message
            iteration_message = IterationMessage.from_context(
                iteration_index + 1, iterations
            )
            message_history.add_message(iteration_message)

            # Stream the response for the current iteration
            response_stream = self._generate_stream(
                message_history=message_history,
                response_type=response_type,
                tool_types=tool_types,
            )

            async for chunk in response_stream:
                # If it's a tool call request, handle tool execution
                if (
                    isinstance(chunk, LlmMessage)
                    and chunk.message_kind == MessageKind.TOOL_CALL_REQUEST
                ):
                    message_history.add_message(chunk)
                    for tool_call in chunk.tool_requests:
                        called_tool: LlmTool = tool_call.parsed_tool
                        called_tools.append(called_tool)

                        # Yield status before execution
                        yield ToolStatusUpdateStreamResponse(
                            kind=LlmStreamResponseKind.TOOL_STATUS_UPDATE,
                            content=called_tool.status,
                        )

                        # Execute the tool
                        tool_response = called_tool.execute(
                            tool_call_id=tool_call.id,
                            datasource=datasource,
                        )

                        # Yield status after execution
                        yield ToolStatusUpdateStreamResponse(
                            kind=LlmStreamResponseKind.TOOL_STATUS_UPDATE,
                            content=called_tool.status,
                        )
                        message_history.add_message(tool_response)

                # If it's a string, treat it as a response chunk
                elif isinstance(chunk, str):
                    yield ResponseChunkStreamResponse(
                        kind=LlmStreamResponseKind.RESPONSE_CHUNK,
                        content=chunk,
                    )
                    should_continue = False

                # If the chunk is a completed LlmMessage
                elif isinstance(chunk, LlmMessage):
                    message_history.add_message(chunk)
                    yield ResponseFullStreamResponse(
                        kind=LlmStreamResponseKind.RESPONSE_FULL,
                        content=chunk.content,
                    )
                    should_continue = False

                # If the chunk is an unexpected type, raise an error
                else:
                    yield ErrorStreamResponse(
                        kind=LlmStreamResponseKind.ERROR,
                        error_message=f"Unexpected type: {type(chunk)}",
                    )
                    raise ValueError(f"Unexpected type: {type(chunk)}")
