from abc import ABC, abstractmethod

from shared.v3.llms.clients.llm_generation_response import LlmGenerationResponse
from shared.v3.llms.config.llm_config import LlmConfig
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
        response_type: type | None = None,
        tools: list[type] | None = None,
        message_history: LlmMessageHistory | None = None,
    ) -> LlmGenerationResponse:
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
        if config.provider == "openai" and config.api_kind == "strict":
            from shared.v3.llms.clients.llm_client_openai_strict import (
                OpenAiStrictWithSystemClient,
            )

            return OpenAiStrictWithSystemClient(config)
        # Add additional conditions here for other providers and API kinds
        else:
            raise ValueError(
                f"No suitable LlmClient subclass found for provider {config.provider} and API kind {config.api_kind}."
            )
