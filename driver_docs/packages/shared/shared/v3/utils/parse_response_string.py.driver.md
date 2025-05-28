# Purpose
This Python code provides a specialized utility function designed to extract and parse JSON objects or arrays from a given string. The primary functionality is encapsulated in the `parse_response_string` function, which scans the input string for valid JSON structures, ignoring any surrounding or interspersed non-JSON text. The function attempts to parse JSON objects or arrays whenever it encounters a '{' or '[', and it continues scanning the string even if a parsing attempt fails. The function returns a single JSON object or array if only one is found, or a list of such objects if multiple are detected. If no valid JSON is found, it raises a custom exception, `ParseOutputError`, which provides feedback on the failure and includes the problematic input string.

The code is structured as a utility module, likely intended for use as part of a larger application where JSON data might be embedded within other text. It does not define a public API or external interface beyond the `parse_response_string` function and the `ParseOutputError` exception class. The use of regular expressions to clean up trailing commas and the JSONDecoder for parsing highlights the technical approach taken to handle potentially malformed JSON data. This module is particularly useful in scenarios where JSON data is extracted from logs, mixed content, or other non-standard sources.
# Imports and Dependencies

---
- `json`
- `re`


# Classes

---
### ParseOutputError 
- **Type**: `class`
- **Members**:
    - `input_str`: Stores the input string that could not be parsed into valid JSON.
- **Description**: The `ParseOutputError` class is a custom exception that inherits from Python's built-in `Exception` class. It is specifically designed to be raised when a string cannot be parsed into valid JSON. The class constructor takes a message and the input string that caused the error, storing the input string as an instance variable and passing a formatted error message to the base `Exception` class.
- **Inherits From**:
    - Exception

**Methods**

---
#### ParseOutputError.__init__
The __init__ method initializes a ParseOutputError exception with a custom message and input string.
- **Inputs**:
    - `message`: A string representing the error message to be included in the exception.
    - `input_str`: A string representing the input that caused the error, which will be stored as an instance attribute.
- **Control Flow**:
    - Assigns the input_str parameter to an instance attribute self.input_str.
    - Calls the superclass's __init__ method with a formatted message combining the message and input_str.
- **Output**:
    - This method does not return any value as it is a constructor for initializing an instance of the ParseOutputError class.



# Functions

---
### parse_response_string 
The function `parse_response_string` scans a string for valid JSON objects or arrays, ignoring surrounding text, and returns them as a single object or a list, or raises an error if none are found.
- **Inputs**:
    - `str_to_parse`: A string that potentially contains JSON objects or arrays, possibly interspersed with non-JSON text.
- **Control Flow**:
    - The function first removes trailing commas before '}' or ']' in the input string to prevent JSON parsing errors.
    - It initializes an empty list `results` to store successfully parsed JSON objects or arrays and a JSONDecoder instance for parsing.
    - A while loop iterates over the string, searching for the next '{' or '[' to identify potential JSON starts.
    - If a match is found, it attempts to decode a JSON object or array starting from the matched position using `raw_decode`.
    - If decoding is successful, the object is added to `results`, and the index is moved to the end of the parsed JSON.
    - If decoding fails, the index is incremented to skip the current bracket and continue searching.
    - After the loop, if no valid JSON is found, a `ParseOutputError` is raised.
    - If exactly one JSON object or array is found, it is returned directly; otherwise, all found objects/arrays are returned in a list.
- **Output**:
    - The function returns a single JSON object or array if exactly one is found, a list of JSON objects/arrays if multiple are found, or raises a `ParseOutputError` if none are found.


