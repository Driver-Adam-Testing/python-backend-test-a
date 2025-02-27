from typing import TYPE_CHECKING

import openai
from shared.v3.interfaces.llm_message import LlmMessage
from shared.v3.interfaces.llm_message_history import LlmMessageHistory
from shared.v3.interfaces.llm_response_type import LlmResponseType
from shared.v3.interfaces.llm_tool import LlmTool
from shared.v3.llms.clients.llm_client import LlmClient
from shared.v3.llms.config.llm_config import LlmConfig

if TYPE_CHECKING:
    from openai.types.chat import ChatCompletionMessage


class OpenAiO1SeriesClient(LlmClient):
    """
    OpenAiOSeriesClient is a specialized LLM client that interacts with OpenAI's O-Series models.

    Key Characteristics:
    - System prompts are not used; instead, they are cast to developer messages.
    - Enforces JSON strictness on the output to ensure valid JSON responses.
    - Tools are executed as optional single instances, allowing for flexible tool integration.
    """

    def __init__(self, config: LlmConfig) -> None:
        super().__init__(config)
        self.client = openai.OpenAI()

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
        """
        # Create a copy of the message history to avoid mutating the original
        openai_o1_message_history: LlmMessageHistory = message_history.copy()

        if response_type:
            openai_o1_message_history.add_message(
                response_type.to_parsing_description_message()
            )

        for tool in tool_types if tool_types else []:
            openai_o1_message_history.add_message(tool.to_parsing_description_message())

        completion_kwargs = {
            "model": self.config.model_id,
            "messages": message_history.to_openai_o1(),
        }

        response: ChatCompletionMessage = (
            self.client.chat.completions.create(**completion_kwargs).choices[0].message
        )
        result = LlmMessage.from_openai_chat_completion_message(
            response, response_type=response_type, tool_types=tool_types
        )
        openai_o1_message_history.add_message(result)
        return result
