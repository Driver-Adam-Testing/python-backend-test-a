# Purpose
This Python code file provides utility functions related to string manipulation and token counting, specifically in the context of using OpenAI's chat completions API. The file includes two main functions: `chunk_str` and `num_tokens_from_messages_open_ai`. The `chunk_str` function is designed to divide a given string into chunks of a specified size with a defined overlap, which can be useful for processing large strings in manageable parts. The `num_tokens_from_messages_open_ai` function estimates the number of tokens used by a list of messages when interacting with OpenAI's models, such as "gpt-3.5-turbo" and "gpt-4". This function is adapted from the OpenAI cookbook and provides a rough estimate of token usage, which is crucial for understanding and managing API usage costs.

The file imports several modules, including `logging` for logging warnings and errors, `tiktoken` for encoding messages, and a `decorators` module from a shared utilities package. The `num_tokens_from_messages_open_ai` function uses a decorator to suppress logging, indicating that it is designed to run quietly without logging output. The code is structured to handle different versions of OpenAI models, providing specific token counts for each and handling potential updates to the models. This file is likely part of a larger library or application that interacts with OpenAI's API, providing essential utilities for managing string data and estimating API usage.
# Imports and Dependencies

---
- `logging`
- `tiktoken`
- `shared.utils.decorators`


# Global Variables

---
### logger 
- **Type**: `logging.Logger`
- **Description**: The `logger` variable is an instance of the `Logger` class from the Python `logging` module. It is configured to use the name of the current module as its logger name, which is typically the module's `__name__` attribute. This logger is used to record log messages, such as warnings, during the execution of the program.
- **Use**: This variable is used to log warning messages when certain conditions are met, such as when a model is not found or when a model may update over time.


# Functions

---
### chunk_str 
The `chunk_str` function divides a string into overlapping chunks of a specified size.
- **Inputs**:
    - `chunk_size`: The size of each chunk to be created from the input string.
    - `chunk_overlap`: The number of characters that each chunk should overlap with the previous chunk.
    - `str_in`: The input string that needs to be divided into chunks.
- **Control Flow**:
    - Calculate the number of chunks needed by dividing the length of the input string by the effective chunk size (chunk_size - chunk_overlap) and adding one.
    - Determine the step size for each chunk, which is the effective chunk size (chunk_size - chunk_overlap).
    - Use a list comprehension to iterate over the range of the number of chunks, slicing the input string from the current index times the step size to the next index times the step size.
- **Output**:
    - A list of strings, each representing a chunk of the input string with the specified overlap.


---
### num_tokens_from_messages_open_ai 
The function estimates the number of tokens used by a list of messages for a specified OpenAI model.
- **Inputs**:
    - `messages`: A list of string messages for which the token count is to be estimated.
    - `model`: An optional string specifying the OpenAI model to use for encoding, defaulting to 'gpt-3.5-turbo-0613'.
- **Control Flow**:
    - Attempt to get the encoding for the specified model using tiktoken; if the model is not found, use a default encoding 'cl100k_base'.
    - Determine the number of tokens per message based on the specified model; different models have different token structures.
    - If the model is a variant of 'gpt-3.5-turbo' or 'gpt-4', issue a warning and recursively call the function with a default model version to ensure compatibility.
    - Raise a NotImplementedError if the model is not supported, providing a link for more information.
    - Iterate over each message, adding the tokens per message and the length of the encoded message to the total token count.
    - Add an additional 3 tokens to account for the reply priming structure.
    - Return the total number of tokens calculated.
- **Output**:
    - The function returns an integer representing the estimated number of tokens used by the messages for the specified model.


