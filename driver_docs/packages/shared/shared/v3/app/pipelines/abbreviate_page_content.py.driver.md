# Purpose
This Python code defines a function, `abbreviate_page_content`, which is designed to summarize text content from a document, specifically focusing on the content before and after a cursor position. The code is structured to handle text in chunks, allowing for efficient processing and summarization using a language model client, `LlmClient`. The function takes in parameters such as a user prompt, text content before and after the cursor, and optionally a client instance. It utilizes concurrent processing to handle multiple chunks of text simultaneously, improving performance when dealing with large documents. The summarized content is returned as an instance of `AbbreviatedPageContentPipelineResponse`, which includes the summarized text before and after the cursor.

The code leverages several classes and interfaces, such as `LlmParseable` and `BaseModel`, to define data structures for handling the summarized content. It also uses a thread pool executor from the `concurrent.futures` module to parallelize the summarization process. The function is part of a broader system that likely involves natural language processing and document management, as indicated by the use of language model clients and message history interfaces. This code is intended to be part of a larger application or library, providing a specific functionality for text summarization within a document processing pipeline.
# Imports and Dependencies

---
- `concurrent.futures`
- `pydantic.BaseModel`
- `shared.v3.app.static.messages.abbreviate_page_content_messages.AbbreviatePageContentSystemMessage`
- `shared.v3.app.static.messages.abbreviate_page_content_messages.AbbreviatePageContentUserMessage`
- `shared.v3.interfaces.llm_message_history.LlmMessageHistory`
- `shared.v3.interfaces.llm_parseable.LlmParseable`
- `shared.v3.llms.clients.llm_client.LlmClient`
- `shared.v3.llms.config.llm_config.LlmConfig`


# Global Variables

---
### PAGE_CONTENT_CHUNK_WORD_SIZE 
- **Type**: `int`
- **Description**: `PAGE_CONTENT_CHUNK_WORD_SIZE` is an integer constant set to 256. It represents the number of words that each chunk of page content should contain when the content is being divided into smaller parts for processing.
- **Use**: This variable is used to determine the size of each chunk of text when splitting page content into smaller segments for summarization.


---
### TEXT_PADDING_WORD_SIZE 
- **Type**: `int`
- **Description**: `TEXT_PADDING_WORD_SIZE` is an integer constant set to 50. It represents the number of words that are preserved as 'untouched' when creating chunks of text for processing.
- **Use**: This variable is used to determine the number of words to keep unaltered at the beginning or end of a text segment when splitting content into chunks for summarization.


# Classes

---
### AbbreviatedDocumentText 
- **Type**: `class`
- **Members**:
    - `abbreviated_document_text`: The summarized text from the document.
- **Description**: The `AbbreviatedDocumentText` class is a simple data structure that inherits from `LlmParseable` and is used to represent a summarized version of a document's text. It contains a single attribute, `abbreviated_document_text`, which holds the summarized text as a string. This class is likely used in the context of processing or handling text data that has been condensed or summarized, possibly by a language model or similar system.
- **Inherits From**:
    - LlmParseable


---
### AbbreviatedPageContentPipelineResponse 
- **Type**: `class`
- **Members**:
    - `abbreviated_before`: The summarized text from the document before the cursor.
    - `abbreviated_after`: The summarized text from the document after the cursor.
- **Description**: The `AbbreviatedPageContentPipelineResponse` class is designed to encapsulate the results of a text summarization process, specifically for text segments located before and after a cursor within a document. It inherits from `LlmParseable`, indicating that it is intended to be used in contexts where parsing with a language model is relevant. The class contains two attributes, `abbreviated_before` and `abbreviated_after`, which store the summarized text from the respective sections of the document.
- **Inherits From**:
    - LlmParseable


---
### SummarizedChunkResponse 
- **Type**: `class`
- **Members**:
    - `content`: A string representing the summarized content of a chunk.
    - `is_before`: A boolean indicating if the chunk is from before the cursor.
    - `index`: An integer representing the position of the chunk in the sequence.
- **Description**: The `SummarizedChunkResponse` class is a data model that represents a summarized chunk of text, including its content, its position relative to a cursor (before or after), and its index in the sequence of chunks. It is used to encapsulate the result of summarizing a portion of text, providing a structured way to handle and sort these chunks when processing document content.
- **Inherits From**:
    - BaseModel


# Functions

---
### abbreviate_page_content 
The function `abbreviate_page_content` summarizes text content before and after a cursor position using a language model client.
- **Inputs**:
    - `user_prompt`: A string representing the user's prompt to guide the summarization process.
    - `page_content_before_cursor`: A string containing the text content before the cursor position, defaulting to an empty string.
    - `page_content_after_cursor`: A string containing the text content after the cursor position, defaulting to an empty string.
    - `selected_text`: A string representing the selected text, defaulting to a newline character.
    - `client`: An optional LlmClient instance used for summarization; if not provided, a default client is created from configuration.
- **Control Flow**:
    - Initialize the `client` using the provided client or a default configuration if none is provided.
    - Define a nested function `summarize_chunk` to summarize a text chunk using the client and return a `SummarizedChunkResponse`.
    - Define a nested function `create_chunks` to split the content into chunks and return a tuple of chunks and untouched words.
    - Initialize empty strings `abbreviated_before` and `abbreviated_after` to store the summarized content.
    - Create chunks for `page_content_before_cursor` and `page_content_after_cursor` using `create_chunks`.
    - Use a `ThreadPoolExecutor` to concurrently summarize each chunk using `summarize_chunk`.
    - Collect and sort the results of the summarization by their index.
    - Concatenate the summarized content into `abbreviated_before` and `abbreviated_after` based on their position relative to the cursor.
    - Return an `AbbreviatedPageContentPipelineResponse` containing the summarized content before and after the cursor.
- **Output**:
    - An `AbbreviatedPageContentPipelineResponse` object containing the summarized text before and after the cursor.


---
### create_chunks 
The `create_chunks` function splits a given text into chunks and identifies untouched words based on a specified position relative to a cursor.
- **Inputs**:
    - `content`: A string representing the text to be chunked, or None if no content is provided.
    - `is_before`: A boolean indicating whether the text is before the cursor (True) or after the cursor (False).
- **Control Flow**:
    - Check if the content is None or empty after stripping whitespace; if so, return an empty list and string.
    - Split the content into words and check if the number of words is less than twice the TEXT_PADDING_WORD_SIZE; if so, return an empty list and the original content.
    - Determine the untouched words based on the `is_before` flag: the last TEXT_PADDING_WORD_SIZE words if `is_before` is True, otherwise the first TEXT_PADDING_WORD_SIZE words.
    - Determine the compressible words by excluding the untouched words based on the `is_before` flag.
    - Calculate the number of chunks and the size of each chunk based on the length of compressible words and PAGE_CONTENT_CHUNK_WORD_SIZE.
    - Iterate over the compressible words, appending them to the current chunk until the chunk size is reached, then add the chunk to the list of chunks.
    - If there are remaining words in the current chunk after the loop, add them as a final chunk.
    - Return the list of chunks and the untouched words joined into a string.
- **Output**:
    - A tuple containing a list of string chunks and a string of untouched words.


---
### summarize_chunk 
The `summarize_chunk` function generates a summarized version of a text chunk using a language model client and returns it along with metadata about its position relative to a cursor.
- **Inputs**:
    - `chunk`: A string representing a portion of text to be summarized.
    - `is_before`: A boolean indicating whether the chunk is from before the cursor position (True) or after (False).
    - `index`: An integer representing the position of the chunk in the sequence of chunks.
- **Control Flow**:
    - The function constructs a `LlmMessageHistory` object with system and user messages, where the user message is created using the `AbbreviatePageContentUserMessage.from_context` method with the provided `chunk`, `is_before`, and `selected_text`.
    - It calls the `client.single_shot` method with the `AbbreviatedDocumentText` response type and the constructed message history to obtain a summarized version of the chunk.
    - The summarized content is extracted from the `parsed_content.abbreviated_document_text` attribute of the response.
    - A `SummarizedChunkResponse` object is created and returned, containing the summarized content, the `is_before` flag, and the `index`.
- **Output**:
    - A `SummarizedChunkResponse` object containing the summarized text, a boolean indicating if it was before the cursor, and the index of the chunk.


