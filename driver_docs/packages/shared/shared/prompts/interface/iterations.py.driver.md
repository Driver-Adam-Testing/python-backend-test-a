# Purpose
This code file is a collection of string templates and associated dictionaries, which are likely used for generating messages in an iterative process involving tool execution and context retrieval. The functionality provided is narrow, focusing specifically on defining prompts for different stages of an iteration process: the first, middle, and final iterations. Each prompt is stored as a multi-line string and is paired with a dictionary that assigns a "role" and "content" to the message, suggesting that these are intended for use in a system that processes user roles and content dynamically. The use of placeholders like `{remaining_iterations}` indicates that these prompts are designed to be formatted with specific iteration data at runtime, making them adaptable to different contexts within the iteration cycle.
# Global Variables

---
### MESSAGE_FINAL_ITERATION 
- **Type**: `dict`
- **Description**: The variable `MESSAGE_FINAL_ITERATION` is a dictionary that contains a single key-value pair. The key is 'role' with the value 'user', and the key 'content' with the value being a string stored in `PROMPT_FINAL_ITERATION`. This string provides instructions for the final iteration of a process, emphasizing the need to return a response and ensure code correctness.
- **Use**: This variable is used to store and convey the final iteration instructions to the user, ensuring that a response is returned and that any code provided is correct.


---
### MESSAGE_FIRST_ITERATION 
- **Type**: `dict`
- **Description**: The variable `MESSAGE_FIRST_ITERATION` is a dictionary with two keys: 'role' and 'content'. The 'role' key is assigned the value 'user', and the 'content' key is assigned the value of the string stored in `PROMPT_FIRST_ITERATION`. This string provides instructions for executing tools during the first iteration of a process, emphasizing the need to retrieve initial context and indicating the number of remaining opportunities to execute tools.
- **Use**: This variable is used to store and convey the initial instructions and context for a user role during the first iteration of a tool execution process.


---
### MESSAGE_MIDDLE_ITERATION 
- **Type**: `dict`
- **Description**: `MESSAGE_MIDDLE_ITERATION` is a dictionary that contains a key-value pair where the key is 'role' with a value of 'user', and the key 'content' with a value that is a multi-line string template. This template provides instructions for reviewing source code and executing tools during the middle iterations of a process.
- **Use**: This variable is used to store and convey instructions to the user during the middle iterations of a tool execution process, ensuring that the user follows the correct procedure for retrieving and reviewing source code.


---
### PROMPT_FINAL_ITERATION 
- **Type**: `str`
- **Description**: PROMPT_FINAL_ITERATION is a string variable that contains a template message for the final iteration of a process. It instructs the user to return a response, ensuring that any code or diagrams are syntactically correct and based on source code results from tools.
- **Use**: This variable is used to provide a predefined message template for the final iteration, guiding the user to return a response based on tool results.


---
### PROMPT_FIRST_ITERATION 
- **Type**: `str`
- **Description**: `PROMPT_FIRST_ITERATION` is a string variable that contains a multi-line prompt message. This message is intended to guide the execution of tools during the first iteration of a process, emphasizing the need to retrieve initial context and informing the user of the remaining opportunities to execute tools.
- **Use**: This variable is used to provide a structured prompt for the first iteration of a tool execution process, ensuring that initial context is gathered.


---
### PROMPT_MIDDLE_ITERATION 
- **Type**: `str`
- **Description**: PROMPT_MIDDLE_ITERATION is a string variable that contains a multi-line prompt message used during the middle iterations of a process involving tool execution and source code review. It provides instructions on how to proceed based on the results obtained from previous tool executions, emphasizing the need for source code results before returning a response.
- **Use**: This variable is used to guide the user during the middle iterations of a process, ensuring they execute necessary tools and review source code before proceeding.


