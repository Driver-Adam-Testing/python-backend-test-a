from abc import ABC, abstractmethod

from shared.v3.interfaces.llm_message import LlmMessage
from shared.v3.interfaces.llm_message_history import LlmMessageHistory
from shared.v3.interfaces.llm_response_type import LlmResponseType
from shared.v3.interfaces.llm_tool import LlmTool
from shared.v3.llms.config.llm_config import ApiKind, LlmConfig


class LlmClient(ABC):
    def __init__(self, config: LlmConfig) -> None:
        """
        Initializes the LlmClient with the given configuration.

        :param config: The LlmConfig object containing configuration details.
        """
        self.config = config

    # TODO: Should tool messages be handled by the multishot client? It becomes difficult when completion kwargs for strict mode are present, but it's beyond the scope of the llmclient.
    @abstractmethod
    def generate(
        self,
        prompt: str | None = None,
        response_type: type[LlmResponseType] | None = None,
        tools: list[type[LlmTool]] | None = None,
        message_history: LlmMessageHistory | None = None,
    ) -> LlmMessage:
        """
        Abstract method to generate a response based on the given prompt, response type, tools, and message history using the configured LLM provider.

        :param prompt: The input prompt for the LLM.
        :param response_type: The type of response expected from the LLM.
        :param tools: A list of tools that the LLM can use.
        :param message_history: A history of messages to provide context for the LLM.
        :return: The generated response from the LLM.
        """
        raise NotImplementedError("This method needs to be implemented by subclasses.")

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
