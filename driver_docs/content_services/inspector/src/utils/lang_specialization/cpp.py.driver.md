# Purpose
This Python source code file defines a set of classes and constants for analyzing and documenting C++ code, specifically focusing on variables, functions, and data structures. The file provides narrow functionality, primarily aimed at extracting and organizing C++ symbols using ctags, and generating documentation prompts for these symbols. It includes classes like `CppVariableData`, `CppFnData`, and `CppClassData`, which extend base classes to provide specific methods for generating system and user prompts for C++ variables, functions, and classes, respectively. Additionally, the file defines collections such as `CppVariableCollection`, `CppFnCollection`, and `CppClassCollection` to manage groups of these symbols. The code also includes raw symbol collection classes like `CppClassRawSymbolCollection`, which use static analysis to extract symbols from C++ code. Overall, this file is part of a larger system for automated C++ code documentation, leveraging both static analysis and language model interactions.
# Imports and Dependencies

---
- `pathlib`
- `typing`
- `utils.codemap_ctags`
- `utils.models`
- `.ir_common`
- `.symbol_common`


# Global Variables

---
### CPP_DATA_STRUCTURES 
- **Type**: `set`
- **Description**: `CPP_DATA_STRUCTURES` is a set containing strings that represent different C++ data structure types, specifically 'class', 'struct', 'enum', 'union', and 'typedef'. This set is used to categorize and identify these types of data structures in C++ code.
- **Use**: This variable is used to identify and categorize C++ data structures during code analysis or processing.


---
### CPP_FUNCTIONS 
- **Type**: `set`
- **Description**: The `CPP_FUNCTIONS` variable is a set containing strings that represent different kinds of C++ functions. Specifically, it includes the strings 'function' and 'prototype', which are used to categorize C++ functions and their prototypes.
- **Use**: This variable is used to identify and categorize C++ functions and prototypes during code analysis or processing.


---
### CPP_MACROS 
- **Type**: `set`
- **Description**: `CPP_MACROS` is a set containing a single string element, 'macro'. This set is used to categorize or identify C++ macros within the context of the code.
- **Use**: This variable is used to classify or filter C++ symbols that are macros.


---
### CPP_VARIABLES 
- **Type**: `set`
- **Description**: `CPP_VARIABLES` is a set containing strings that represent different types of C++ variables. Specifically, it includes the strings 'variable' and 'externvar', which likely correspond to standard C++ variables and external variables, respectively.
- **Use**: This set is used to categorize or identify C++ variable types during code analysis or processing.


---
### DATA_STRUCTURES_FOUND_SYSTEM_PROMPT_JSON 
- **Type**: `str`
- **Description**: The variable `DATA_STRUCTURES_FOUND_SYSTEM_PROMPT_JSON` is a string containing a system prompt template for documenting C++ data structures. It provides instructions for generating JSON documentation for data structures such as structs, enums, and classes in C++. The prompt emphasizes the use of a specific JSON schema to describe the type, members, description, and inheritance of the data structure.
- **Use**: This variable is used to guide the generation of structured documentation for C++ data structures by providing a template for the expected JSON output.


---
### DATA_STRUCTURES_FOUND_USER_PROMPT 
- **Type**: `str`
- **Description**: The variable `DATA_STRUCTURES_FOUND_USER_PROMPT` is a string that contains a template for a user prompt. This prompt is designed to guide users in summarizing data structures found in a given code file. It provides instructions on how to describe data structures, emphasizing the need for detail proportional to the complexity of the data structure.
- **Use**: This variable is used to generate a user prompt for documenting data structures in code.


---
### DATA_STRUCTURES_NONE_CONTENT 
- **Type**: `string`
- **Description**: The variable `DATA_STRUCTURES_NONE_CONTENT` is a string that contains a message indicating that no custom data structures are defined in a given file. It is used as a placeholder or default message when no data structures are found during analysis.
- **Use**: This variable is used to signal the absence of custom data structures in a file.


---
### FUNCTIONS_FOUND_SYSTEM_PROMPT_JSON 
- **Type**: `str`
- **Description**: The `FUNCTIONS_FOUND_SYSTEM_PROMPT_JSON` is a string variable that contains a JSON schema template for documenting functions and class methods in C++ code. It provides a structured format for describing the function's purpose, inputs, control flow, and output.
- **Use**: This variable is used to guide the documentation process for functions in C++ by providing a consistent schema.


---
### FUNCTIONS_FOUND_USER_PROMPT 
- **Type**: `str`
- **Description**: The variable `FUNCTIONS_FOUND_USER_PROMPT` is a string that contains a template for a user prompt. This prompt is designed to guide the user in summarizing a function or method in a given C++ code. It provides instructions on how to describe the inputs, control flow, logic, and output of the function.
- **Use**: This variable is used to generate a user prompt for summarizing functions in C++ code.


---
### FUNCTIONS_NONE_CONTENT 
- **Type**: `str`
- **Description**: `FUNCTIONS_NONE_CONTENT` is a string variable that holds a message indicating that no functions or function prototypes are defined in a given file. This message is used as a placeholder or default response when no functions are detected during the analysis of a C++ source file.
- **Use**: This variable is used to provide a default message when no functions are found in a C++ file.


---
### SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT 
- **Type**: `str`
- **Description**: `SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT` is a string variable that contains a detailed prompt template for explaining the purpose of a large source code file. It guides the user to consider various aspects of the code, such as its functionality, technical components, and whether it defines public APIs or interfaces.
- **Use**: This variable is used to provide a structured prompt for users to generate comprehensive explanations of large source code files.


---
### SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_CPP 
- **Type**: `str`
- **Description**: The variable `SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_CPP` is a string that contains a detailed prompt for a C++ programmer and software engineering documentation expert. It outlines the role of the expert in explaining C++ code, focusing on technical details and the conceptual components and purpose of the software.
- **Use**: This variable is used to provide a detailed prompt for generating documentation for large C++ systems.


---
### SOURCE_CODE_SMALL_PURPOSE_USER_PROMPT 
- **Type**: `str`
- **Description**: `SOURCE_CODE_SMALL_PURPOSE_USER_PROMPT` is a string variable that contains a template for generating a concise explanation of a small source code file's purpose. It provides guidance on how to describe the functionality and type of code in a brief paragraph.
- **Use**: This variable is used to prompt users to provide a short and clear explanation of small source code files.


---
### SOURCE_CODE_SMALL_SYSTEM_PROMPT_GENERAL_CPP 
- **Type**: `str`
- **Description**: `SOURCE_CODE_SMALL_SYSTEM_PROMPT_GENERAL_CPP` is a string variable that contains a prompt template for generating documentation for small and simple C++ source code files. The prompt emphasizes the need for clarity and conciseness in the documentation.
- **Use**: This variable is used to provide a template for generating documentation for small C++ source code files.


---
### TECHNICAL_CONCEPTS 
- **Type**: `str`
- **Description**: The `TECHNICAL_CONCEPTS` variable is a string that contains a template for generating a paragraph description of the important technical features and their interactions in a source code file. It emphasizes writing about conceptual use cases, applications, logic, and component interactions rather than focusing on specific functions or variables.
- **Use**: This variable is used as a template for generating descriptive paragraphs about technical features in source code files.


---
### VARIABLES_FOUND_SYSTEM_PROMPT_JSON 
- **Type**: `string`
- **Description**: The variable `VARIABLES_FOUND_SYSTEM_PROMPT_JSON` is a string that contains a JSON schema template. This template is used to guide the documentation process for variables in C++ code, ensuring that the documentation follows a specific format. The schema includes fields for the type of the variable, a description, and its use.
- **Use**: This variable is used to provide a structured format for documenting C++ variables.


---
### VARIABLES_FOUND_USER_PROMPT 
- **Type**: `str`
- **Description**: `VARIABLES_FOUND_USER_PROMPT` is a string variable that contains a template for a user prompt. This prompt is used to instruct the user to summarize a global variable in the provided code. It includes guidelines on how to describe the variable, emphasizing the need for detail that matches the complexity of the variable.
- **Use**: This variable is used to generate a user prompt for summarizing global variables in a codebase.


---
### VARIABLES_NONE_CONTENT 
- **Type**: `string`
- **Description**: `VARIABLES_NONE_CONTENT` is a string variable that contains a message indicating that no global variables are defined in a given file. It is used as a placeholder or default message when no global variables are found during analysis.
- **Use**: This variable is used to signal the absence of global variables in a file.


# Classes

---
### CppClassCollection 
- **Type**: `class`
- **Members**:
    - `data`: A dictionary mapping strings to either a CppClassData instance or a list of CppClassData instances.
- **Description**: The `CppClassCollection` class is a specialized collection class that inherits from `IrCollection`. It is designed to manage a collection of C++ class data, represented by the `CppClassData` type. The class provides a class method `from_llm` which facilitates the creation of a `CppClassCollection` instance from a language model and a list of raw symbols, leveraging the `from_llm_with_ir_data` method to populate the collection with `CppClassData` instances. This class is part of a system that processes and organizes C++ code symbols for further analysis or documentation.
- **Inherits From**:
    - IrCollection

**Methods**

---
#### CppClassCollection.from_llm
The `from_llm` function creates an instance of the class using data from a language model and a collection of raw symbols.
- **Inputs**:
    - `llm`: An instance of the `ChatOpenAI` class, representing a language model.
    - `symbols_list`: An instance of `RawSymbolCollection`, representing a collection of raw symbols.
- **Control Flow**:
    - The function calls `from_llm_with_ir_data` on the class (`cls`) with `CppClassData`, `llm`, and `symbols_list` as arguments.
    - The result of the `from_llm_with_ir_data` call is returned as the output of the function.
- **Output**:
    - The function returns an instance of the class (`Self`) created using the language model and the raw symbols collection.



---
### CppClassData 
- **Type**: `class`
- **Members**:
    - `system_prompt`: Returns a system prompt string for documenting C++ data structures.
    - `user_prompt`: Generates a user prompt string for a given C++ symbol.
    - `child_to_ir`: Maps a symbol kind to its corresponding intermediate representation class or None.
    - `child_to_field_name`: Maps a symbol kind to its corresponding scope relation field name.
- **Description**: The `CppClassData` class is a specialized subclass of `ClassData` designed to handle C++ class data structures. It provides class methods to generate system and user prompts for documenting C++ data structures, specifically focusing on classes, structs, and enums. The class also includes methods to map child symbols to their respective intermediate representation classes and field names based on their kind, such as methods or nested classes. This class is part of a larger framework for analyzing and documenting C++ code, leveraging symbol data extracted from source files.
- **Inherits From**:
    - ClassData

**Methods**

---
#### CppClassData.child_to_field_name
The `child_to_field_name` function maps a `RawSymbolData` object's `symbol_kind` to a corresponding `ScopeRelation` value.
- **Inputs**:
    - `cls`: The class object that the method is bound to, typically used for class methods.
    - `child`: An instance of `RawSymbolData` representing a symbol with a specific kind.
- **Control Flow**:
    - A dictionary `mapping` is defined to map `SymbolKind` values to `ScopeRelation` values.
    - The function attempts to retrieve the `ScopeRelation` value from the `mapping` dictionary using the `symbol_kind` attribute of the `child` argument.
- **Output**:
    - The function returns a `ScopeRelation` value corresponding to the `symbol_kind` of the `child`, or `None` if no mapping is found.


---
#### CppClassData.child_to_ir
The `child_to_ir` function maps a given symbol's kind to a corresponding intermediate representation (IR) data type or returns None if no mapping is applicable.
- **Inputs**:
    - `cls`: The class reference, typically used for class methods.
    - `symbol`: An instance of `RawSymbolData` representing a symbol with a specific kind that needs to be mapped to an IR data type.
- **Control Flow**:
    - A dictionary `mapping` is defined to associate `SymbolKind` values with corresponding IR data types or None.
    - The function attempts to retrieve the IR data type from the `mapping` dictionary using the `symbol.symbol_kind` as the key.
    - If a match is found, the corresponding IR data type is returned; otherwise, None is returned.
- **Output**:
    - The function returns a type of `IrData` if a mapping exists for the symbol's kind, or None if no mapping is applicable.


---
#### CppClassData.system_prompt
The `system_prompt` function returns a predefined JSON string that serves as a system prompt for documenting C++ data structures.
- **Inputs**:
    - None
- **Control Flow**:
    - The function directly returns the constant `DATA_STRUCTURES_FOUND_SYSTEM_PROMPT_JSON`.
- **Output**:
    - A string containing a JSON schema for documenting C++ data structures.


---
#### CppClassData.user_prompt
The `user_prompt` function generates a formatted string prompt for a given symbol, including its name, code, and optionally the full file code.
- **Inputs**:
    - `cls`: The class reference, typically used in class methods to access class-level attributes or methods.
    - `symbol`: An instance of `RawSymbolData` containing information about a symbol, including its name, symbol code, and optionally the full file code.
- **Control Flow**:
    - Initialize a string `user_prompt` with a predefined prompt and the symbol's name and code.
    - Check if the symbol has associated file code; if so, append it to the `user_prompt`.
    - Return the constructed `user_prompt` string.
- **Output**:
    - A formatted string that includes the symbol's name, code, and optionally the full file code.



---
### CppClassRawSymbolCollection 
- **Type**: `class`
- **Members**:
    - `data`: A dictionary mapping symbol names to RawSymbolData instances.
- **Description**: The `CppClassRawSymbolCollection` class is a specialized collection for handling raw symbol data extracted from C++ code, specifically focusing on class-related symbols. It inherits from `RawSymbolCollection` and provides methods to populate its data from static analysis of C++ code using ctags. The class processes symbols to identify C++ functions and data structures, organizing them into a structured format that includes handling of method overloading and nested classes. It does not support creation from LLM and relies on static analysis for its operations.
- **Inherits From**:
    - RawSymbolCollection

**Methods**

---
#### CppClassRawSymbolCollection.from_llm
The `from_llm` function is a class method that raises a NotImplementedError, indicating that static analysis should be used for C++ classes instead of this method.
- **Inputs**:
    - `code`: A string representing the code to be analyzed.
    - `root_rel_path`: A string representing the root relative path of the code file.
- **Control Flow**:
    - The function immediately raises a NotImplementedError with a specific message.
- **Output**:
    - The function does not return any output as it raises an exception.


---
#### CppClassRawSymbolCollection.from_static_analysis
The `from_static_analysis` function performs static analysis on C++ code to extract and organize symbol data related to classes and functions using ctags.
- **Inputs**:
    - `code`: A string representing the C++ source code to be analyzed.
    - `root_rel_path`: A Path object representing the root-relative path of the file containing the code.
- **Control Flow**:
    - Determine if the code requires multi-prompt processing using `code_requires_multi_prompt` function.
    - Extract symbols from the code using `extract_symbols_w_ctags` function.
    - Initialize dictionaries for global method counts and raw symbol data for classes.
    - Iterate over extracted symbols to count global methods and create raw symbol data for data structures.
    - For each symbol, check if it is a function within a data structure and update the class symbol data accordingly.
    - Check for nested data structures and update the class symbol data with nested class information.
    - Return `None` if no class symbol data is found, otherwise return an instance of the class with the collected data.
- **Output**:
    - Returns an instance of the class containing the collected raw symbol data if any class data is found, otherwise returns None.


---
#### CppClassRawSymbolCollection.to_dict
The `to_dict` function returns the `data` attribute of the instance as a dictionary.
- **Inputs**:
    - None
- **Control Flow**:
    - The function directly returns the `data` attribute of the instance without any additional processing.
- **Output**:
    - A dictionary where the keys are strings and the values are of type `RawSymbolData`.



---
### CppFnCollection 
- **Type**: `class`
- **Members**:
    - `data`: A dictionary mapping strings to either a CppFnData instance or a list of CppFnData instances.
- **Description**: The `CppFnCollection` class is a specialized collection class that inherits from `IrCollection`. It is designed to manage a collection of C++ function data, represented by the `CppFnData` class. The class provides a class method `from_llm` which facilitates the creation of a `CppFnCollection` instance using a language model (`llm`) and a list of raw symbols (`symbols_list`). This method leverages the `from_llm_with_ir_data` method to populate the collection with `CppFnData` instances, effectively bridging the gap between raw symbol data and structured intermediate representation data for C++ functions.
- **Inherits From**:
    - IrCollection

**Methods**

---
#### CppFnCollection.from_llm
The `from_llm` function creates an instance of the class by invoking the `from_llm_with_ir_data` method with `CppFnData`, a language model, and a collection of symbols.
- **Inputs**:
    - `llm`: An instance of the `ChatOpenAI` class, representing a language model.
    - `symbols_list`: An instance of `RawSymbolCollection`, representing a collection of raw symbols.
- **Control Flow**:
    - The function calls `cls.from_llm_with_ir_data` with `CppFnData`, `llm`, and `symbols_list` as arguments.
    - The result of the `from_llm_with_ir_data` call is returned as the output of the function.
- **Output**:
    - An instance of the class from which the method is called, initialized using the provided language model and symbol collection.



---
### CppFnData 
- **Type**: `class`
- **Members**:
    - `system_prompt`: Returns a predefined system prompt for documenting C++ functions.
    - `user_prompt`: Generates a user prompt string based on the provided symbol data.
    - `child_to_ir`: Raises a NotImplementedError as functions should not have children.
    - `child_to_field_name`: Raises a NotImplementedError as functions should not have children.
- **Description**: The `CppFnData` class is a specialized subclass of `FnData` designed to handle the documentation of C++ functions. It provides class methods to generate system and user prompts for documenting functions, utilizing predefined templates and symbol data. The class also includes methods that raise exceptions for operations related to child elements, as functions are not expected to have children in this context. This class is part of a larger framework for extracting and documenting C++ code elements.
- **Inherits From**:
    - FnData

**Methods**

---
#### CppFnData.child_to_field_name
The function `child_to_field_name` raises a `NotImplementedError` indicating that functions should not have children.
- **Inputs**:
    - `cls`: The class method's implicit first argument, representing the class itself.
    - `child`: An instance of `RawSymbolData`, representing a child symbol data.
- **Control Flow**:
    - The function immediately raises a `NotImplementedError` with the message 'Functions should not have children'.
- **Output**:
    - The function does not return any output as it raises an exception.


---
#### CppFnData.child_to_ir
The `child_to_ir` function raises a `NotImplementedError` indicating that functions should not have children.
- **Inputs**:
    - `cls`: The class on which this method is called, typically a class method.
    - `symbol`: An instance of `RawSymbolData` representing the symbol data to be processed.
- **Control Flow**:
    - The function immediately raises a `NotImplementedError` with a specific message.
- **Output**:
    - The function does not return any value as it raises an exception.


---
#### CppFnData.system_prompt
The `system_prompt` function returns a predefined JSON schema string for documenting C++ functions.
- **Inputs**:
    - None
- **Control Flow**:
    - The function directly returns the constant `FUNCTIONS_FOUND_SYSTEM_PROMPT_JSON`.
- **Output**:
    - A string containing a JSON schema for documenting C++ functions.


---
#### CppFnData.user_prompt
The `user_prompt` function generates a formatted string containing a function's name and code, and optionally the full file code, for documentation purposes.
- **Inputs**:
    - `cls`: The class from which this method is called, typically used in class methods.
    - `symbol`: An instance of `RawSymbolData` containing information about a symbol, including its name, symbol code, and optionally the full file code.
- **Control Flow**:
    - Initialize `user_prompt` with a formatted string containing a predefined prompt, the symbol's name, and its code.
    - Check if the `symbol` has associated file code.
    - If file code is present, append it to the `user_prompt` string.
    - Return the complete `user_prompt` string.
- **Output**:
    - A string that includes the function's name, its code, and optionally the full file code, formatted for documentation.



---
### CppFreeFnRawSymbolCollection 
- **Type**: `class`
- **Members**:
    - `data`: A dictionary mapping function names to lists of RawSymbolData objects.
- **Description**: The `CppFreeFnRawSymbolCollection` class is designed to collect and manage raw symbol data for C++ free functions, which are functions not contained within a class or struct. It inherits from `RawSymbolCollection` and provides methods to extract and organize function symbols from C++ code using static analysis. The class primarily focuses on identifying functions, determining if they are overloaded, and storing their raw symbol data in a structured format. It does not support extraction via language models (LLM) and relies on static analysis for symbol extraction.
- **Inherits From**:
    - RawSymbolCollection

**Methods**

---
#### CppFreeFnRawSymbolCollection.from_llm
The `from_llm` function is a class method that raises a NotImplementedError, indicating that static analysis should be used for C++ functions instead of this method.
- **Inputs**:
    - `code`: A string representing the code to be analyzed.
    - `root_rel_path`: A string representing the root relative path of the code file.
- **Control Flow**:
    - The function immediately raises a NotImplementedError with a specific message.
- **Output**:
    - The function does not return any output as it raises an exception.


---
#### CppFreeFnRawSymbolCollection.from_static_analysis
The `from_static_analysis` function extracts and processes C++ function symbols from a given code string and returns a collection of raw symbol data.
- **Inputs**:
    - `cls`: The class type to which this method belongs, used to instantiate the output object.
    - `code`: A string containing the C++ source code to be analyzed.
    - `root_rel_path`: The relative path to the root directory of the source code file, used for symbol extraction.
- **Control Flow**:
    - Determine if the code requires multi-prompt processing using `code_requires_multi_prompt` function.
    - Extract symbols from the code using `extract_symbols_w_ctags` with the provided root relative path and code.
    - Create a list of all function names from the extracted symbols that are of kind `CPP_FUNCTIONS` and do not start with `__anon`.
    - Initialize an empty dictionary `fn_raw_symbol_data` to store raw symbol data for functions.
    - Iterate over each symbol in the extracted symbols.
    - For each symbol, check if it is a function and not contained within a class or data structure.
    - Construct the function name, considering its scope if it belongs to a data structure.
    - Check if the function is overloaded by counting its occurrences in `all_fn_names`.
    - Create raw symbol data using `create_raw_symbol_via_ctags` and append it to `fn_raw_symbol_data` under the constructed function name.
    - Return `None` if no function symbols were processed, otherwise return an instance of `cls` initialized with `fn_raw_symbol_data`.
- **Output**:
    - Returns an instance of the class `cls` containing a dictionary of raw symbol data for C++ functions, or `None` if no function symbols are found.


---
#### CppFreeFnRawSymbolCollection.to_dict
The `to_dict` function returns the `data` attribute of the instance as a dictionary.
- **Inputs**:
    - None
- **Control Flow**:
    - The function directly returns the `data` attribute of the instance without any additional processing.
- **Output**:
    - A dictionary where the keys are strings and the values are `RawSymbolData` objects.



---
### CppVariableCollection 
- **Type**: `class`
- **Members**:
    - `data`: A dictionary mapping string keys to either a CppVariableData instance or a list of CppVariableData instances.
- **Description**: The `CppVariableCollection` class is a specialized collection class that inherits from `IrCollection`. It is designed to manage a collection of C++ variable data, represented by the `CppVariableData` class. The class provides a class method `from_llm` which facilitates the creation of a `CppVariableCollection` instance from a language model and a list of raw symbols, leveraging the `from_llm_with_ir_data` method to populate the collection with `CppVariableData` instances. This class is part of a larger system for handling intermediate representations of C++ code symbols.
- **Inherits From**:
    - IrCollection

**Methods**

---
#### CppVariableCollection.from_llm
The `from_llm` function creates an instance of the class using data from a language model and a collection of symbols.
- **Inputs**:
    - `llm`: An instance of the ChatOpenAI class, representing a language model.
    - `symbols_list`: A collection of raw symbols, represented by the RawSymbolCollection class.
- **Control Flow**:
    - The function calls the `from_llm_with_ir_data` method of the class, passing `CppVariableData`, `llm`, and `symbols_list` as arguments.
    - The `from_llm_with_ir_data` method is expected to handle the creation of the class instance using the provided data.
- **Output**:
    - Returns an instance of the class that called the method, initialized with data from the language model and symbols list.



---
### CppVariableData 
- **Type**: `class`
- **Members**:
    - `system_prompt`: Returns a system prompt string for documenting C++ variables.
    - `user_prompt`: Generates a user prompt string based on the provided symbol data.
    - `child_to_ir`: Raises a NotImplementedError as variables should not have children.
    - `child_to_field_name`: Raises a NotImplementedError as variables should not have children.
- **Description**: The `CppVariableData` class is a specialized class for handling C++ variable data within a documentation context. It provides class methods to generate system and user prompts for documenting variables, ensuring that the documentation process is consistent and informative. The class also explicitly disallows the concept of child elements for variables, as indicated by the `NotImplementedError` in the `child_to_ir` and `child_to_field_name` methods, reinforcing the idea that variables do not have hierarchical children in this context.
- **Inherits From**:
    - VariableData

**Methods**

---
#### CppVariableData.child_to_field_name
The `child_to_field_name` function raises a `NotImplementedError` indicating that variables should not have children.
- **Inputs**:
    - `cls`: The class object from which the method is called.
    - `child`: An instance of `RawSymbolData` representing a child symbol.
- **Control Flow**:
    - The function immediately raises a `NotImplementedError` with a specific message.
- **Output**:
    - The function does not return any value as it raises an exception.


---
#### CppVariableData.child_to_ir
The `child_to_ir` function raises a `NotImplementedError` indicating that variables should not have children.
- **Inputs**:
    - `cls`: The class on which this method is called, typically a class method.
    - `symbol`: An instance of `RawSymbolData` representing the symbol data to be processed.
- **Control Flow**:
    - The function immediately raises a `NotImplementedError` with a specific message.
- **Output**:
    - The function does not return any value as it raises an exception.


---
#### CppVariableData.system_prompt
The `system_prompt` function returns a predefined JSON schema string for documenting variables in C++ code.
- **Inputs**:
    - None
- **Control Flow**:
    - The function directly returns the constant `VARIABLES_FOUND_SYSTEM_PROMPT_JSON`.
- **Output**:
    - The function outputs a string containing a JSON schema for documenting C++ variables.


---
#### CppVariableData.user_prompt
The `user_prompt` function generates a formatted string prompt for a given symbol, including its name, code, and optionally the full file code.
- **Inputs**:
    - `cls`: The class reference, typically used in class methods to access class-level attributes or methods.
    - `symbol`: An instance of `RawSymbolData` containing information about a symbol, including its name, symbol code, and optionally file code.
- **Control Flow**:
    - Initialize a string `user_prompt` with a formatted message including the symbol's name and symbol code.
    - Check if the `symbol` has associated file code.
    - If file code is present, append it to the `user_prompt` string.
    - Return the complete `user_prompt` string.
- **Output**:
    - A formatted string containing the symbol's name, symbol code, and optionally the full file code.



---
### CppVariableRawSymbolCollection 
- **Type**: `class`
- **Members**:
    - `data`: A dictionary mapping string keys to RawSymbolData objects.
- **Description**: The `CppVariableRawSymbolCollection` class is a specialized collection for handling raw symbol data related to C++ variables. It inherits from `RawSymbolCollection` and provides methods for creating instances from static analysis of C++ code using ctags. The class is designed to facilitate the extraction and organization of variable symbols in C++ code, storing them in a dictionary format. It does not support creation from language model analysis, emphasizing its reliance on static analysis tools.
- **Inherits From**:
    - RawSymbolCollection

**Methods**

---
#### CppVariableRawSymbolCollection.from_llm
The `from_llm` function is a class method intended to create an instance of the class using a language model and a list of symbols, but it raises a NotImplementedError indicating that static analysis should be used instead.
- **Inputs**:
    - `llm`: An instance of the ChatOpenAI class, representing a language model.
    - `symbols_list`: An instance of RawSymbolCollection, representing a collection of symbols to be processed.
- **Control Flow**:
    - The function is defined as a class method using the @classmethod decorator.
    - It takes two parameters: `llm` and `symbols_list`.
    - The function immediately raises a NotImplementedError with a message indicating that static analysis should be used for C++ variables.
- **Output**:
    - The function does not return any output as it raises a NotImplementedError.


---
#### CppVariableRawSymbolCollection.from_static_analysis
The `from_static_analysis` function performs a static analysis on C++ code to extract variable symbols using ctags.
- **Inputs**:
    - `cls`: The class type that will be used to create the collection of symbols.
    - `code`: A string containing the C++ source code to be analyzed.
    - `root_rel_path`: A Path object representing the root relative path of the source code file.
- **Control Flow**:
    - Calls the `default_ctags_analysis` function with the provided class type, code, root relative path, and specific parameters for variable symbol extraction.
    - Specifies `SymbolKind.VARIABLE` to indicate that the analysis is focused on variable symbols.
    - Uses `CPP_VARIABLES` to define the kinds of C++ symbols to be extracted, specifically variables and extern variables.
    - Sets the delimiter to '::' and enables symbol padding for the analysis.
- **Output**:
    - Returns an instance of the class type `cls` containing the extracted variable symbols, or `None` if no symbols are found.


---
#### CppVariableRawSymbolCollection.to_dict
The `to_dict` function returns the `data` attribute of the instance as a dictionary.
- **Inputs**:
    - None
- **Control Flow**:
    - The function directly returns the `data` attribute of the instance without any additional processing.
- **Output**:
    - A dictionary where the keys are strings and the values are `RawSymbolData` objects.



