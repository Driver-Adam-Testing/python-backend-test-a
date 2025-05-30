# Purpose
This Python source code file is designed to facilitate the extraction and documentation of symbols from C and C++ header files. It provides a structured approach to analyze and document various components such as data structures, functions, and variables found within these header files. The file defines several classes that extend from base classes like `RawSymbolCollection`, `ClassData`, `FnData`, and `VariableData`, each tailored to handle specific types of symbols. The primary functionality revolves around using `ctags` for static analysis to extract symbols and then organizing these symbols into collections for further processing and documentation.

The code is organized into several classes, each responsible for handling different types of symbols: `HeaderDataStructureRawSymbolCollection`, `HeaderFnRawSymbolCollection`, and `HeaderVariableRawSymbolCollection` for raw symbol extraction, and `HeaderDataStructureData`, `HeaderFnData`, and `HeaderVariableData` for processing and documentation. These classes utilize prompts to generate detailed documentation for each symbol type, leveraging the `ChatOpenAI` model for natural language processing. The file is intended to be part of a larger system that automates the documentation of C and C++ header files, providing a clear and structured API for symbol extraction and documentation generation.
# Imports and Dependencies

---
- `pathlib`
- `typing`
- `utils.codemap_ctags`
- `utils.models`
- `ir_common`
- `symbol_common`


# Global Variables

---
### C_OR_CPP_HEADER_DATA_STRUCTURES 
- **Type**: `set`
- **Description**: `C_OR_CPP_HEADER_DATA_STRUCTURES` is a set containing strings that represent different types of data structures commonly found in C or C++ header files. These include 'enum', 'union', 'struct', 'class', and 'typedef', which are fundamental constructs used to define data types and organize code in C/C++ programming.
- **Use**: This variable is used to identify and categorize data structures when analyzing C or C++ header files.


---
### C_OR_CPP_HEADER_FUNCTIONS 
- **Type**: `set`
- **Description**: The variable `C_OR_CPP_HEADER_FUNCTIONS` is a set containing a single string element, 'function'. This set is used to categorize or identify symbols in C or C++ header files that are of the 'function' kind.
- **Use**: This variable is used to filter or identify function symbols when analyzing C or C++ header files.


---
### C_OR_CPP_HEADER_MACROS 
- **Type**: `set`
- **Description**: `C_OR_CPP_HEADER_MACROS` is a set containing the string 'macro'. This set is used to categorize or identify macro elements in C or C++ header files.
- **Use**: This variable is used to identify macro elements in C or C++ header files.


---
### C_OR_CPP_HEADER_VARIABLES 
- **Type**: `set`
- **Description**: `C_OR_CPP_HEADER_VARIABLES` is a set containing strings that represent different kinds of variables that can be found in C or C++ header files. Specifically, it includes 'variable' and 'externvar', which denote regular variables and external variables, respectively.
- **Use**: This set is used to categorize and identify variable symbols in C or C++ header files during static analysis.


---
### DATA_STRUCTURES_FOUND_SYSTEM_PROMPT_JSON 
- **Type**: `string`
- **Description**: The variable `DATA_STRUCTURES_FOUND_SYSTEM_PROMPT_JSON` is a string containing a system prompt template for documenting data structures in C and C++ code, particularly header files. It provides a JSON schema that outlines how to describe data structures, including their type, members, description, and inheritance. This prompt is intended for use by systems programmers and documentation experts to ensure consistent and detailed documentation of data structures.
- **Use**: This variable is used as a template for generating system prompts to document data structures in C and C++ header files.


---
### DATA_STRUCTURES_FOUND_USER_PROMPT 
- **Type**: `str`
- **Description**: The variable `DATA_STRUCTURES_FOUND_USER_PROMPT` is a string that contains a template prompt for summarizing data structures in provided code. It is designed to guide the user in describing data structures such as structs, classes, or enums, focusing on their complexity and importance.
- **Use**: This variable is used to provide a consistent prompt format for users to document data structures in code.


---
### FUNCTIONS_FOUND_SYSTEM_PROMPT_JSON 
- **Type**: `str`
- **Description**: The `FUNCTIONS_FOUND_SYSTEM_PROMPT_JSON` is a string variable that contains a JSON schema template. This template is used to guide the documentation process for functions and class methods in C and C++ code, especially header files. It specifies the format and content required for documenting functions, including a single sentence description, inputs, control flow, and output.
- **Use**: This variable is used as a template to ensure consistent and comprehensive documentation of functions and methods in C and C++ header files.


---
### FUNCTIONS_FOUND_USER_PROMPT 
- **Type**: `str`
- **Description**: `FUNCTIONS_FOUND_USER_PROMPT` is a string variable that contains a template for a user prompt. This prompt is used to instruct a user to summarize a function or method in the provided code, focusing on inputs, control flow, logic, and output. The prompt emphasizes providing detail that matches the complexity of the function.
- **Use**: This variable is used to generate user prompts for documenting functions or methods in C and C++ code.


---
### SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT 
- **Type**: `str`
- **Description**: `SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT` is a string variable that contains a detailed prompt for explaining the purpose of a large C or C++ header file. The prompt guides the user to write a comprehensive explanation of the header file's purpose, focusing on its functionality, technical components, and whether it defines public APIs or external interfaces.
- **Use**: This variable is used to provide a template for generating detailed documentation of large C or C++ header files.


---
### SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_C_OR_CPP_HEADER 
- **Type**: `string`
- **Description**: The variable `SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_C_OR_CPP_HEADER` is a string that contains a detailed prompt for a system designed to generate documentation for C and C++ header files. It emphasizes the expertise required in both programming and documentation to explain technical details and the purpose of software effectively.
- **Use**: This variable is used as a prompt to guide the generation of detailed documentation for large C and C++ header files.


---
### SOURCE_CODE_SMALL_PURPOSE_USER_PROMPT 
- **Type**: `str`
- **Description**: This variable is a string that contains a prompt for users to explain the purpose of a small C or C++ header file. It is designed to guide users in writing a concise paragraph that captures the essence of the header file's purpose.
- **Use**: This variable is used to provide a template for users to describe the purpose of small header files in a clear and concise manner.


---
### SOURCE_CODE_SMALL_SYSTEM_PROMPT_GENERAL_C_OR_CPP_HEADER 
- **Type**: `str`
- **Description**: This variable is a string that contains a system prompt for a small and simple C or C++ header file documentation task. It is designed to guide the user in writing concise and clear documentation for small source code files.
- **Use**: This variable is used to provide a template or guideline for generating documentation for small C or C++ header files.


---
### VARIABLES_FOUND_SYSTEM_PROMPT_JSON 
- **Type**: `str`
- **Description**: `VARIABLES_FOUND_SYSTEM_PROMPT_JSON` is a string variable that contains a JSON schema template. This template is used for documenting variables in C and C++ header files, focusing on explaining technical details and the purpose of software components.
- **Use**: This variable is used to provide a structured format for documenting variables in C and C++ header files.


---
### VARIABLES_FOUND_USER_PROMPT 
- **Type**: `str`
- **Description**: `VARIABLES_FOUND_USER_PROMPT` is a string variable that contains a prompt template for summarizing a variable in a given code. It provides instructions for describing global variables, emphasizing the need for detail proportional to the complexity of the variable.
- **Use**: This variable is used to guide users in documenting global variables in code.


# Classes

---
### HeaderDataStructureCollection 
- **Type**: `class`
- **Members**:
    - `data`: A dictionary mapping strings to either HeaderDataStructureData or a list of HeaderDataStructureData.
- **Description**: The `HeaderDataStructureCollection` class is a specialized collection class that inherits from `IrCollection`. It is designed to manage a collection of header data structures, specifically for C or C++ header files. The class contains a class method `from_llm` which facilitates the creation of an instance from a language model and a list of raw symbols, leveraging the `HeaderDataStructureData` class to process the data. This class is part of a system that analyzes and documents C and C++ header files, focusing on data structures.
- **Inherits From**:
    - IrCollection

**Methods**

---
#### HeaderDataStructureCollection.from_llm
The `from_llm` function creates an instance of the class using data from a language model and a collection of symbols.
- **Inputs**:
    - `llm`: An instance of the ChatOpenAI class, representing the language model to be used.
    - `symbols_list`: An instance of RawSymbolCollection, representing a collection of symbols to be used in the creation of the class instance.
- **Control Flow**:
    - The function calls another class method `from_llm_with_ir_data` with `HeaderDataStructureData`, `llm`, and `symbols_list` as arguments.
    - The `from_llm_with_ir_data` method is responsible for creating and returning an instance of the class.
- **Output**:
    - The function returns an instance of the class it is called on, initialized with data from the language model and the symbols list.



---
### HeaderDataStructureData 
- **Type**: `class`
- **Members**:
    - `system_prompt`: Returns a JSON-formatted system prompt for documenting data structures.
    - `user_prompt`: Generates a user prompt string for a given symbol, including its name and code.
    - `child_to_ir`: Maps a symbol to its corresponding intermediate representation (IR) data type or None.
    - `child_to_field_name`: Maps a child symbol to its corresponding field name, such as 'Methods' or 'Nested Classes'.
- **Description**: The `HeaderDataStructureData` class is designed to facilitate the documentation of data structures found in C and C++ header files. It provides class methods to generate system and user prompts for documenting these data structures, and it includes logic to map symbols to their corresponding intermediate representation (IR) data types or field names. This class inherits from `ClassData` and is part of a larger framework for analyzing and documenting code structures.
- **Inherits From**:
    - ClassData

**Methods**

---
#### HeaderDataStructureData.child_to_field_name
The function `child_to_field_name` maps a `RawSymbolData` object's `symbol_kind` to a corresponding field name string.
- **Inputs**:
    - `cls`: The class reference, typically used in class methods.
    - `child`: An instance of `RawSymbolData` representing a symbol with a specific kind.
- **Control Flow**:
    - A dictionary `mapping` is defined to map `SymbolKind` values to field name strings.
    - The function returns the field name string corresponding to the `symbol_kind` of the `child` using the `mapping` dictionary.
- **Output**:
    - A string representing the field name corresponding to the `symbol_kind` of the `child`, or `None` if no mapping is found.


---
#### HeaderDataStructureData.child_to_ir
The `child_to_ir` function maps a `RawSymbolData` instance to a corresponding `IrData` type based on the symbol kind.
- **Inputs**:
    - `cls`: The class reference, typically used when defining class methods.
    - `symbol`: An instance of `RawSymbolData` representing a symbol with a specific kind.
- **Control Flow**:
    - A dictionary `mapping` is defined to associate `SymbolKind` values with corresponding `IrData` types.
    - The function attempts to retrieve the `IrData` type from the `mapping` dictionary using the `symbol.symbol_kind` as the key.
    - If the `symbol_kind` is `SymbolKind.CALLABLE`, it returns `HeaderFnData`.
    - If the `symbol_kind` is `SymbolKind.DATA_STRUCTURE`, it returns `None`.
- **Output**:
    - The function returns a type of `IrData` or `None` based on the `symbol_kind` of the input `symbol`.


---
#### HeaderDataStructureData.system_prompt
The `system_prompt` function returns a predefined JSON string that serves as a system prompt for documenting data structures in C and C++ code.
- **Inputs**:
    - None
- **Control Flow**:
    - The function directly returns the constant `DATA_STRUCTURES_FOUND_SYSTEM_PROMPT_JSON`.
- **Output**:
    - A string containing a JSON schema for documenting data structures in C and C++ code.


---
#### HeaderDataStructureData.user_prompt
The `user_prompt` function generates a formatted string prompt for documenting a data structure using its name and code, optionally including the full file code if available.
- **Inputs**:
    - `cls`: The class reference, typically used in class methods, but not utilized in this function.
    - `symbol`: An instance of `RawSymbolData` containing the name, symbol code, and optionally the full file code of a data structure.
- **Control Flow**:
    - Initialize `user_prompt` with a formatted string containing a predefined prompt, the data structure's name, and its symbol code.
    - Check if `symbol.file_code` is present; if so, append the full file code to `user_prompt`.
    - Return the constructed `user_prompt` string.
- **Output**:
    - A formatted string that serves as a prompt for documenting a data structure, including its name, symbol code, and optionally the full file code.



---
### HeaderDataStructureRawSymbolCollection 
- **Type**: `class`
- **Members**:
    - `data`: A dictionary mapping symbol names to RawSymbolData or lists of RawSymbolData.
- **Description**: The `HeaderDataStructureRawSymbolCollection` class is a specialized collection for handling raw symbol data extracted from C or C++ header files, specifically focusing on data structures. It inherits from `RawSymbolCollection` and provides methods to populate its data from static analysis of code using ctags. The class processes symbols to identify and categorize data structures and their associated methods, handling cases like overloaded methods and nested classes. It also includes a method to convert its data into a dictionary format.
- **Inherits From**:
    - RawSymbolCollection

**Methods**

---
#### HeaderDataStructureRawSymbolCollection.from_llm
The `from_llm` method raises a NotImplementedError indicating that static analysis should be used for header functions.
- **Inputs**:
    - `code`: A string representing the code to be analyzed.
    - `root_rel_path`: A string representing the root relative path where the code is located.
- **Control Flow**:
    - The function immediately raises a NotImplementedError with a specific message.
- **Output**:
    - The function does not return any output as it raises an exception.


---
#### HeaderDataStructureRawSymbolCollection.from_static_analysis
The `from_static_analysis` function analyzes C or C++ header code to extract and organize symbol data into a structured format using ctags.
- **Inputs**:
    - `code`: A string containing the source code of a C or C++ header file to be analyzed.
    - `root_rel_path`: A Path object representing the relative path to the root directory of the source code.
- **Control Flow**:
    - Determine if the code requires multi-prompt processing using `code_requires_multi_prompt` function.
    - Extract symbols from the code using `extract_symbols_w_ctags` function.
    - Initialize dictionaries for global method counts and raw symbol data for classes.
    - Iterate over each symbol to count global methods and create raw symbol data for data structures, excluding anonymous ones.
    - For each symbol, check if it is a method within a class and update the class's raw symbol data with method information, handling overloaded methods.
    - Check for nested data structures and update the parent class's raw symbol data with nested class information.
    - Print the collected class raw symbol data for debugging purposes.
    - Return an instance of the class with the collected data if any symbols were found, otherwise return None.
- **Output**:
    - An instance of the class containing the structured symbol data if symbols are found, otherwise None.


---
#### HeaderDataStructureRawSymbolCollection.to_dict
The `to_dict` function returns the `data` attribute of the class instance as a dictionary.
- **Inputs**:
    - None
- **Control Flow**:
    - The function directly returns the `data` attribute of the class instance without any additional processing.
- **Output**:
    - A dictionary where the keys are strings and the values are `RawSymbolData` objects.



---
### HeaderFnCollection 
- **Type**: `class`
- **Members**:
    - `data`: A dictionary mapping strings to either a HeaderFnData instance or a list of HeaderFnData instances.
- **Description**: The `HeaderFnCollection` class is a specialized collection class that inherits from `IrCollection`. It is designed to manage a collection of header function data, specifically `HeaderFnData` objects, which represent functions extracted from C or C++ header files. The class provides a class method `from_llm` to create an instance of `HeaderFnCollection` using a language model (`llm`) and a list of raw symbols (`symbols_list`). This method utilizes the `from_llm_with_ir_data` method to populate the collection with `HeaderFnData` instances.
- **Inherits From**:
    - IrCollection

**Methods**

---
#### HeaderFnCollection.from_llm
The `from_llm` function creates an instance of the class using LLM data and a list of symbols by calling another class method `from_llm_with_ir_data`.
- **Inputs**:
    - `llm`: An instance of the `ChatOpenAI` class, representing a language model.
    - `symbols_list`: An instance of `RawSymbolCollection`, representing a collection of raw symbols.
- **Control Flow**:
    - The function calls the `from_llm_with_ir_data` method of the class, passing `HeaderFnData`, `llm`, and `symbols_list` as arguments.
    - The result of the `from_llm_with_ir_data` method call is returned.
- **Output**:
    - The function returns an instance of the class it is called on, initialized with data from the LLM and the symbols list.



---
### HeaderFnData 
- **Type**: `class`
- **Members**:
    - `system_prompt`: Returns a JSON-formatted system prompt for documenting functions.
    - `user_prompt`: Generates a user prompt string for a given symbol, including its code and file code if available.
    - `child_to_ir`: Raises NotImplementedError as functions should not have children.
    - `child_to_field_name`: Raises NotImplementedError as functions should not have children.
- **Description**: The `HeaderFnData` class is a specialized subclass of `FnData` designed to handle the documentation of functions found in C and C++ header files. It provides class methods to generate system and user prompts for documenting these functions, utilizing predefined JSON schemas. The class explicitly does not support child elements, as indicated by the `NotImplementedError` raised in methods related to child processing.
- **Inherits From**:
    - FnData

**Methods**

---
#### HeaderFnData.child_to_field_name
The function `child_to_field_name` raises a `NotImplementedError` indicating that functions should not have children.
- **Inputs**:
    - `cls`: The class to which this method belongs.
    - `child`: An instance of `RawSymbolData` representing a child symbol.
- **Control Flow**:
    - The function immediately raises a `NotImplementedError` with the message 'Functions should not have children'.
- **Output**:
    - The function does not return any value as it raises an exception.


---
#### HeaderFnData.child_to_ir
The `child_to_ir` function raises a `NotImplementedError` indicating that functions should not have children.
- **Inputs**:
    - `cls`: The class type from which the method is called.
    - `symbol`: An instance of `RawSymbolData` representing the symbol data to be processed.
- **Control Flow**:
    - The function immediately raises a `NotImplementedError` with a specific message.
- **Output**:
    - The function does not return any value as it raises an exception.


---
#### HeaderFnData.system_prompt
The `system_prompt` function returns a predefined JSON string used as a system prompt for documenting functions and class methods in C and C++ code.
- **Inputs**:
    - None
- **Control Flow**:
    - The function directly returns the constant `FUNCTIONS_FOUND_SYSTEM_PROMPT_JSON`.
- **Output**:
    - A string containing a JSON schema for documenting functions and class methods.


---
#### HeaderFnData.user_prompt
The `user_prompt` function generates a formatted string containing a user prompt with function details from a given `RawSymbolData` object.
- **Inputs**:
    - `cls`: The class reference, typically used in class methods.
    - `symbol`: An instance of `RawSymbolData` containing information about a symbol, including its name, symbol code, and optionally, file code.
- **Control Flow**:
    - Initialize a string `user_prompt` with a formatted message containing the function name and its code from the `symbol` object.
    - Check if the `symbol` object has `file_code` data.
    - If `file_code` is present, append the full file code to the `user_prompt` string.
- **Output**:
    - A formatted string that includes the function name, its code, and optionally, the full file code if available.



---
### HeaderFnRawSymbolCollection 
- **Type**: `class`
- **Members**:
    - `data`: A dictionary mapping function names to RawSymbolData or lists of RawSymbolData.
- **Description**: The `HeaderFnRawSymbolCollection` class is designed to collect and manage raw symbol data specifically for functions found in C or C++ header files. It inherits from `RawSymbolCollection` and provides methods to extract function symbols using static analysis. The class processes symbols to identify functions, considering their scope and whether they are overloaded, and stores this information in a structured format. It also includes a method to convert the collected data into a dictionary format, although it does not implement functionality for LLM-based symbol extraction.
- **Inherits From**:
    - RawSymbolCollection

**Methods**

---
#### HeaderFnRawSymbolCollection.from_llm
The `from_llm` function is a class method that raises a NotImplementedError, indicating that static analysis should be used instead of LLM for header functions.
- **Inputs**:
    - `code`: A string representing the code to be analyzed.
    - `root_rel_path`: A string representing the root relative path of the code file.
- **Control Flow**:
    - The function immediately raises a NotImplementedError with a specific message.
- **Output**:
    - The function does not return any output as it raises an exception.


---
#### HeaderFnRawSymbolCollection.from_static_analysis
The `from_static_analysis` function extracts and processes function symbols from C or C++ header code using static analysis and returns a collection of raw symbol data.
- **Inputs**:
    - `code`: A string containing the source code of a C or C++ header file to be analyzed.
    - `root_rel_path`: A `Path` object representing the relative path to the root directory of the source code file.
- **Control Flow**:
    - Determine if the code requires multi-prompt processing using `code_requires_multi_prompt` function.
    - Extract symbols from the code using `extract_symbols_w_ctags` function.
    - Create a list of all function names from the extracted symbols that are not anonymous and are of kind 'function'.
    - Initialize an empty dictionary `fn_raw_symbol_data` to store raw symbol data for functions.
    - Iterate over each symbol in the extracted symbols.
    - For each symbol, check if it is a function and not anonymous.
    - Determine if the function is contained within a class or data structure by checking its scope and scope kind.
    - Construct the function name, considering its scope if it is part of a data structure.
    - If the function is not contained in a class and is unique, add its raw symbol data to `fn_raw_symbol_data` with `is_overloaded` set to `False`.
    - If the function is not contained in a class and is overloaded, add its raw symbol data to `fn_raw_symbol_data` with `is_overloaded` set to `True`.
    - Return `None` if no function symbols were found, otherwise return an instance of the class with the collected raw symbol data.
- **Output**:
    - Returns an instance of the class containing the raw symbol data for functions if any are found, otherwise returns `None`.


---
#### HeaderFnRawSymbolCollection.to_dict
The `to_dict` function returns the `data` attribute of the class instance as a dictionary.
- **Inputs**:
    - None
- **Control Flow**:
    - The function directly returns the `data` attribute of the class instance without any additional processing.
- **Output**:
    - A dictionary where the keys are strings and the values are `RawSymbolData` objects.



---
### HeaderVariableCollection 
- **Type**: `class`
- **Members**:
    - `data`: A dictionary mapping strings to either a HeaderVariableData instance or a list of HeaderVariableData instances.
- **Description**: The `HeaderVariableCollection` class is a specialized collection class that inherits from `IrCollection`. It is designed to manage a collection of header variable data, specifically for C or C++ header files. The class contains a class method `from_llm` which facilitates the creation of a `HeaderVariableCollection` instance using data from a language model and a list of raw symbols. This class is part of a system that processes and documents code symbols extracted from header files, focusing on variables.
- **Inherits From**:
    - IrCollection

**Methods**

---
#### HeaderVariableCollection.from_llm
The `from_llm` function creates an instance of the class using LLM data and a collection of raw symbols.
- **Inputs**:
    - `llm`: An instance of the `ChatOpenAI` class, representing the language model to be used.
    - `symbols_list`: An instance of `RawSymbolCollection`, representing a collection of raw symbols to be processed.
- **Control Flow**:
    - The function calls `cls.from_llm_with_ir_data` with `HeaderVariableData`, `llm`, and `symbols_list` as arguments.
    - The function returns the result of the `cls.from_llm_with_ir_data` call.
- **Output**:
    - An instance of the class from which the method is called, initialized with data from the LLM and the raw symbol collection.



---
### HeaderVariableData 
- **Type**: `class`
- **Members**:
    - `system_prompt`: Returns a system prompt string for variables found.
    - `user_prompt`: Generates a user prompt string based on the provided symbol data.
    - `child_to_ir`: Raises NotImplementedError as variables should not have children.
    - `child_to_field_name`: Raises NotImplementedError as variables should not have children.
- **Description**: The `HeaderVariableData` class is a specialized subclass of `VariableData` designed to handle variable-related data in the context of C and C++ header files. It provides class methods to generate system and user prompts for documenting variables, ensuring that the documentation process is consistent and follows a predefined format. The class explicitly does not support child elements, as indicated by the `NotImplementedError` raised in methods related to child processing, reflecting the nature of variables as non-hierarchical elements in this context.
- **Inherits From**:
    - VariableData

**Methods**

---
#### HeaderVariableData.child_to_field_name
The `child_to_field_name` function raises a `NotImplementedError` indicating that variables should not have children.
- **Inputs**:
    - `child`: An instance of `RawSymbolData` representing a child symbol.
- **Control Flow**:
    - The function immediately raises a `NotImplementedError` with a specific message.
- **Output**:
    - The function does not return any output as it raises an exception.


---
#### HeaderVariableData.child_to_ir
The `child_to_ir` function raises a NotImplementedError indicating that variables should not have children.
- **Inputs**:
    - `cls`: The class from which the method is called, typically a class method.
    - `symbol`: An instance of RawSymbolData representing a symbol in the code.
- **Control Flow**:
    - The function immediately raises a NotImplementedError with a specific message.
- **Output**:
    - The function does not return any value as it raises an exception.


---
#### HeaderVariableData.system_prompt
The `system_prompt` function returns a predefined JSON string for documenting variables in C and C++ code.
- **Inputs**:
    - None
- **Control Flow**:
    - The function directly returns the constant `VARIABLES_FOUND_SYSTEM_PROMPT_JSON`.
- **Output**:
    - A string containing a JSON schema for documenting variables in C and C++ code.


---
#### HeaderVariableData.user_prompt
The `user_prompt` function generates a formatted string prompt based on the provided symbol's name and code, optionally including the full file code if available.
- **Inputs**:
    - `cls`: The class reference, typically used in class methods, but not utilized in this function.
    - `symbol`: An instance of `RawSymbolData` containing the name, symbol code, and optionally the full file code of a variable.
- **Control Flow**:
    - Initialize a string `user_prompt` with a formatted message including the variable's name and code from the `symbol` object.
    - Check if the `symbol` object has `file_code` available.
    - If `file_code` is available, append it to the `user_prompt` string with appropriate formatting.
    - Return the constructed `user_prompt` string.
- **Output**:
    - A formatted string that includes the variable's name, symbol code, and optionally the full file code.



---
### HeaderVariableRawSymbolCollection 
- **Type**: `class`
- **Members**:
    - `data`: A dictionary mapping string keys to either a single RawSymbolData or a list of RawSymbolData.
- **Description**: The `HeaderVariableRawSymbolCollection` class is a specialized collection for handling raw symbol data related to variables found in C or C++ header files. It inherits from `RawSymbolCollection` and provides methods for creating instances from static analysis, specifically using ctags to analyze code and extract variable symbols. The class also includes a method to convert its data into a dictionary format. It is designed to work with static analysis tools and does not support creation from language model analysis, as indicated by the `NotImplementedError` in the `from_llm` method.
- **Inherits From**:
    - RawSymbolCollection

**Methods**

---
#### HeaderVariableRawSymbolCollection.from_llm
The `from_llm` method is a class method placeholder that raises a NotImplementedError, indicating that static analysis should be used instead of LLM for header functions.
- **Inputs**:
    - `code`: A string representing the code to be analyzed.
    - `root_rel_path`: A string representing the root relative path of the code file.
- **Control Flow**:
    - The method immediately raises a NotImplementedError with a specific message.
- **Output**:
    - The function does not return any output as it raises an exception.


---
#### HeaderVariableRawSymbolCollection.from_static_analysis
The `from_static_analysis` function performs a static analysis on code to extract variable symbols using ctags and returns a collection of these symbols.
- **Inputs**:
    - `cls`: The class type that will be used to create the collection of symbols.
    - `code`: A string containing the source code to be analyzed.
    - `root_rel_path`: A Path object representing the root relative path of the source code file.
- **Control Flow**:
    - The function calls `default_ctags_analysis` with the provided class type, code, and root relative path.
    - It specifies the symbol kind as `SymbolKind.VARIABLE` to focus on variable symbols.
    - It uses `C_OR_CPP_HEADER_VARIABLES` to define the kinds of ctags symbols to extract, which include 'variable' and 'externvar'.
    - The delimiter is set to '::' and symbol padding is enabled.
    - The result of `default_ctags_analysis` is returned, which is a collection of extracted variable symbols.
- **Output**:
    - The function returns a collection of variable symbols extracted from the code, or None if no symbols are found.


---
#### HeaderVariableRawSymbolCollection.to_dict
The `to_dict` function returns the `data` attribute of the class instance as a dictionary.
- **Inputs**:
    - None
- **Control Flow**:
    - The function directly returns the `data` attribute of the class instance without any additional processing.
- **Output**:
    - A dictionary where the keys are strings and the values are `RawSymbolData` objects.



