import concurrent.futures

from pydantic import BaseModel
from shared.v3.llms.clients.llm_client import LlmClient
from shared.v3.llms.config.llm_config import LlmConfig
from shared.v3.messages.llm_message_history import LlmMessageHistory
from shared.v3.pipelines.interfaces.pipeline_request import (
    PipelineExecutionRequest,
)
from shared.v3.static.messages.pipeline_abbreviate_page_content_messages import (
    AbbreviatePageContentSystemMessage,
    AbbreviatePageContentUserMessage,
)
from shared.v3.utils.parseable import LlmParseable

TEXT_PADDING_WORD_SIZE = 50
PAGE_CONTENT_CHUNK_WORD_SIZE = 256


class AbbreviatedDocumentText(LlmParseable):
    """
    Attributes:
        abbreviated_document_text (str): The summarized text from the document.
    """

    abbreviated_document_text: str


class AbbreviatedPageContentPipelineResponse(LlmParseable):
    """
    Attributes:
        abbreviated_before (str): The summarized text from the document before the cursor.
        abbreviated_after (str): The summarized text from the document after the cursor.
    """

    abbreviated_before: str
    abbreviated_after: str


class SummarizedChunkResponse(BaseModel):
    content: str
    is_before: bool
    index: int


def abbreviate_page_content(
    pipeline_execution_request: PipelineExecutionRequest,
    client: LlmClient | None = None,
) -> AbbreviatedPageContentPipelineResponse:
    """
    Performance
    Test 1: (50 each)
    +------------------+-----------+--------------+------------+
    |    Client ID     | Best Time | Average Time | Worst Time |
    +------------------+-----------+--------------+------------+
    | gpt_4o_mini_chat |    1.25   |     7.58     |   91.92    |
    |      gpt_4o      |    1.19   |     4.33     |   11.34    |
    |   gpt_4o_mini    |    1.87   |     3.75     |    8.3     |
    |     o3_mini      |    4.58   |     8.26     |   19.41    |
    |     o1_mini      |    8.47   |    13.94     |    34.0    |
    |        o1        |   12.86   |    23.97     |    43.7    |
    +------------------+-----------+--------------+------------+

    Test 2: (10 each)
    +------------------+-----------+--------------+------------+
    |    Client ID     | Best Time | Average Time | Worst Time |
    +------------------+-----------+--------------+------------+
    | gpt_4o_mini_chat |    1.02   |     2.67     |    3.88    |
    |   gpt_4o_mini    |    1.67   |     3.68     |    5.94    |
    |      gpt_4o      |    1.88   |     4.78     |   10.96    |
    |     o3_mini      |    4.78   |     9.11     |   15.97    |
    |     o1_mini      |   10.49   |    14.35     |   20.82    |
    |        o1        |    13.5   |    20.99     |   29.87    |
    +------------------+-----------+--------------+------------+
    """
    client = client or LlmClient.from_config(LlmConfig.gpt_4o_mini())

    def summarize_chunk(
        chunk: str, is_before: bool, index: int
    ) -> SummarizedChunkResponse:
        return SummarizedChunkResponse(
            content=client.generate(
                response_type=AbbreviatedDocumentText,
                message_history=LlmMessageHistory(
                    messages=[
                        AbbreviatePageContentSystemMessage(),
                        AbbreviatePageContentUserMessage.from_context(
                            prompt=pipeline_execution_request.original_prompt,
                            page_content=chunk,
                            before=is_before,
                            selected_text=pipeline_execution_request.selected_text,
                        ),
                    ]
                ),
            ).parsed_content.abbreviated_document_text,
            is_before=is_before,
            index=index,
        )

    def create_chunks(content: str | None, is_before: bool) -> tuple[list[str], str]:
        if not content or not content.strip():
            return ([], "")
        words = content.split(" ")
        if len(words) < TEXT_PADDING_WORD_SIZE * 2:
            return ([], content)
        untouched_words = (
            words[-TEXT_PADDING_WORD_SIZE:]
            if is_before
            else words[:TEXT_PADDING_WORD_SIZE]
        )
        compress_words = (
            words[:-TEXT_PADDING_WORD_SIZE]
            if is_before
            else words[TEXT_PADDING_WORD_SIZE:]
        )

        number_of_chunks = int(len(compress_words) / PAGE_CONTENT_CHUNK_WORD_SIZE) + 1
        chunk_size = int(len(compress_words) / number_of_chunks) + 1

        chunks = []
        current_chunk = []
        for word in compress_words:
            current_chunk.append(word)
            if len(current_chunk) == chunk_size:
                chunks.append(" ".join(current_chunk))
                current_chunk = []

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return (chunks, " ".join(untouched_words))

    abbreviated_before = ""
    abbreviated_after = ""

    before_chunks, before_untouched_words = create_chunks(
        pipeline_execution_request.text_before_selection, True
    )
    after_chunks, after_untouched_words = create_chunks(
        pipeline_execution_request.text_after_selection, False
    )

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        if before_chunks:
            futures.extend(
                executor.submit(
                    summarize_chunk,
                    chunk,
                    True,
                    index,
                )
                for index, chunk in enumerate(before_chunks)
            )
        if after_chunks:
            futures.extend(
                executor.submit(
                    summarize_chunk,
                    chunk,
                    False,
                    index,
                )
                for index, chunk in enumerate(after_chunks)
            )

        results: list[SummarizedChunkResponse] = [
            future.result() for future in concurrent.futures.as_completed(futures)
        ]
        results.sort(key=lambda x: x.index)
        for result in results:
            if result.is_before:
                abbreviated_before += " " + result.content
            else:
                abbreviated_after += " " + result.content
    return AbbreviatedPageContentPipelineResponse(
        abbreviated_before=abbreviated_before + before_untouched_words,
        abbreviated_after=after_untouched_words + abbreviated_after,
    )
