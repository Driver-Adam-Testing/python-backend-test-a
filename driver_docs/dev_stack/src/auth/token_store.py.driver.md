# Purpose
This code is a short script that provides narrow functionality for managing token data in a JSON file located in the user's home directory. It defines a constant `TOKEN_FILE` that specifies the path to the file `.driver_cli.json`, which is used to store token information. The script includes three functions: `save_tokens(tokens)`, which writes a dictionary of tokens to the file; `load_tokens()`, which reads and returns the token data if the file exists, or returns `None` if it does not; and `clear_tokens()`, which deletes the token file if it exists. This script is likely part of a larger application, serving as a utility for handling authentication or session tokens in a command-line interface (CLI) environment.
# Imports and Dependencies

---
- `json`
- `pathlib.Path`


# Global Variables

---
### TOKEN_FILE 
- **Type**: `Path`
- **Description**: `TOKEN_FILE` is a global variable that represents the file path to a JSON file named ".driver_cli.json" located in the user's home directory. It is used to store and manage token data for a CLI application.
- **Use**: This variable is used as the file path for saving, loading, and clearing token data in the application.


# Functions

---
### clear_tokens 
The `clear_tokens` function deletes the token file if it exists.
- **Inputs**:
    - None
- **Control Flow**:
    - Check if the `TOKEN_FILE` exists using the `exists()` method.
    - If the file exists, delete it using the `unlink()` method.
- **Output**:
    - The function does not return any value; it performs a file deletion operation if the file exists.


---
### load_tokens 
The `load_tokens` function reads and returns JSON data from a predefined file if it exists, otherwise it returns None.
- **Inputs**:
    - None
- **Control Flow**:
    - Check if the file specified by `TOKEN_FILE` exists.
    - If the file exists, open it and load its contents as JSON, then return the loaded data.
    - If the file does not exist, return `None`.
- **Output**:
    - The function returns the JSON data loaded from the file if it exists, otherwise it returns `None`.


---
### save_tokens 
The `save_tokens` function writes a given dictionary of tokens to a JSON file located at a predefined path.
- **Inputs**:
    - `tokens`: A dictionary containing token data that needs to be saved to a file.
- **Control Flow**:
    - Open the file specified by the global variable `TOKEN_FILE` in write mode.
    - Use the `json.dump` method to write the `tokens` dictionary to the file.
- **Output**:
    - The function does not return any value; it performs a file write operation to save the tokens.


