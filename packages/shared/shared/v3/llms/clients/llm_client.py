from abc import ABC, abstractmethod

from shared.v3.agents.agent_tool import LlmTool
from shared.v3.agents.response_type import LlmResponseType
from shared.v3.llms.config.llm_config import ApiKind, LlmConfig
from shared.v3.messages.llm_message import LlmMessage
from shared.v3.messages.llm_message_history import LlmMessageHistory


class LlmClient(ABC):
    def __init__(self, config: LlmConfig) -> None:
        """
        Initializes the LlmClient with the given configuration.

        :param config: The LlmConfig object containing configuration details.
        """
        self.config = config

    @abstractmethod
    def generate(
        self,
        prompt: str | None = None,
        response_type: type[LlmResponseType] | None = None,
        tools: list[type[LlmTool]] | None = None,
        message_history: LlmMessageHistory | None = None,
    ) -> LlmMessage:
        """
        Abstract method to generate a response based on the given prompt and messages using the configured LLM provider.

        :param prompt: The input prompt for the LLM.
        :param messages: A list of LlmMessages to provide context or history for the LLM.
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
        if config.api_kind == ApiKind.OPENAI_STRICT:
            from shared.v3.llms.clients.llm_client_openai_strict import (
                OpenAiStrictWithSystemClient,
            )

            return OpenAiStrictWithSystemClient(config)
        elif config.api_kind == ApiKind.OPENAI_O1:
            from shared.v3.llms.clients.llm_client_openai_o1 import (
                OpenAiO1SeriesClient,
            )

            return OpenAiO1SeriesClient(config)
        elif config.api_kind == ApiKind.OPENAI_O3:
            from shared.v3.llms.clients.llm_client_openai_o3 import (
                OpenAiO3SeriesClient,
            )

            return OpenAiO3SeriesClient(config)
        elif config.api_kind == ApiKind.OPENAI_CHAT_WITH_TOOLS:
            from shared.v3.llms.clients.llm_client_openai_chat import (
                OpenAiChatClient,
            )

            return OpenAiChatClient(config)
        # Add additional conditions here for other providers and API kinds
        else:
            raise ValueError(
                f"No suitable LlmClient subclass found for provider {config.provider} and API kind {config.api_kind}."
            )
