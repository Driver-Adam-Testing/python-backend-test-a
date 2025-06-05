# Purpose
This Python code defines two classes, `MultiShotIterationContextMessage` and `IterationMessage`, both of which extend the `LlmMessage` class. The primary purpose of this file is to facilitate communication in a multi-iteration process, likely within a larger system that involves iterative tasks or interactions. The `MultiShotIterationContextMessage` class provides a template message that sets the context for operating in a multi-iteration mode, emphasizing the importance of iterating until a task is resolved to the highest quality. It also specifies that the final response should be in markdown format and not a tool call or description thereof.

The `IterationMessage` class is designed to generate messages specific to each iteration of the process. It includes a class method `from_context` that constructs an `IterationMessage` based on the current iteration and the total number of iterations. This method dynamically adjusts the message content to guide the process, indicating whether tools should be executed or if a final response should be returned. The code is structured to be part of a broader system, likely a library or module, that handles iterative tasks, and it defines a clear interface for generating context-specific messages during these iterations.
# Imports and Dependencies

---
- `shared.v3.globals.constants`
- `shared.v3.interfaces.llm_message`
- `shared.v3.interfaces.llm_message_kind`


# Global Variables

---
### content 
- **Type**: `str`
- **Description**: The `content` variable is a string that holds the message text for different iterations in the `IterationMessage` class. It provides specific instructions or information based on the current iteration of a task, such as whether tools should be executed or if a final response should be returned.
- **Use**: This variable is used to store and convey iteration-specific messages within the `IterationMessage` class, guiding the behavior of the iteration process.


---
### message_kind 
- **Type**: `MessageKind`
- **Description**: The `message_kind` variable is a class attribute of type `MessageKind` used in both `MultiShotIterationContextMessage` and `IterationMessage` classes. It is set to `MessageKind.ITERATION`, indicating that these messages are related to iteration processes.
- **Use**: This variable is used to categorize messages as iteration-related within the context of multi-iteration tasks.


# Classes

---
### IterationMessage 
- **Type**: `class`
- **Members**:
    - `message_kind`: Specifies the kind of message, set to MessageKind.ITERATION.
- **Description**: The `IterationMessage` class is a specialized message type that inherits from `LlmMessage` and is used to handle iterative processes in a multi-iteration context. It provides a class method `from_context` that generates an `IterationMessage` instance based on the current iteration and total iterations, guiding the execution of tools and responses based on the iteration stage. The message content varies depending on whether it is the first, an intermediate, or the final iteration, ensuring that the process is completed with the necessary context and tool executions.
- **Inherits From**:
    - LlmMessage

**Methods**

---
#### IterationMessage.from_context
The `from_context` function generates an `IterationMessage` with specific instructions based on the current iteration and total iterations.
- **Inputs**:
    - `iteration`: The current iteration number, indicating the progress in a series of iterations.
    - `total_iterations`: The total number of iterations planned, used to determine the remaining iterations and the context of the current iteration.
- **Control Flow**:
    - Calculate the remaining iterations by subtracting the current iteration from the total iterations.
    - Check if the current iteration is the first one; if so, set the content to instruct tool execution and mention the remaining iterations.
    - If the current iteration is not the first but less than the total, set the content to instruct conditional response based on context completeness and mention the remaining iterations.
    - If the current iteration is the last one, set the content to instruct returning a response without further tool execution.
- **Output**:
    - Returns an instance of `IterationMessage` with a content string that provides instructions based on the iteration context.



---
### MultiShotIterationContextMessage 
- **Type**: `class`
- **Members**:
    - `message_kind`: Specifies the kind of message, set to MessageKind.ITERATION.
    - `content`: Contains a detailed string message guiding the operation in multi-iteration mode.
- **Description**: The `MultiShotIterationContextMessage` class is a specialized message class that inherits from `LlmMessage` and is used to convey instructions for operating in a multi-iteration mode. It defines a specific message kind and provides a detailed content string that outlines the iterative process, emphasizing the need for high-quality task resolution and the conditions under which final responses should be made. The class ensures that the final response is always in markdown format and not a tool call, guiding users to refine their requests if necessary.
- **Inherits From**:
    - LlmMessage


