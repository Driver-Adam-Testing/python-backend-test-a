# Purpose
This Python code file is designed to facilitate the extraction and documentation of various components within a source code file, such as functions, variables, and data structures, using a language model (LLM) like OpenAI's ChatGPT. The file defines a series of classes and functions that work together to analyze code, identify key elements, and generate structured documentation. The primary functionality revolves around the use of prompts to guide the LLM in identifying and describing these elements, with specific prompts tailored for imports, functions, variables, and data structures. The code is structured to handle both single and multi-prompt scenarios, allowing for the processing of large codebases by splitting them into manageable chunks.

The file includes several classes that represent collections of symbols, such as `DefaultFnRawSymbolCollection`, `DefaultVariableRawSymbolCollection`, and `DefaultDataStructureRawSymbolCollection`, each responsible for handling a specific type of code element. These classes provide methods for extracting information from the code using the LLM and converting it into a structured format. Additionally, the file defines intermediate representation (IR) classes like `DefaultFnData`, `DefaultVariableData`, and `DefaultDataStructureData`, which are used to transform raw symbol data into a more detailed and documented form. Overall, this code serves as a library intended to be imported and used in other projects to automate the process of code analysis and documentation generation.
# Imports and Dependencies

---
- `pathlib`
- `typing`
- `openai`
- `utils.models`
- `shared.chunking.text_splitter`


# Global Variables

---
### DATA_STRUCTURES_CHECKER_SYSTEM_PROMPT_JSON 
- **Type**: `str`
- **Description**: The variable `DATA_STRUCTURES_CHECKER_SYSTEM_PROMPT_JSON` is a string that contains a JSON schema template. This template is used to guide the extraction of important data structures from a given code snippet. It specifies the format in which the data structures should be listed, ensuring consistency in the output.
- **Use**: This variable is used to define the expected JSON schema for listing important data structures in code analysis.


---
### DATA_STRUCTURES_FOUND_SYSTEM_PROMPT_JSON 
- **Type**: `str`
- **Description**: The `DATA_STRUCTURES_FOUND_SYSTEM_PROMPT_JSON` is a string variable that contains a JSON schema template. This template is used to guide the documentation of data structures by specifying the format and content required for describing them.
- **Use**: This variable is used to provide a structured format for documenting data structures in code.


---
### DATA_STRUCTURES_FOUND_USER_PROMPT 
- **Type**: `str`
- **Description**: The `DATA_STRUCTURES_FOUND_USER_PROMPT` is a string variable that contains a template for a user prompt. This prompt is used to instruct a user to summarize a data structure in the provided code. It includes guidelines on how to describe the data structure, emphasizing the need for detail that matches the complexity of the data structure.
- **Use**: This variable is used to provide a consistent and structured prompt for users to document data structures in code.


---
### FUNCTIONS_CHECKER_SYSTEM_PROMPT_JSON 
- **Type**: `string`
- **Description**: The `FUNCTIONS_CHECKER_SYSTEM_PROMPT_JSON` variable is a string that contains a JSON schema template. This template is used to guide the extraction of function definitions from a given codebase by specifying the expected format of the response, which includes a list of function names.
- **Use**: This variable is used to define the expected JSON schema for listing functions in a codebase.


---
### FUNCTIONS_FOUND_SYSTEM_PROMPT_JSON 
- **Type**: `string`
- **Description**: The `FUNCTIONS_FOUND_SYSTEM_PROMPT_JSON` variable is a string that contains a JSON schema template. This template is used to guide the documentation process for functions found in a given codebase. It specifies the format and content required for documenting functions, including a single sentence description, inputs, control flow, and output.
- **Use**: This variable is used to standardize the documentation process for functions by providing a structured format.


---
### FUNCTIONS_FOUND_USER_PROMPT 
- **Type**: `str`
- **Description**: `FUNCTIONS_FOUND_USER_PROMPT` is a string variable that contains a template for a user prompt. This prompt is used to instruct a system to summarize a function in the provided code, focusing on inputs, control flow, logic, and output.
- **Use**: This variable is used to generate a user prompt for summarizing functions in code.


---
### IMPORTS_SYSTEM_PROMPT_JSON 
- **Type**: `str`
- **Description**: `IMPORTS_SYSTEM_PROMPT_JSON` is a string variable that contains a JSON schema template. This template is used to identify and list the imports and dependencies in a given piece of code. The schema specifies that the response should be a JSON object with a single key, `data`, which is an array of import names.
- **Use**: This variable is used to guide the extraction of import statements from code by providing a structured format for the output.


---
### SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT 
- **Type**: `str`
- **Description**: `SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT` is a string variable that contains a detailed prompt for explaining the purpose of a source code file. It guides the user to write a comprehensive explanation of the file's purpose, considering various aspects such as functionality, technical components, and the nature of the code.
- **Use**: This variable is used to provide a detailed prompt for users to explain the purpose of a source code file in a structured manner.


---
### SOURCE_CODE_SMALL_PURPOSE_USER_PROMPT 
- **Type**: `str`
- **Description**: `SOURCE_CODE_SMALL_PURPOSE_USER_PROMPT` is a string variable that contains a template for generating a concise explanation of a source code file's purpose. It prompts the user to consider specific questions about the code's functionality and type when writing their explanation.
- **Use**: This variable is used to guide users in writing a brief summary of a source code file's purpose.


---
### SOURCE_CODE_SYSTEM_PROMPT_GENERAL_DEFAULT 
- **Type**: `str`
- **Description**: The variable `SOURCE_CODE_SYSTEM_PROMPT_GENERAL_DEFAULT` is a string that contains a template for a system prompt. This prompt is designed for a software engineering documentation expert, emphasizing the ability to explain technical details and articulate key conceptual components and purposes of software.
- **Use**: This variable is used as a default system prompt for generating documentation related to software engineering.


---
### TECHNICAL_CONCEPTS 
- **Type**: `str`
- **Description**: The `TECHNICAL_CONCEPTS` variable is a string that contains a template for describing the important technical features and their interactions in a source code file. It guides the user to focus on conceptual use cases, applications, logic, and component interactions rather than specific functions or variables.
- **Use**: This variable is used as a prompt template to instruct users on how to describe technical concepts in a source code file.


---
### VARIABLES_CHECKER_SYSTEM_PROMPT_JSON 
- **Type**: `string`
- **Description**: The `VARIABLES_CHECKER_SYSTEM_PROMPT_JSON` is a string variable that contains a JSON schema formatted prompt. This prompt is used to instruct a system to list any global variables defined in a given code snippet. It specifies the criteria for identifying global variables and the expected JSON response format.
- **Use**: This variable is used to provide a structured prompt for identifying global variables in a code analysis context.


---
### VARIABLES_FOUND_SYSTEM_PROMPT_JSON 
- **Type**: `string`
- **Description**: The `VARIABLES_FOUND_SYSTEM_PROMPT_JSON` is a string variable that contains a JSON schema template. This template is used to guide the documentation of global variables in Python code, ensuring that the documentation is consistent and follows a specific format. The schema includes fields for the type, description, and use of the variable.
- **Use**: This variable is used to provide a structured format for documenting global variables in Python code.


---
### VARIABLES_FOUND_USER_PROMPT 
- **Type**: `string`
- **Description**: `VARIABLES_FOUND_USER_PROMPT` is a string variable that contains a multi-line prompt. This prompt is designed to instruct a user or system on how to summarize a global variable in a given code snippet. It provides guidelines on what constitutes a global variable and how to document it effectively.
- **Use**: This variable is used to provide a template or guideline for summarizing global variables in code documentation.


# Classes

---
### DefaultDataStructureCollection 
- **Type**: `class`
- **Members**:
    - `data`: A dictionary mapping strings to either DefaultDataStructureData or a list of DefaultDataStructureData.
- **Description**: The `DefaultDataStructureCollection` class is a specialized collection class that inherits from `IrCollection`. It is designed to manage a collection of data structures, specifically `DefaultDataStructureData` objects, which can be stored either individually or as lists within a dictionary. The class provides a class method `from_llm` to instantiate the collection using a language model (`llm`) and a list of symbols (`symbols_list`), leveraging the `from_llm_with_ir_data` method to populate the collection with the appropriate data structure instances.
- **Inherits From**:
    - IrCollection

**Methods**

---
#### DefaultDataStructureCollection.from_llm
The `from_llm` function creates an instance of the class by invoking the `from_llm_with_ir_data` method with a default data structure, a language model, and a collection of symbols.
- **Inputs**:
    - `llm`: An instance of the ChatOpenAI class, representing a language model.
    - `symbols_list`: An instance of RawSymbolCollection, representing a collection of raw symbols.
- **Control Flow**:
    - The function calls the `from_llm_with_ir_data` method on the class `cls`.
    - It passes `DefaultDataStructureData`, `llm`, and `symbols_list` as arguments to the method.
    - The method returns an instance of the class `cls`.
- **Output**:
    - An instance of the class `cls` is returned, created using the provided language model and symbols list.



---
### DefaultDataStructureData 
- **Type**: `class`
- **Members**:
    - `system_prompt`: Returns a system prompt string for data structure documentation.
    - `user_prompt`: Generates a user prompt string for a given symbol's name and code.
    - `child_to_ir`: Raises NotImplementedError as default data structures should not have children.
    - `child_to_field_name`: Raises NotImplementedError as default data structures should not have children.
- **Description**: The `DefaultDataStructureData` class is a specialized subclass of `DataStructureData` designed to handle default data structures in a documentation context. It provides class methods to generate system and user prompts for documenting data structures, specifically tailored for use with language models. The class explicitly raises `NotImplementedError` for methods related to child data structures, indicating that default data structures are not expected to have children in this context.
- **Inherits From**:
    - DataStructureData

**Methods**

---
#### DefaultDataStructureData.child_to_field_name
The function `child_to_field_name` raises a `NotImplementedError` indicating that default data structures should not have children.
- **Inputs**:
    - `cls`: The class reference from which the method is called.
    - `child`: An instance of `RawSymbolData` representing a child symbol.
- **Control Flow**:
    - The function immediately raises a `NotImplementedError` with a specific message.
- **Output**:
    - The function does not return any value as it raises an exception.


---
#### DefaultDataStructureData.child_to_ir
The `child_to_ir` function raises a NotImplementedError indicating that default data structures should not have children.
- **Inputs**:
    - `cls`: The class type from which the method is called.
    - `symbol`: An instance of RawSymbolData representing the symbol data to be processed.
- **Control Flow**:
    - The function immediately raises a NotImplementedError with a specific message.
- **Output**:
    - The function does not return any value as it raises an exception.


---
#### DefaultDataStructureData.system_prompt
The `system_prompt` function returns a predefined JSON string for documenting data structures.
- **Inputs**:
    - None
- **Control Flow**:
    - The function directly returns the value of the constant `DATA_STRUCTURES_FOUND_SYSTEM_PROMPT_JSON`.
- **Output**:
    - The function outputs a string containing a JSON schema for documenting data structures.


---
#### DefaultDataStructureData.user_prompt
The `user_prompt` function generates a formatted string that includes a predefined prompt and the name and code of a given symbol.
- **Inputs**:
    - `cls`: The class object that the method is bound to, typically used in class methods.
    - `symbol`: An instance of `RawSymbolData` containing the name and file code of a symbol.
- **Control Flow**:
    - The function constructs a string by concatenating a predefined prompt with the symbol's name and its file code.
- **Output**:
    - A string that combines a predefined prompt with the symbol's name and its file code.



---
### DefaultDataStructureRawSymbolCollection 
- **Type**: `class`
- **Members**:
    - `data`: A dictionary mapping string keys to RawSymbolData objects.
- **Description**: The `DefaultDataStructureRawSymbolCollection` class is a specialized collection class that inherits from `RawSymbolCollection`. It is designed to handle collections of raw symbol data specifically related to data structures. The class provides methods to create instances from language model (LLM) analysis, but not from static analysis, as indicated by the `NotImplementedError` in the `from_static_analysis` method. The `from_llm` method utilizes a default LLM analysis function to populate the collection with data structure symbols extracted from code. The `to_dict` method returns the internal data dictionary, allowing access to the raw symbol data.
- **Inherits From**:
    - RawSymbolCollection

**Methods**

---
#### DefaultDataStructureRawSymbolCollection.from_llm
The `from_llm` function creates an instance of a class by analyzing code with a language model to identify data structures.
- **Inputs**:
    - `cls`: The class type that will be instantiated.
    - `llm`: An instance of the ChatOpenAI class used for language model analysis.
    - `code`: The source code to be analyzed by the language model.
    - `root_rel_path`: The root relative path of the source code file being analyzed.
- **Control Flow**:
    - The function calls `default_llm_analysis` with the provided class type, language model, code, root relative path, a predefined system prompt for data structures, an empty user prompt, and a symbol kind indicating data structures.
    - The `default_llm_analysis` function processes the code to identify data structures using the language model and returns an instance of the class with the identified data structures or None if no data structures are found.
- **Output**:
    - The function returns an instance of the class with identified data structures or None if no data structures are found.


---
#### DefaultDataStructureRawSymbolCollection.from_static_analysis
The `from_static_analysis` function is a placeholder method intended to be overridden, as it raises a NotImplementedError indicating that the default case should use the `from_llm` method instead.
- **Inputs**:
    - `cls`: The class on which this method is called, typically a subclass of RawSymbolCollection.
    - `code`: A string representing the source code to be analyzed.
    - `root_rel_path`: A Path object representing the root relative path of the source code file.
- **Control Flow**:
    - The function immediately raises a NotImplementedError with a specific message.
- **Output**:
    - The function does not return any value as it raises an exception.


---
#### DefaultDataStructureRawSymbolCollection.to_dict
The `to_dict` function returns the `data` attribute of the class instance as a dictionary.
- **Inputs**:
    - None
- **Control Flow**:
    - The function directly returns the `data` attribute of the class instance.
- **Output**:
    - A dictionary where keys are strings and values are `RawSymbolData` objects.



---
### DefaultFnCollection 
- **Type**: `class`
- **Members**:
    - `data`: A dictionary mapping strings to either DefaultFnData or a list of DefaultFnData.
- **Description**: The `DefaultFnCollection` class is a specialized collection class that inherits from `IrCollection`. It is designed to manage a collection of function data, specifically `DefaultFnData` objects, which can be stored individually or as lists within a dictionary. The class provides a class method `from_llm` that facilitates the creation of a `DefaultFnCollection` instance by leveraging a language model (`llm`) and a list of symbols (`symbols_list`). This method utilizes the `from_llm_with_ir_data` method to populate the collection with `DefaultFnData` instances.
- **Inherits From**:
    - IrCollection

**Methods**

---
#### DefaultFnCollection.from_llm
The `from_llm` function creates an instance of the class by invoking the `from_llm_with_ir_data` method with `DefaultFnData`, an LLM instance, and a symbols list.
- **Inputs**:
    - `llm`: An instance of the ChatOpenAI class, representing a language model.
    - `symbols_list`: An instance of RawSymbolCollection, representing a collection of raw symbols.
- **Control Flow**:
    - The function calls the `from_llm_with_ir_data` method on the class (`cls`) with `DefaultFnData`, `llm`, and `symbols_list` as arguments.
    - The result of the `from_llm_with_ir_data` method call is returned.
- **Output**:
    - The function returns an instance of the class (`cls`) created using the `from_llm_with_ir_data` method.



---
### DefaultFnData 
- **Type**: `class`
- **Members**:
    - `system_prompt`: Returns a predefined system prompt string for functions.
    - `user_prompt`: Generates a user prompt string using the provided symbol's name and file code.
    - `child_to_ir`: Raises a NotImplementedError indicating default functions should not have children.
    - `child_to_field_name`: Raises a NotImplementedError indicating default functions should not have children.
- **Description**: The `DefaultFnData` class is a specialized subclass of `FnData` designed to handle default function data within a system. It provides class methods to generate system and user prompts based on predefined templates and symbol data. The class explicitly raises `NotImplementedError` for methods related to child processing, indicating that default functions are not expected to have children in this context. This class is part of a larger framework for managing and documenting code symbols, particularly focusing on functions.
- **Inherits From**:
    - FnData

**Methods**

---
#### DefaultFnData.child_to_field_name
The `child_to_field_name` function raises a `NotImplementedError` indicating that default functions should not have children.
- **Inputs**:
    - `cls`: The class reference from which the method is called.
    - `child`: An instance of `RawSymbolData` representing a child symbol.
- **Control Flow**:
    - The function immediately raises a `NotImplementedError` with a specific message.
- **Output**:
    - The function does not return any value as it raises an exception.


---
#### DefaultFnData.child_to_ir
The `child_to_ir` function raises a NotImplementedError indicating that default functions should not have children.
- **Inputs**:
    - `cls`: The class type from which the method is called.
    - `symbol`: An instance of RawSymbolData representing a symbol.
- **Control Flow**:
    - The function immediately raises a NotImplementedError with a specific message.
- **Output**:
    - The function does not return any value as it raises an exception.


---
#### DefaultFnData.system_prompt
The `system_prompt` function returns a predefined JSON string used as a system prompt for function documentation.
- **Inputs**:
    - `cls`: The class method decorator `@classmethod` implies that `cls` is a reference to the class itself, not an instance of the class.
- **Control Flow**:
    - The function directly returns the constant `FUNCTIONS_FOUND_SYSTEM_PROMPT_JSON`.
- **Output**:
    - The function outputs a string that contains a JSON schema for documenting functions.


---
#### DefaultFnData.user_prompt
The `user_prompt` function generates a formatted string containing a user prompt and the code associated with a given symbol.
- **Inputs**:
    - `cls`: The class reference, typically used in class methods, but not utilized in this function.
    - `symbol`: An instance of `RawSymbolData` containing the name and file code of a symbol.
- **Control Flow**:
    - The function constructs a string by concatenating a predefined prompt with the symbol's name and its associated code.
- **Output**:
    - A string that includes a user prompt followed by the symbol's name and its code.



---
### DefaultFnRawSymbolCollection 
- **Type**: `class`
- **Members**:
    - `data`: A dictionary mapping string keys to RawSymbolData objects.
- **Description**: The `DefaultFnRawSymbolCollection` class is a specialized collection for handling raw symbol data related to functions. It inherits from `RawSymbolCollection` and provides methods to create instances from language model (LLM) analysis, specifically for extracting callable symbols from code. The class includes a method `from_llm` that utilizes a default LLM analysis function to populate the collection with function symbols, and a `to_dict` method to convert the collection's data into a dictionary format. The class is designed to work with OpenAI's language models to analyze and extract function-related symbols from code.
- **Inherits From**:
    - RawSymbolCollection

**Methods**

---
#### DefaultFnRawSymbolCollection.from_llm
The `from_llm` function initializes a class instance by performing a default LLM analysis to extract callable symbols from the provided code.
- **Inputs**:
    - `cls`: The class type that will be instantiated, expected to be a subclass of `RawSymbolCollection`.
    - `llm`: An instance of `ChatOpenAI` used for language model processing.
    - `code`: A string containing the source code to be analyzed.
    - `root_rel_path`: A string representing the root relative path of the source code file.
- **Control Flow**:
    - The function calls `default_llm_analysis` with the provided class type, LLM instance, code, root relative path, and specific prompts for function checking.
    - The `default_llm_analysis` function processes the code to identify callable symbols using the LLM and returns a collection of these symbols.
    - The result of `default_llm_analysis` is returned, which is either an instance of the class type with the extracted symbols or `None` if no symbols are found.
- **Output**:
    - The function returns an instance of the specified class type containing the extracted callable symbols, or `None` if no symbols are found.


---
#### DefaultFnRawSymbolCollection.from_static_analysis
The `from_static_analysis` function is a class method placeholder that raises a NotImplementedError, indicating that the default behavior should use the `from_llm` method instead.
- **Inputs**:
    - `code`: A string representing the source code to be analyzed.
    - `root_rel_path`: A Path object representing the root relative path of the source code file.
- **Control Flow**:
    - The function immediately raises a NotImplementedError with a specific message.
- **Output**:
    - The function does not return any output as it raises an exception.


---
#### DefaultFnRawSymbolCollection.to_dict
The `to_dict` function returns the `data` attribute of the class instance as a dictionary.
- **Inputs**:
    - None
- **Control Flow**:
    - The function directly returns the `data` attribute of the class instance.
- **Output**:
    - A dictionary where the keys are strings and the values are `RawSymbolData` objects.



---
### DefaultVariableCollection 
- **Type**: `class`
- **Members**:
    - `data`: A dictionary mapping strings to either a DefaultVariableData instance or a list of DefaultVariableData instances.
- **Description**: The `DefaultVariableCollection` class is a specialized collection class that inherits from `IrCollection`. It is designed to manage a collection of `DefaultVariableData` objects, which can be either individual instances or lists of such instances, indexed by string keys. The class provides a class method `from_llm` that facilitates the creation of a `DefaultVariableCollection` instance using data derived from a language model (LLM) and a collection of raw symbols. This method leverages the `from_llm_with_ir_data` method to populate the collection with the appropriate data.
- **Inherits From**:
    - IrCollection

**Methods**

---
#### DefaultVariableCollection.from_llm
The `from_llm` function creates an instance of the class by invoking the `from_llm_with_ir_data` method with default variable data, a language model, and a collection of symbols.
- **Inputs**:
    - `llm`: An instance of the ChatOpenAI class, representing a language model used for processing.
    - `symbols_list`: An instance of RawSymbolCollection, representing a collection of symbols to be used in the process.
- **Control Flow**:
    - The function calls the `from_llm_with_ir_data` method on the class `cls` with `DefaultVariableData`, `llm`, and `symbols_list` as arguments.
    - The result of the `from_llm_with_ir_data` method call is returned as the output of the function.
- **Output**:
    - The function returns an instance of the class `cls` created using the `from_llm_with_ir_data` method.



---
### DefaultVariableData 
- **Type**: `class`
- **Members**:
    - `system_prompt`: Returns a system prompt string for variable documentation.
    - `user_prompt`: Generates a user prompt string using a given symbol's name and code.
    - `child_to_ir`: Raises NotImplementedError as default variables should not have children.
    - `child_to_field_name`: Raises NotImplementedError as default variables should not have children.
- **Description**: The `DefaultVariableData` class is a specialized subclass of `VariableData` designed to handle default variable documentation prompts and interactions. It provides class methods to generate system and user prompts for documenting variables, specifically using a given symbol's data. The class also includes methods for converting child symbols to intermediate representations (IR) and field names, but these raise `NotImplementedError` as default variables are not expected to have children. This class is part of a larger framework for managing and documenting code symbols using language models.
- **Inherits From**:
    - VariableData

**Methods**

---
#### DefaultVariableData.child_to_field_name
The function `child_to_field_name` raises a `NotImplementedError` indicating that default variables should not have children.
- **Inputs**:
    - `cls`: The class to which this method belongs.
    - `child`: An instance of `RawSymbolData` representing a child symbol.
- **Control Flow**:
    - The function immediately raises a `NotImplementedError` with a specific message.
- **Output**:
    - The function does not return any value as it raises an exception.


---
#### DefaultVariableData.child_to_ir
The `child_to_ir` function raises a `NotImplementedError` indicating that default variables should not have children.
- **Inputs**:
    - `cls`: The class type from which the method is called.
    - `symbol`: An instance of `RawSymbolData` representing the symbol data to be processed.
- **Control Flow**:
    - The function immediately raises a `NotImplementedError` with a specific message.
- **Output**:
    - The function does not return any value as it raises an exception.


---
#### DefaultVariableData.system_prompt
The `system_prompt` function returns a predefined JSON string for documenting variables.
- **Inputs**:
    - None
- **Control Flow**:
    - The function directly returns the constant `VARIABLES_FOUND_SYSTEM_PROMPT_JSON`.
- **Output**:
    - The function outputs a string containing a JSON schema for documenting variables.


---
#### DefaultVariableData.user_prompt
The `user_prompt` function generates a formatted string prompt using a symbol's name and code.
- **Inputs**:
    - `cls`: The class reference, typically used in class methods.
    - `symbol`: An instance of RawSymbolData containing the symbol's name and file code.
- **Control Flow**:
    - The function constructs a string by concatenating a predefined prompt with the symbol's name and its associated code.
- **Output**:
    - A formatted string that includes the symbol's name and its code, prefixed by a user prompt message.



---
### DefaultVariableRawSymbolCollection 
- **Type**: `class`
- **Members**:
    - `data`: A dictionary mapping string keys to RawSymbolData objects.
- **Description**: The `DefaultVariableRawSymbolCollection` class is a specialized collection for handling raw symbol data related to variables. It inherits from `RawSymbolCollection` and provides methods to create instances from language model (LLM) analysis, specifically for variable symbols. The class includes a `from_llm` class method that utilizes a default LLM analysis function to populate the collection with variable symbols extracted from code. Additionally, it provides a `to_dict` method to convert the collection's data into a dictionary format.
- **Inherits From**:
    - RawSymbolCollection

**Methods**

---
#### DefaultVariableRawSymbolCollection.from_llm
The `from_llm` function creates an instance of a class by performing a default LLM analysis on the provided code to extract symbols of a specified kind.
- **Inputs**:
    - `llm`: An instance of the `ChatOpenAI` class used to interact with the language model.
    - `code`: A string containing the source code to be analyzed.
    - `root_rel_path`: A string representing the root relative path of the code file being analyzed.
- **Control Flow**:
    - The function calls `default_llm_analysis` with the provided class, LLM instance, code, root relative path, a system prompt specific to the type of symbols being extracted, an empty user prompt, and a symbol kind indicating the type of symbols to extract.
    - The `default_llm_analysis` function processes the code to determine if it requires multiple prompts and splits the code into chunks if necessary.
    - It then uses either `_default_checker` or `_default_checker_multi_prompt` to extract symbols from the code, depending on whether the code was split into chunks.
    - The extracted symbols are used to create raw symbol data, which is then used to instantiate the specified collection class.
    - The function returns an instance of the collection class containing the extracted symbols, or `None` if no symbols were found.
- **Output**:
    - An instance of the specified collection class containing the extracted symbols, or `None` if no symbols were found.


---
#### DefaultVariableRawSymbolCollection.from_static_analysis
The `from_static_analysis` function is a placeholder method intended to be overridden, which raises a `NotImplementedError` indicating that the default case should use the `from_llm` method instead.
- **Inputs**:
    - `cls`: The class on which this method is called, typically a subclass of `RawSymbolCollection`.
    - `code`: A string representing the source code to be analyzed.
    - `root_rel_path`: A `Path` object representing the root relative path of the source code file.
- **Control Flow**:
    - The function immediately raises a `NotImplementedError` with a specific message.
- **Output**:
    - The function does not return any output as it raises an exception.


---
#### DefaultVariableRawSymbolCollection.to_dict
The `to_dict` function returns the `data` attribute of the class instance as a dictionary.
- **Inputs**:
    - None
- **Control Flow**:
    - The function directly returns the `data` attribute of the class instance.
- **Output**:
    - A dictionary where the keys are strings and the values are `RawSymbolData` objects.



# Functions

---
### _default_checker 
The `_default_checker` function attempts to generate a list of data from a language model and returns it in different formats based on the input parameters.
- **Inputs**:
    - `llm`: An instance of the ChatOpenAI class, representing the language model to be used.
    - `user_prompt`: A string containing the user prompt to be used in the language model query.
    - `system_prompt`: A string containing the system prompt to be used in the language model query.
    - `code`: A string containing the code to be analyzed by the language model.
    - `as_list_data_ds`: A boolean flag indicating whether to return the result as a ListData object or a list of strings.
- **Control Flow**:
    - Attempt to create a ListData object using the `from_llm` method with the provided language model, prompts, and code.
    - If a LengthFinishReasonError is raised, catch the exception and initialize an empty ListData object.
    - Check if the ListData object contains any data.
    - If data is present and `as_list_data_ds` is True, return the ListData object; otherwise, return the data as a list of strings.
    - If no data is present, return None.
- **Output**:
    - The function returns a list of strings, a ListData object, or None, depending on the presence of data and the `as_list_data_ds` flag.


---
### _default_checker_multi_prompt 
The function `_default_checker_multi_prompt` processes multiple code chunks using a language model to identify and deduplicate entities across overlapping code segments.
- **Inputs**:
    - `llm`: An instance of `ChatOpenAI` used to process the code chunks.
    - `code_chunks`: A list of strings, each representing a chunk of code to be processed.
    - `system_prompt`: A string containing the system prompt to guide the language model's processing.
    - `user_prompt`: A string containing the user prompt to guide the language model's processing.
- **Control Flow**:
    - Initialize an empty list `checker_responses` to store results.
    - Iterate over each `code_chunk` in `code_chunks` with its index `idx`.
    - For each `code_chunk`, call `_default_checker` with the provided prompts and code chunk.
    - If `_default_checker` returns non-None data, append a list containing the index and response data to `checker_responses`.
    - If `checker_responses` is not empty, iterate over the list to remove duplicate entities between overlapping chunks.
    - Return `checker_responses` if it contains any data, otherwise return `None`.
- **Output**:
    - The function returns a list of lists, each containing an index and a list of strings representing deduplicated entities, or `None` if no entities are found.


---
### default_imports_checker 
The `default_imports_checker` function checks for imports and dependencies in a given code string using a language model.
- **Inputs**:
    - `llm`: An instance of the `ChatOpenAI` class, representing the language model to be used for analysis.
    - `code`: A string containing the source code to be analyzed for imports and dependencies.
    - `root_rel_path`: A string representing the root relative path of the code file, though it is not used in this function.
- **Control Flow**:
    - The function calls the `_default_checker` function with the provided `llm`, an empty `user_prompt`, the `IMPORTS_SYSTEM_PROMPT_JSON` as the `system_prompt`, the `code`, and `as_list_data_ds` set to `True`.
- **Output**:
    - The function returns a `ListData` object containing the imports and dependencies found in the code, or `None` if no imports are found.


---
### default_llm_analysis 
The `default_llm_analysis` function analyzes code to extract symbols using a language model and returns a collection of these symbols.
- **Inputs**:
    - `collection_cls`: A class type that extends RawSymbolCollection, used to instantiate the output collection.
    - `llm`: An instance of ChatOpenAI, representing the language model used for analysis.
    - `code`: A string containing the source code to be analyzed.
    - `root_rel_path`: A string representing the root relative path of the code file.
    - `system_prompt`: A string containing the system prompt for the language model.
    - `user_prompt`: A string containing the user prompt for the language model.
    - `symbol_kind`: An instance of SymbolKind, indicating the type of symbols to extract (e.g., functions, variables).
- **Control Flow**:
    - Check if the code requires multi-prompt analysis using `code_requires_multi_prompt` function.
    - If multi-prompt is required, split the code into chunks using `split_text` and analyze each chunk with `_default_checker_multi_prompt`.
    - For each chunk, extract symbols and create raw symbol data using `create_raw_symbol_via_llm`.
    - If multi-prompt is not required, analyze the entire code using `_default_checker` and extract symbols.
    - Create raw symbol data for each symbol found in the code.
    - Return a collection of raw symbol data using `collection_cls` if any symbols are found, otherwise return None.
- **Output**:
    - The function returns an instance of RawSymbolCollection containing the extracted symbols, or None if no symbols are found.


