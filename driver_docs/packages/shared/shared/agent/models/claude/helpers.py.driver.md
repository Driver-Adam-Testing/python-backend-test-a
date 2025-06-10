# Purpose
This Python code file is designed to facilitate the interaction with a set of tools by formatting and parsing XML-based tool descriptions and function calls. The primary functionality is to generate a structured prompt that describes available tools and their parameters, allowing users to understand how to invoke these tools. The `format_tool_prompt` function constructs an XML-like string that details each tool's name, description, and parameters, which can be used to guide users in making function calls. The code also includes a `parse_tool_calls_from_response` function that extracts and parses tool invocation details from a given XML response, creating instances of `ToolCall` objects that encapsulate the function name and its parameters. Additionally, the `format_tool_results` function formats the results of tool executions into an XML-like structure, providing a standardized way to present the output of tool invocations.

The code is structured as a utility module that can be integrated into larger systems where tool invocation and result formatting are required. It defines classes such as `Function` and `ToolCall` to encapsulate the concept of a tool function and its invocation, respectively. The use of regular expressions and XML parsing through the `xml.etree.ElementTree` module indicates that the code is designed to handle structured data efficiently. This module does not define a public API but rather provides internal functions and classes that can be used by other components of a software system to manage tool interactions in a consistent and structured manner.
# Imports and Dependencies

---
- `re`
- `xml.etree.ElementTree`
- `inspect.signature`


# Classes

---
### Function 
- **Type**: `class`
- **Members**:
    - `name`: Stores the name of the function.
    - `arguments`: Holds the arguments associated with the function.
- **Description**: The `Function` class is a simple data structure used to represent a function with its name and associated arguments. It is primarily used to encapsulate the details of a function call, allowing for easy manipulation and access to the function's name and its parameters. This class is utilized in the context of tool calls, where functions are invoked with specific arguments.

**Methods**

---
#### Function.__init__
The `__init__` function initializes a `Function` object with a name and arguments.
- **Inputs**:
    - `name`: The name of the function, which is a string representing the function's identifier.
    - `arguments`: The arguments of the function, which is a dictionary containing parameter names and their corresponding values.
- **Control Flow**:
    - The function assigns the provided `name` to the instance variable `self.name`.
    - The function assigns the provided `arguments` to the instance variable `self.arguments`.
- **Output**:
    - The function does not return any value; it initializes the instance variables of the `Function` class.



---
### ToolCall 
- **Type**: `class`
- **Members**:
    - `function`: Holds the function associated with the tool call.
    - `id`: An identifier for the tool call, initially set to None.
- **Description**: The `ToolCall` class is a simple structure used to encapsulate a function and an optional identifier. It is primarily used to represent a call to a tool, where the `function` attribute holds the function to be called, and the `id` attribute can be used to store an identifier for the call, though it is initialized as None. This class is utilized in the context of parsing and handling tool calls from XML responses.

**Methods**

---
#### ToolCall.__init__
The `__init__` function initializes a `ToolCall` object with a given function and sets its ID to `None`.
- **Inputs**:
    - `function`: The function to be associated with the `ToolCall` object, typically an instance of the `Function` class.
- **Control Flow**:
    - Assigns the input `function` to the `function` attribute of the `ToolCall` instance.
    - Sets the `id` attribute of the `ToolCall` instance to `None`.
- **Output**:
    - This function does not return any value; it initializes an instance of the `ToolCall` class.



# Functions

---
### format_tool_prompt 
The `format_tool_prompt` function generates a formatted XML-like string that describes a set of tools and their parameters for use in a specific environment.
- **Inputs**:
    - `tools`: A list of tool objects, where each tool has a `name`, `description`, and a `function` with parameters.
- **Control Flow**:
    - Initialize an empty list `tool_descriptions` to store descriptions of each tool.
    - Iterate over each tool in the `tools` list.
    - For each tool, create a string `tool_description` that includes the tool's name and description.
    - Use the `inspect.signature` function to retrieve the signature of the tool's function.
    - Iterate over the parameters of the function, excluding 'agent_context', and append each parameter's name and type to the `tool_description`.
    - Complete the `tool_description` by closing the XML-like tags and append it to `tool_descriptions`.
    - Concatenate all tool descriptions into a single string and embed it within a larger XML-like template string `CLAUDE_TOOL_PROMPT`.
    - Return the `CLAUDE_TOOL_PROMPT` string.
- **Output**:
    - A formatted string that describes the available tools and their parameters in an XML-like structure.


---
### format_tool_results 
The `format_tool_results` function formats the results of tool executions into an XML-like string structure.
- **Inputs**:
    - `tool_names`: A list of tool names corresponding to each result.
    - `args`: A list of arguments that were passed to each tool.
    - `results`: A list of results returned by each tool.
- **Control Flow**:
    - Initialize an empty string `formatted_results` to accumulate formatted result entries.
    - Iterate over the `tool_names`, `args`, and `results` lists simultaneously using `zip`, allowing for different lengths with `strict=False`.
    - For each tool name, argument, and result, append a formatted XML-like string to `formatted_results`, embedding the tool name, argument, and result.
    - After the loop, wrap the accumulated `formatted_results` in a `<function_results>` tag to form the final XML-like structure.
    - Return the complete formatted string as `FORMAT_TOOL_RESULTS`.
- **Output**:
    - A string containing the formatted results of tool executions, structured in an XML-like format with each tool's name, argument, and result.


---
### parse_tool_calls_from_response 
The function `parse_tool_calls_from_response` extracts and parses tool call information from an XML-formatted response string.
- **Inputs**:
    - `response`: A string containing XML-formatted data with tool call information enclosed within <function_calls> tags.
- **Control Flow**:
    - Initialize an empty list `tool_calls` to store parsed tool call objects.
    - Use a regular expression to find all XML blocks enclosed within <function_calls> tags in the `response` string.
    - Iterate over each XML block found.
    - Parse each XML block into an ElementTree object `root`.
    - Find all <invoke> elements within the `root` using XPath.
    - For each <invoke> element, extract the text of the <tool_name> element and store it in `tool_name`.
    - Extract all child elements of <parameters> within the <invoke> element, and create a dictionary `parameters` mapping each parameter's tag to its text.
    - Create a `Function` object using `tool_name` and `parameters`.
    - Create a `ToolCall` object using the `Function` object.
    - Append the `ToolCall` object to the `tool_calls` list.
    - Return the `tool_calls` list containing all parsed tool call objects.
- **Output**:
    - A list of `ToolCall` objects, each representing a parsed tool call with its associated function name and parameters.


