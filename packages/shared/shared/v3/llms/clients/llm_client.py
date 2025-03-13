from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator

from shared.v3.globals.iteration_messages import (
    IterationMessage,
    MultiShotSystemMessage,
)
from shared.v3.interfaces.llm_message import LlmMessage, MessageKind
from shared.v3.interfaces.llm_message_history import LlmMessageHistory
from shared.v3.interfaces.llm_response_type import LlmResponseType
from shared.v3.interfaces.llm_stream_response import (
    LlmStreamResponse,
    LlmStreamResponseKind,
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
            case ApiKind.OPENAI_O3:
                # TODO: this might be the same as CHAT WITH TOOLS
                from shared.v3.llms.clients.llm_client_openai_o3 import (
                    OpenAiO3SeriesClient,
                )

                return OpenAiO3SeriesClient(config)
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
    def claude_3_sonnet(cls) -> "LlmClient":
        return cls.from_config(LlmConfig.claude_3_sonnet())

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
    ) -> LlmMessage:
        """
        This method is used to generate a response from the LLM.

        :param message_history: The message history to use for the generation.
        :param response_type: The response type to use for the generation.
        :param tool_types: The tool types to use for the generation.
        :return: The generated response.

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
    ) -> AsyncGenerator[LlmMessage, None]:
        yield self._generate(
            message_history=message_history,
            response_type=response_type,
            tool_types=tool_types,
        )

    def single_shot(
        self,
        prompt: str | None = None,
        response_type: type[LlmResponseType] | None = None,
        message_history: LlmMessageHistory | None = None,
    ) -> LlmMessage:
        if message_history is None:
            message_history = LlmMessageHistory(messages=[])
        if prompt:
            message_history.add_message(
                LlmMessage(message_kind=MessageKind.USER, content=prompt)
            )
        return self._generate(
            message_history=message_history,
            response_type=response_type,
            tool_types=None,
        )

    def multi_shot(
        self,
        prompt: str | None = None,
        iterations: int = 2,
        response_type: type[LlmResponseType] | None = None,
        tool_types: list[type[LlmTool]] | None = None,
        message_history: LlmMessageHistory | None = None,
        datasource: DataSource | None = None,
    ) -> tuple[LlmMessage, list[LlmTool], LlmMessageHistory]:
        called_tools: list[LlmTool] = []
        if message_history is None:
            message_history = LlmMessageHistory()
        message_history.add_message(MultiShotSystemMessage())
        if prompt:
            message_history.add_message(
                LlmMessage(message_kind=MessageKind.USER, content=prompt)
            )

        for i in range(iterations):
            message_history.add_message(
                IterationMessage.from_context(i + 1, iterations)
            )
            response_i = self._generate(
                message_history=message_history,
                response_type=response_type,
                tool_types=tool_types,
            )
            if response_i.tool_requests:
                for tool_call in response_i.tool_requests:
                    called_tool: LlmTool = tool_call.parsed_tool
                    called_tools.append(called_tool)
                    message_history.add_message(
                        called_tool.execute(
                            tool_call_id=tool_call.id,
                            datasource=datasource,
                        )
                    )
            else:
                return response_i, called_tools, message_history
        raise RuntimeError(
            "Error: The agent invocation did not complete successfully in the allotted iterations."
        )

    # TODO: This is bringing up: do these generations return an LlmMessage, or do they append the message_history?
    # Since this is yielding LlmStreamResponse, but the final assistant message doesn't make sense to redundantly return as a full message
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
        message_history.add_message(MultiShotSystemMessage())
        if prompt:
            message_history.add_message(
                LlmMessage(message_kind=MessageKind.USER, content=prompt)
            )
        halt_iterator = False
        for i in range(iterations):
            if halt_iterator:
                break
            message_history.add_message(
                IterationMessage.from_context(i + 1, iterations)
            )
            response_i = self._generate_stream(
                message_history=message_history,
                response_type=response_type,
                tool_types=tool_types,
            )
            async for chunk in response_i:
                if (
                    isinstance(chunk, LlmMessage)
                    and chunk.message_kind == MessageKind.TOOL_CALL_REQUEST
                ):
                    message_history.add_message(chunk)
                    for tool_call in chunk.tool_requests:
                        called_tool: LlmTool = tool_call.parsed_tool
                        called_tools.append(called_tool)
                        yield called_tool.to_status_stream_response()
                        tool_response = called_tool.execute(
                            tool_call_id=tool_call.id,
                            datasource=datasource,
                        )
                        yield called_tool.to_status_stream_response()
                        message_history.add_message(tool_response)
                elif isinstance(chunk, str):
                    yield LlmStreamResponse(
                        kind=LlmStreamResponseKind.RESPONSE_CHUNK,
                        content=chunk,
                    )
                    halt_iterator = True
                elif isinstance(chunk, LlmMessage):
                    message_history.add_message(chunk)
                    yield LlmStreamResponse(
                        kind=LlmStreamResponseKind.RESPONSE_FULL,
                        full_message=chunk,
                        content=chunk.content,
                    )
                    halt_iterator = True
                else:
                    raise ValueError(f"Unexpected type: {type(chunk)}")
