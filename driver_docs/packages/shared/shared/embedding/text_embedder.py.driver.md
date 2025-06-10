# Purpose
This Python code file is designed to provide functionality for embedding text using OpenAI's text embedding models. It includes both synchronous and asynchronous functions to handle text embedding tasks, making it versatile for different application needs. The primary functions, `batch_embed_text` and `async_batch_embed_text`, take a list of text chunks, which can be either strings or instances of the `TextChunk` class, and return a list of embeddings. The code ensures that only supported models are used by checking against a predefined list of supported models. It also handles potential API errors by implementing a retry mechanism with exponential backoff for the asynchronous function, ensuring robustness in the face of network or server issues.

The file imports necessary modules and classes, including OpenAI's API client classes and custom utilities for text chunking and retry logic. The use of environment variables allows for configuration flexibility, such as specifying the text embedding model. The code is structured to be part of a larger application, likely serving as a utility module that can be imported and used wherever text embedding is required. The presence of both synchronous and asynchronous implementations suggests that the code is designed to be adaptable to different performance and concurrency requirements, making it suitable for integration into various systems that require text processing capabilities.
# Imports and Dependencies

---
- `os`
- `itertools.batched`
- `openai.APIConnectionError`
- `openai.APITimeoutError`
- `openai.AsyncOpenAI`
- `openai.InternalServerError`
- `openai.OpenAI`
- `openai.RateLimitError`
- `shared.chunking.text_splitter.TextChunk`
- `shared.utils.decorators.async_retry_with_exponential_backoff`


# Global Variables

---
### BATCH_SIZE 
- **Type**: `int`
- **Description**: BATCH_SIZE is an integer variable set to 500, which represents the maximum number of text chunks that can be processed in a single batch when embedding text using OpenAI's API. This value is chosen to ensure that the total number of tokens processed in a batch does not exceed OpenAI's limit of 300,000 tokens, given that each chunk can have up to 512 tokens.
- **Use**: BATCH_SIZE is used to determine the size of each batch of text chunks when calling the OpenAI API for text embedding.


---
### SUPPORTED_OPENAI_MODELS 
- **Type**: `list`
- **Description**: `SUPPORTED_OPENAI_MODELS` is a list containing the names of OpenAI models that are supported by the application. Currently, it includes only one model, 'text-embedding-3-small', which is used for text embedding tasks.
- **Use**: This variable is used to validate if a specified model is supported before attempting to create embeddings with it.


---
### TEXT_EMBEDDING_MODEL 
- **Type**: `str`
- **Description**: `TEXT_EMBEDDING_MODEL` is a string variable that holds the name of the default text embedding model to be used, which is retrieved from the environment variable `TEXT_EMBEDDING_MODEL`. If the environment variable is not set, it defaults to 'text-embedding-3-small'.
- **Use**: This variable is used as the default model parameter in functions that perform text embedding operations.


# Functions

---
### _prepare_text_chunks 
The function `_prepare_text_chunks` processes a list of text chunks, ensuring they are either all strings or all `TextChunk` objects, and returns a list of strings.
- **Inputs**:
    - `text_chunks`: A list containing elements that are either strings or `TextChunk` objects.
- **Control Flow**:
    - Check if all elements in `text_chunks` are instances of `TextChunk`.
    - If true, return a list of the `text` attribute from each `TextChunk`.
    - If not all elements are strings, raise a `TypeError` indicating the list must be homogeneous.
    - If all elements are strings, return the list as is.
- **Output**:
    - A list of strings derived from the input `text_chunks`, either directly or by extracting the `text` attribute from `TextChunk` objects.


---
### async_batch_embed_text 
The `async_batch_embed_text` function asynchronously processes text chunks to generate embeddings using a specified OpenAI model.
- **Inputs**:
    - `text_chunks`: A list of text chunks, which can be either strings or instances of the TextChunk class, to be embedded.
    - `model`: An optional string specifying the OpenAI model to use for embedding, defaulting to the environment variable TEXT_EMBEDDING_MODEL.
- **Control Flow**:
    - Check if the provided model is supported; if not, raise a ValueError.
    - Initialize an AsyncOpenAI client to interact with the OpenAI API.
    - Prepare the text chunks by converting them to strings if they are instances of TextChunk.
    - Initialize an empty list to store embeddings.
    - Iterate over the prepared text chunks in batches of size BATCH_SIZE.
    - For each batch, asynchronously request embeddings from the OpenAI API using the specified model.
    - Extract and accumulate the embeddings from the API response into the embeddings list.
    - Return the list of accumulated embeddings.
- **Output**:
    - A list of embeddings corresponding to the input text chunks.


---
### batch_embed_text 
The `batch_embed_text` function generates embeddings for a list of text chunks using a specified OpenAI model.
- **Inputs**:
    - `text_chunks`: A list of text chunks, which can be either strings or instances of the `TextChunk` class, to be embedded.
    - `model`: An optional string specifying the OpenAI model to use for embedding, defaulting to the environment variable `TEXT_EMBEDDING_MODEL` or 'text-embedding-3-small'.
- **Control Flow**:
    - Check if the specified model is in the list of supported models; if not, raise a `ValueError`.
    - Instantiate an `OpenAI` client to interact with the OpenAI API.
    - Prepare the text chunks by converting them to strings if they are instances of `TextChunk`, using the helper function `_prepare_text_chunks`.
    - Call the `embeddings.create` method on the `OpenAI` client with the prepared text chunks and specified model to generate embeddings.
    - Extract and return the list of embeddings from the response data.
- **Output**:
    - A list of embeddings corresponding to the input text chunks.


