from shared.v3.llms.clients.llm_client import LlmClient
from shared.v3.llms.config.llm_config import LlmConfig
from shared.v3.messages.llm_message_history import LlmMessageHistory
from shared.v3.pipelines.interfaces.pipeline_request import (
    PipelineExecutionRequest,
)
from shared.v3.static.messages.driver_application_messages import (
    AbbreviateDocumentSystemMessage,
    AgenticContextMessage,
)
from shared.v3.utils.parseable import LlmParseable


class AbbreviatedDocumentText(LlmParseable):
    """
    A class that represents the abbreviated text from a document.
    When given a document part, this class will return a terse, information dense, version of the document part, so that it can be used by a system to respond to a user request.
    The user request is not included in the abbreviated text.

    Attributes:
        abbreviated_document_text (str): The trimmed text from the document.
    """

    abbreviated_document_text: str


def compress_before(
    pipeline_execution_request: PipelineExecutionRequest,
) -> AbbreviatedDocumentText | None:
    trim_client = LlmClient.from_config(LlmConfig.default())
    if (
        pipeline_execution_request.text_before_selection
        and pipeline_execution_request.text_before_selection.strip() != ""
    ):
        if pipeline_execution_request.selected_text:
            before_prompt = f"User Prompt:\n {pipeline_execution_request.original_prompt}\n\n Selected Text:\n {pipeline_execution_request.selected_text}\n\n Document Content Before Prompt:\n {pipeline_execution_request.text_before_selection}"
        else:
            before_prompt = f"User Prompt:\n {pipeline_execution_request.original_prompt}\n\n Document Content Before Prompt:\n {pipeline_execution_request.text_before_selection}"
        return trim_client.generate(
            prompt=before_prompt,
            response_type=AbbreviatedDocumentText,
            message_history=LlmMessageHistory(
                messages=[
                    AbbreviateDocumentSystemMessage(),
                    AgenticContextMessage(),
                ]
            ),
        ).parsed_content
    return None


def compress_after(
    pipeline_execution_request: PipelineExecutionRequest,
) -> AbbreviatedDocumentText | None:
    trim_client = LlmClient.from_config(LlmConfig.default())
    if (
        pipeline_execution_request.text_after_selection
        and pipeline_execution_request.text_after_selection.strip() != ""
    ):
        if pipeline_execution_request.selected_text:
            after_prompt = f"User Prompt:\n {pipeline_execution_request.original_prompt}\n\n Selected Text:\n {pipeline_execution_request.selected_text}\n\n Document Content After Prompt:\n {pipeline_execution_request.text_after_selection}"
        else:
            after_prompt = f"User Prompt:\n {pipeline_execution_request.original_prompt}\n\n Document Content After Prompt:\n {pipeline_execution_request.text_after_selection}"
        return trim_client.generate(
            prompt=after_prompt,
            response_type=AbbreviatedDocumentText,
            message_history=LlmMessageHistory(
                messages=[
                    AbbreviateDocumentSystemMessage(),
                    AgenticContextMessage(),
                ]
            ),
        ).parsed_content
    return None
