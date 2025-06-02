# Purpose
This Python code provides functionality for text processing, specifically focusing on splitting text into manageable chunks and counting tokens using a specified model. The code is structured as a utility module, likely intended to be imported and used in other scripts or applications that require text manipulation. The primary components include a `TextChunk` data class, which encapsulates information about each text chunk, such as the text itself, its starting line, starting token, and the list of tokens. The `split_text` function is the core of this module, designed to divide a given text into chunks based on a specified model and token, with configurable chunk size and overlap. This function uses the `tiktoken` library to encode and decode text, ensuring that the chunks are appropriately sized and overlap as needed.

Additionally, the module includes a `get_num_tokens` function, which calculates the number of tokens in a given text using the specified model. This function is useful for understanding the tokenization of text, which is crucial in applications like natural language processing where token limits may apply. The code is designed to be flexible, allowing for different models to be specified, although the current implementation only supports splitting based on a predefined token. The use of the `tiktoken` library suggests that this module is intended for use with models that require token-based text processing, such as those in the GPT series.
# Imports and Dependencies

---
- `dataclasses`
- `tiktoken`


# Global Variables

---
### TOKEN 
- **Type**: `str`
- **Description**: `TOKEN` is a global string variable initialized with the value "token". It is used as a default delimiter for splitting text in the `split_text` function.
- **Use**: This variable is used as the default value for the `split_on` parameter in the `split_text` function to determine how the input text should be split into chunks.


# Classes

---
### TextChunk 
- **Type**: `dataclass`
- **Members**:
    - `text`: The text content of the chunk.
    - `start_line`: The starting line number of the chunk in the original text.
    - `start_token`: The starting token index of the chunk in the original text.
    - `tokens`: A list of token indices representing the chunk.
- **Description**: The `TextChunk` class is a data structure used to represent a segment of text that has been tokenized and split from a larger body of text. It stores the actual text of the chunk, the starting line and token indices from the original text, and a list of token indices that make up the chunk. This class is particularly useful for handling text processing tasks where text needs to be divided into manageable pieces for further analysis or processing.


# Functions

---
### get_num_tokens 
The function `get_num_tokens` calculates the number of tokens in a given text using a specified model's encoding.
- **Inputs**:
    - `text`: A string representing the input text whose tokens are to be counted.
    - `model`: An optional string specifying the model to use for encoding, defaulting to 'gpt-4'.
- **Control Flow**:
    - Retrieve the encoder for the specified model using `tiktoken.encoding_for_model(model)`.
    - Encode the input text using the retrieved encoder, ignoring any special disallowed tokens.
    - Return the length of the encoded token list, which represents the number of tokens in the input text.
- **Output**:
    - An integer representing the number of tokens in the input text.


---
### split_text 
The `split_text` function divides a given text into chunks based on a specified model and token, returning a list of `TextChunk` objects.
- **Inputs**:
    - `text`: The input text to be split into chunks.
    - `model`: The model used for encoding the text, defaulting to 'gpt-4'.
    - `split_on`: The parameter determining the method of splitting, defaulting to 'TOKEN'.
    - `chunk_size`: The maximum size of each chunk, defaulting to 512 tokens.
    - `chunk_overlap`: The number of tokens that overlap between consecutive chunks, defaulting to 64 tokens.
- **Control Flow**:
    - Initialize an empty list `chunks` to store the resulting text chunks.
    - Check if `split_on` is equal to `TOKEN`; if not, raise a `NotImplementedError`.
    - Use the `tiktoken` library to get an encoder for the specified model.
    - Encode the input text into tokens using the encoder.
    - Initialize `line_number` and `token_number` to zero to track the starting line and token of each chunk.
    - Iterate over the tokens in steps of `chunk_size - chunk_overlap` to create chunks.
    - For each chunk, decode the tokens back to text and create a `TextChunk` object with the decoded text, starting line, starting token, and the list of tokens.
    - Append each `TextChunk` object to the `chunks` list.
    - Update `line_number` and `token_number` based on the number of newlines and tokens in the current chunk.
    - Return the list of `TextChunk` objects.
- **Output**:
    - A list of `TextChunk` objects, each containing a portion of the original text, the starting line number, the starting token number, and the list of tokens for that chunk.


