# Purpose
This Python source code file is designed to facilitate the extraction and documentation of C language constructs such as functions, variables, data structures, and declarations. It leverages static analysis to parse C code and generate structured representations of these constructs using classes like `CDeclarationRawSymbolCollection`, `CFunctionRawSymbolCollection`, `CVariableRawSymbolCollection`, and others. These classes are responsible for collecting raw symbol data from C code, which is then used to create detailed documentation prompts for each type of construct. The file also defines classes like `CFnData`, `CVariableData`, and `CDataStructureData` to handle the transformation of raw symbol data into intermediate representations (IR) that can be used to generate documentation.

The code is structured as a library intended to be imported and used in a larger system, likely one that automates the generation of documentation for C codebases. It defines a series of classes that encapsulate the logic for parsing C code, extracting relevant symbols, and preparing them for documentation. The file does not define public APIs or external interfaces directly but provides a framework for integrating with other components, such as a language model (e.g., `ChatOpenAI`) for generating natural language descriptions. The use of static analysis ensures that the documentation process is grounded in the actual code structure, providing accurate and detailed insights into the C code being analyzed.
# Imports and Dependencies

---
- `pathlib`
- `typing`
- `utils.models`
- `utils.treesitter_driver`
- `.ir_common`
- `.symbol_common`


# Global Variables

---
### C_VARIABLES
- **Type**: `set`
- **Description**: `C_VARIABLES` is a set containing two string elements: 'variable' and 'externvar'. This set is likely used to categorize or identify certain types of C variables or symbols within the context of the codebase.
- **Use**: This variable is used to store and reference specific C variable types or categories.


---
### DATA_STRUCTURES_FOUND_SYSTEM_PROMPT_JSON
- **Type**: `str`
- **Description**: The variable `DATA_STRUCTURES_FOUND_SYSTEM_PROMPT_JSON` is a string containing a JSON schema template for documenting data structures in C code. It provides a structured format for describing the type, members, and a detailed description of a data structure.
- **Use**: This variable is used to guide the documentation process for C data structures by providing a consistent JSON schema.


---
### DATA_STRUCTURES_FOUND_USER_PROMPT
- **Type**: `str`
- **Description**: The variable `DATA_STRUCTURES_FOUND_USER_PROMPT` is a string that contains a template prompt for summarizing data structures in C code. It provides guidelines for describing data structures, emphasizing the need for detail proportional to the complexity of the data structure.
- **Use**: This variable is used to generate user prompts for documenting data structures in C code.


---
### DATA_STRUCTURES_NONE_CONTENT
- **Type**: `str`
- **Description**: The variable `DATA_STRUCTURES_NONE_CONTENT` is a string that contains a message indicating that no custom data structures are defined in the file. It serves as a placeholder or default message when no data structures are found.
- **Use**: This variable is used to signal the absence of custom data structures in a given file.


---
### DECL_FOUND_USER_PROMPT
- **Type**: `str`
- **Description**: The variable `DECL_FOUND_USER_PROMPT` is a string that contains a template for a user prompt. This prompt is used to instruct a system to document a public API for a given function. The template includes placeholders for the function name and its code, which are dynamically inserted when the prompt is used.
- **Use**: This variable is used to generate a user prompt for documenting a function's public API.


---
### FUNCTIONS_FOUND_SYSTEM_PROMPT_JSON
- **Type**: `str`
- **Description**: The variable `FUNCTIONS_FOUND_SYSTEM_PROMPT_JSON` is a string that contains a JSON schema template for documenting functions in C code. It provides a structured format for describing the function's purpose, inputs, control flow, and output.
- **Use**: This variable is used to guide the documentation process for functions by providing a consistent schema to follow.


---
### FUNCTIONS_FOUND_USER_PROMPT
- **Type**: `str`
- **Description**: The variable `FUNCTIONS_FOUND_USER_PROMPT` is a string that contains a template for a user prompt. This prompt is used to request a summary of a function in a given code, including details about inputs, control flow, logic, and output. The prompt is designed to guide the user in providing a detailed explanation of the function's complexity.
- **Use**: This variable is used to store a template prompt for summarizing functions in code.


---
### FUNCTIONS_NONE_CONTENT
- **Type**: `str`
- **Description**: The variable `FUNCTIONS_NONE_CONTENT` is a string that contains a message indicating that no functions or function prototypes are defined in the file. This message is used as a placeholder or default content when no functions are found.
- **Use**: This variable is used to signal the absence of function definitions in a file.


---
### FUNCTION_DECLS_FOUND_SYSTEM_PROMPT_JSON
- **Type**: `string`
- **Description**: The variable `FUNCTION_DECLS_FOUND_SYSTEM_PROMPT_JSON` is a string that contains a JSON schema and guidelines for documenting public C APIs declared in header files. It provides a structured format for documenting functions, including a single sentence summary, a detailed description, input parameters, and output behavior.
- **Use**: This variable is used to guide the documentation process for C function declarations, ensuring consistency and clarity in API documentation.


---
### SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT
- **Type**: `str`
- **Description**: This variable is a string that contains a user prompt template for explaining the purpose of a large source code file. It guides the user to provide a detailed explanation of the file's purpose, focusing on its functionality, components, and whether it defines public APIs or interfaces.
- **Use**: This variable is used to generate a user prompt for explaining the purpose of large source code files.


---
### SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_C
- **Type**: `str`
- **Description**: This variable is a multi-line string that serves as a system prompt for a large C source code documentation task. It provides instructions for generating detailed documentation for C code, focusing on technical details and the purpose of the software.
- **Use**: This variable is used as a prompt to guide the generation of detailed documentation for large C source code files.


---
### SOURCE_CODE_SMALL_PURPOSE_USER_PROMPT
- **Type**: `str`
- **Description**: This variable is a string that contains a prompt for a user to explain the purpose of a small source code file. It guides the user to provide a concise explanation of the file's purpose in a single paragraph, focusing on the type of code and its functionality.
- **Use**: This variable is used to prompt users to describe the purpose of small source code files.


---
### SOURCE_CODE_SMALL_SYSTEM_PROMPT_GENERAL_C
- **Type**: `str`
- **Description**: This variable is a string that contains a system prompt for a documentation tool focused on small and simple C source code files. It provides guidance for generating concise and clear documentation for small C code files.
- **Use**: This variable is used to provide a system prompt for generating documentation for small C source code files.


---
### TECHNICAL_CONCEPTS
- **Type**: `str`
- **Description**: The `TECHNICAL_CONCEPTS` variable is a string that contains a template for a prompt. This prompt is designed to guide users in describing the important technical features and their interactions within a source code file. It emphasizes conceptual use cases, applications, logic, and component interactions rather than focusing on specific functions or variables.
- **Use**: This variable is used to provide a structured prompt for users to describe technical features in a source code file.


---
### VARIABLES_FOUND_SYSTEM_PROMPT_JSON
- **Type**: `str`
- **Description**: This variable is a string that contains a JSON schema for documenting variables in C code. It provides a template for describing the type, description, and use of a variable.
- **Use**: This variable is used to guide the documentation process for C variables by providing a structured format.


---
### VARIABLES_FOUND_USER_PROMPT
- **Type**: `list`
- **Description**: `VARIABLES_FOUND_USER_PROMPT` is a list of dictionaries, each containing a 'name' and 'content' key. The 'name' key holds the name of an input argument, while the 'content' key provides a description of that input argument.
- **Use**: This variable is used to store and organize information about input arguments for documentation purposes.


---
### VARIABLES_NONE_CONTENT
- **Type**: `str`
- **Description**: `VARIABLES_NONE_CONTENT` is a string variable that holds a message indicating that no global variables are defined in a given file. It is used as a constant message to inform users or developers about the absence of global variables in the analyzed code.
- **Use**: Used to convey the absence of global variables in a file.


# Classes

---
### CDataStructureCollection
- **Type**: `class`
- **Members**:
    - `data`: A dictionary mapping strings to either CDataStructureData or a list of CDataStructureData.
- **Description**: The CDataStructureCollection class is a specialized collection class that inherits from IrCollection. It is designed to manage a collection of CDataStructureData objects, which represent data structures in C code. The class provides a class method, from_llm, which facilitates the creation of a CDataStructureCollection instance using a language model and a list of raw symbols. This class is part of a larger system for analyzing and documenting C code, leveraging static analysis and language models to gather and organize information about C data structures.
- **Inherits From**:
    - IrCollection

**Methods**

---
#### CDataStructureCollection.from_llm
The `from_llm` function creates an instance of the class by invoking the `from_llm_with_ir_data` method with specific parameters.
- **Inputs**:
    - `llm`: An instance of the ChatOpenAI class, representing a language model.
    - `symbols_list`: An instance of RawSymbolCollection, representing a collection of raw symbols.
- **Control Flow**:
    - The function calls the `from_llm_with_ir_data` method on the class `cls`, passing `CDataStructureData`, `llm`, and `symbols_list` as arguments.
    - The result of the `from_llm_with_ir_data` method call is returned.
- **Output**:
    - An instance of the class `cls` is returned, created using the `from_llm_with_ir_data` method.



---
### CDataStructureData
- **Type**: `class`
- **Members**:
    - `system_prompt`: Returns a system prompt string for documenting C data structures.
    - `user_prompt`: Generates a user prompt string for a given C data structure symbol.
    - `child_to_ir`: Raises NotImplementedError as C data structures should not have children.
    - `child_to_field_name`: Raises NotImplementedError as C data structures should not have children.
- **Description**: The `CDataStructureData` class is a specialized class for handling C data structures within a documentation framework. It extends the `DataStructureData` class and provides methods to generate system and user prompts specifically tailored for documenting C data structures. The class also includes methods that raise `NotImplementedError` for operations related to child elements, as C data structures are not expected to have children in this context.
- **Inherits From**:
    - DataStructureData

**Methods**

---
#### CDataStructureData.child_to_field_name
The function raises an error indicating that C data structures should not have children.
- **Inputs**:
    - `cls`: The class method's implicit first argument, representing the class itself.
    - `symbol`: An instance of RawSymbolData, representing a symbol in the code.
- **Control Flow**:
    - The function immediately raises a NotImplementedError with a specific message.
- **Output**:
    - The function does not return any value; it raises an exception instead.


---
#### CDataStructureData.child_to_ir
The function raises a NotImplementedError indicating that C data structures should not have children.
- **Inputs**:
    - `cls`: The class object that the method is bound to, typically used to access class-level attributes or methods.
    - `symbol`: An instance of RawSymbolData, representing a symbol in the code that is being processed.
- **Control Flow**:
    - The function immediately raises a NotImplementedError with a specific message.
- **Output**:
    - The function does not return any value as it raises an exception.


---
#### CDataStructureData.system_prompt
The `system_prompt` function returns a predefined JSON string for documenting data structures in C.
- **Inputs**:
    - None
- **Control Flow**:
    - The function directly returns the constant `DATA_STRUCTURES_FOUND_SYSTEM_PROMPT_JSON`.
- **Output**:
    - A string containing a JSON schema for documenting C data structures.


---
#### CDataStructureData.user_prompt
The `user_prompt` function generates a formatted string prompt for documenting a data structure using its name and code, and optionally includes the full file code if available.
- **Inputs**:
    - `cls`: The class reference, typically used in class methods to refer to the class itself.
    - `symbol`: An instance of `RawSymbolData` containing information about a data structure, including its name, symbol code, and optionally the full file code.
- **Control Flow**:
    - Initialize a string `user_prompt` with a predefined prompt template and the data structure's name and code from the `symbol` object.
    - Check if the `symbol` object has `file_code` available.
    - If `file_code` is present, append it to the `user_prompt` string with appropriate formatting.
    - Return the constructed `user_prompt` string.
- **Output**:
    - A formatted string that includes the data structure's name, its code, and optionally the full file code if available.



---
### CDataStructureRawSymbolCollection
- **Type**: `class`
- **Members**:
    - `data`: A dictionary mapping string keys to RawSymbolData objects.
- **Description**: The CDataStructureRawSymbolCollection class is a specialized collection for handling raw symbol data related to C data structures. It inherits from RawSymbolCollection and provides methods for creating instances from static analysis of C code. The class primarily focuses on extracting and storing data structure definitions found in the code, utilizing a driver tree to parse the code and collect relevant symbols. It also includes a method to convert the stored data into a dictionary format. The class does not support creation from language model (LLM) analysis, as it is designed to rely on static analysis for C data structures.
- **Inherits From**:
    - RawSymbolCollection

**Methods**

---
#### CDataStructureRawSymbolCollection.from_llm
The `from_llm` function raises a NotImplementedError indicating that static analysis should be used for C data structures.
- **Inputs**:
    - `code`: A string representing the code to be analyzed.
    - `root_rel_path`: A string representing the root relative path for the code.
- **Control Flow**:
    - The function immediately raises a NotImplementedError with a specific message.
- **Output**:
    - The function does not return any value as it raises an exception.


---
#### CDataStructureRawSymbolCollection.from_static_analysis
The `from_static_analysis` function creates an instance of the class with data extracted from static analysis of code, or returns None if no relevant data is found.
- **Inputs**:
    - `code`: A string representing the source code to be analyzed.
    - `root_rel_path`: A Path object representing the root relative path of the source code file.
- **Control Flow**:
    - Create a CDriverTree instance from the provided code and root relative path.
    - Initialize an empty dictionary to store raw symbol data for data structures.
    - Determine if the code requires multi-prompt processing based on its size.
    - Iterate over each data structure definition extracted from the driver tree.
    - For each symbol with a name, create a RawSymbolData instance with various parameters including the code and path.
    - Store the created RawSymbolData in the dictionary using the symbol's name as the key.
    - Return None if no data structures were found, otherwise return an instance of the class with the collected data.
- **Output**:
    - Returns an instance of the class with data structure raw symbol data if any are found, otherwise returns None.


---
#### CDataStructureRawSymbolCollection.to_dict
The `to_dict` function returns the `data` attribute of the instance as a dictionary.
- **Inputs**:
    - None
- **Control Flow**:
    - The function directly returns the `data` attribute of the instance.
- **Output**:
    - A dictionary where keys are strings and values are `RawSymbolData` objects.



---
### CDeclarationCollection
- **Type**: `class`
- **Members**:
    - `data`: A dictionary mapping strings to either CFnDeclData or a list of CFnDeclData.
- **Description**: The CDeclarationCollection class is a specialized collection that inherits from IrCollection and is designed to manage C function declaration data. It stores its data in a dictionary where keys are strings and values are either a single CFnDeclData instance or a list of such instances. The class provides a class method, from_llm, which facilitates the creation of a CDeclarationCollection instance by leveraging language model data and a list of raw symbols, specifically using the CFnDeclData class to process the information.
- **Inherits From**:
    - IrCollection

**Methods**

---
#### CDeclarationCollection.from_llm
The `from_llm` function creates an instance of the class using LLM and symbol list data by calling another class method.
- **Inputs**:
    - `cls`: The class itself, used to call the class method.
    - `llm`: An instance of the ChatOpenAI class, representing a language model.
    - `symbols_list`: An instance of RawSymbolCollection, representing a collection of raw symbols.
- **Control Flow**:
    - The function calls the class method `from_llm_with_ir_data` with `CFnDeclData`, `llm`, and `symbols_list` as arguments.
    - The result of the `from_llm_with_ir_data` method call is returned.
- **Output**:
    - An instance of the class (`Self`) created using the provided LLM and symbol list data.



---
### CDeclarationRawSymbolCollection
- **Type**: `class`
- **Members**:
    - `data`: A dictionary mapping string keys to RawSymbolData objects.
- **Description**: The `CDeclarationRawSymbolCollection` class is a specialized collection for handling raw symbol data related to C declarations. It inherits from `RawSymbolCollection` and provides methods to create instances from static analysis of code. The class focuses on extracting and storing declaration symbols that have been matched to definitions, ensuring that only relevant symbols are included in the collection. It also includes a method to convert the stored data into a dictionary format, facilitating easy access and manipulation of the symbol data.
- **Inherits From**:
    - RawSymbolCollection

**Methods**

---
#### CDeclarationRawSymbolCollection.from_llm
The `from_llm` function is a placeholder method intended to be overridden for creating an instance from a language model, but currently raises a NotImplementedError.
- **Inputs**:
    - `code`: A string representing the code to be analyzed or processed.
    - `root_rel_path`: A string representing the root relative path where the code is located.
- **Control Flow**:
    - The function immediately raises a NotImplementedError with a message indicating that static analysis should be used for C imports.
- **Output**:
    - The function does not return any value as it raises an exception.


---
#### CDeclarationRawSymbolCollection.from_static_analysis
The function `from_static_analysis` creates an instance of the class with raw symbol data from static analysis of code, or returns None if no valid symbols are found.
- **Inputs**:
    - `code`: A string representing the source code to be analyzed.
    - `root_rel_path`: A Path object representing the root relative path of the source code file.
    - `reified_symbols`: A list of ReifiedSymbol objects or None, representing symbols extracted from the code that may include declarations and definitions.
- **Control Flow**:
    - Initialize an empty dictionary `declaration_raw_symbol_data` to store raw symbol data.
    - Determine if the code requires multi-prompt processing by calling `code_requires_multi_prompt` with the code.
    - Filter `reified_symbols` to get only those that are declarations and store them in `decl_symbols`.
    - Iterate over each `reified_sym` in `decl_symbols`.
    - For each `reified_sym`, check if the symbol has a name and a definition.
    - If both conditions are met, create a `RawSymbolData` object using `RawSymbolData.from_tree_sitter_raw_symbol` with various parameters including the symbol, path, and code.
    - Store the created `RawSymbolData` object in `declaration_raw_symbol_data` with the symbol's name as the key.
    - Check if `declaration_raw_symbol_data` is empty; if it is, set `output` to None, otherwise create an instance of the class with `declaration_raw_symbol_data` and assign it to `output`.
    - Return the `output`.
- **Output**:
    - Returns an instance of the class with the collected raw symbol data if any valid symbols are found, otherwise returns None.


---
#### CDeclarationRawSymbolCollection.to_dict
The `to_dict` function returns the `data` attribute of the instance as a dictionary.
- **Inputs**:
    - None
- **Control Flow**:
    - The function directly returns the `data` attribute of the instance without any additional processing.
- **Output**:
    - A dictionary where the keys are strings and the values are `RawSymbolData` objects.



---
### CFnData
- **Type**: `class`
- **Members**:
    - `system_prompt`: Returns a system prompt string for documenting C functions.
    - `user_prompt`: Generates a user prompt string for a given C function symbol.
    - `child_to_ir`: Raises NotImplementedError as C functions should not have children.
    - `child_to_field_name`: Raises NotImplementedError as C functions should not have children.
- **Description**: The `CFnData` class is a specialized subclass of `FnData` designed to handle the documentation of C functions. It provides class methods to generate system and user prompts for documenting C functions, utilizing predefined JSON schema strings. The class explicitly raises `NotImplementedError` for methods related to child handling, as C functions are not expected to have children in this context. This class is part of a larger framework for analyzing and documenting C code, focusing on functions.
- **Inherits From**:
    - FnData

**Methods**

---
#### CFnData.child_to_field_name
The function raises an error indicating that C functions should not have children.
- **Inputs**:
    - `cls`: The class reference from which the method is called.
    - `symbol`: An instance of RawSymbolData representing a symbol in the code.
- **Control Flow**:
    - The function immediately raises a NotImplementedError with a specific message.
- **Output**:
    - The function does not return any value as it raises an exception.


---
#### CFnData.child_to_ir
The function `child_to_ir` raises a `NotImplementedError` indicating that C functions should not have children.
- **Inputs**:
    - `cls`: The class reference, typically used in class methods.
    - `symbol`: An instance of `RawSymbolData` representing a symbol in the code.
- **Control Flow**:
    - The function immediately raises a `NotImplementedError` with a specific message.
- **Output**:
    - The function does not return any value as it raises an exception.


---
#### CFnData.system_prompt
The function returns a predefined JSON string used as a system prompt for documenting C functions.
- **Inputs**:
    - None
- **Control Flow**:
    - The function directly returns a constant string without any conditions or iterations.
- **Output**:
    - A string containing a JSON schema for documenting C functions.


---
#### CFnData.user_prompt
The `user_prompt` function generates a formatted string containing a function's name and code, and optionally the full file code, for user prompts.
- **Inputs**:
    - `cls`: The class reference, typically used in class methods.
    - `symbol`: An instance of `RawSymbolData` containing information about a function, including its name, symbol code, and optionally the full file code.
- **Control Flow**:
    - Initialize `user_prompt` with a formatted string containing a predefined prompt, the function's name, and its code from `symbol`.
    - Check if `symbol.file_code` is not empty or None.
    - If `symbol.file_code` is present, append the full file code to `user_prompt`.
    - Return the constructed `user_prompt` string.
- **Output**:
    - A string that includes the function's name, its code, and optionally the full file code, formatted for user prompts.



---
### CFnDeclData
- **Type**: `class`
- **Members**:
    - `system_prompt`: Returns a JSON string for documenting C function declarations.
    - `user_prompt`: Generates a user prompt string for documenting a C function symbol.
    - `child_to_ir`: Raises NotImplementedError as C declarations should not have children.
    - `child_to_field_name`: Raises NotImplementedError as C declarations should not have children.
- **Description**: The `CFnDeclData` class is a specialized subclass of `FnDeclData` designed to handle C function declarations. It provides class methods to generate system and user prompts for documenting C function declarations, ensuring that the documentation is based on the public API interface. The class also explicitly raises `NotImplementedError` for methods related to child processing, as C declarations are not expected to have children in this context.
- **Inherits From**:
    - FnDeclData

**Methods**

---
#### CFnDeclData.child_to_field_name
The function raises an error indicating that C declarations should not have children.
- **Inputs**:
    - `cls`: The class from which the method is called.
    - `symbol`: An instance of RawSymbolData representing a symbol in the code.
- **Control Flow**:
    - The function immediately raises a NotImplementedError with a specific message.
- **Output**:
    - The function does not return any value as it raises an exception.


---
#### CFnDeclData.child_to_ir
The function raises a NotImplementedError indicating that C declarations should not have children.
- **Inputs**:
    - `cls`: The class reference from which the method is called.
    - `symbol`: An instance of RawSymbolData representing a symbol in the code.
- **Control Flow**:
    - The function immediately raises a NotImplementedError with a specific message.
- **Output**:
    - The function does not return any value as it raises an exception.


---
#### CFnDeclData.system_prompt
The function returns a predefined JSON string for documenting C function declarations.
- **Inputs**:
    - None
- **Control Flow**:
    - The function directly returns a constant string without any computation or branching.
- **Output**:
    - A string containing a JSON schema for documenting C function declarations.


---
#### CFnDeclData.user_prompt
The `user_prompt` function generates a user prompt string by combining a predefined prompt with the symbol's code and optionally its associated header file code.
- **Inputs**:
    - `cls`: The class reference, typically used in class methods.
    - `symbol`: An instance of RawSymbolData containing information about a symbol, including its definition and associated file code.
- **Control Flow**:
    - Retrieve the symbol's code from the `symbol` argument's `reified_symbol.definition.raw.symbol_code` attribute.
    - Initialize the `user_prompt` string with a predefined prompt followed by the symbol's code.
    - Check if the `symbol` has associated file code (`symbol.file_code`).
    - If associated file code exists, append it to the `user_prompt` string with a header indicating it is header file code.
    - Return the constructed `user_prompt` string.
- **Output**:
    - A string that combines a predefined prompt with the symbol's code and optionally its associated header file code.



---
### CFunctionCollection
- **Type**: `class`
- **Members**:
    - `data`: A dictionary mapping strings to CFnData or lists of CFnData.
- **Description**: The `CFunctionCollection` class is a specialized collection class that inherits from `IrCollection`. It is designed to manage a collection of C function data, represented by the `CFnData` class or lists of `CFnData`. The class provides a class method `from_llm` which facilitates the creation of a `CFunctionCollection` instance from a language model and a list of raw symbols, leveraging the `from_llm_with_ir_data` method to populate the collection with intermediate representation data.
- **Inherits From**:
    - IrCollection

**Methods**

---
#### CFunctionCollection.from_llm
The `from_llm` function creates an instance of the class using LLM and symbol data.
- **Inputs**:
    - `llm`: An instance of the ChatOpenAI class, representing a language model.
    - `symbols_list`: An instance of RawSymbolCollection, representing a collection of raw symbols.
- **Control Flow**:
    - The function calls the `from_llm_with_ir_data` method of the class, passing `CFnData`, `llm`, and `symbols_list` as arguments.
    - The `from_llm_with_ir_data` method is expected to return an instance of the class, which is then returned by the `from_llm` function.
- **Output**:
    - An instance of the class that `from_llm` is a method of, created using the provided LLM and symbol data.



---
### CFunctionRawSymbolCollection
- **Type**: `class`
- **Members**:
    - `data`: A dictionary mapping function names to their corresponding RawSymbolData.
- **Description**: The CFunctionRawSymbolCollection class is designed to collect and manage raw symbol data specifically for C functions. It extends the RawSymbolCollection class and provides methods to populate its data from static analysis of C code. The class focuses on extracting callable symbols from a list of reified symbols, creating RawSymbolData instances for each, and storing them in a dictionary. It also includes a method to convert the stored data into a dictionary format, but does not support creation from language model analysis, emphasizing the use of static analysis for C functions.
- **Inherits From**:
    - RawSymbolCollection

**Methods**

---
#### CFunctionRawSymbolCollection.from_llm
The `from_llm` function raises a NotImplementedError indicating that static analysis should be used for C functions.
- **Inputs**:
    - `code`: A string representing the code to be analyzed.
    - `root_rel_path`: A string representing the root relative path for the code.
- **Control Flow**:
    - The function immediately raises a NotImplementedError with a specific message.
- **Output**:
    - The function does not return any value as it raises an exception.


---
#### CFunctionRawSymbolCollection.from_static_analysis
The function extracts and processes callable symbols from a list of reified symbols, returning a collection of raw symbol data if any are found.
- **Inputs**:
    - `code`: A string representing the source code to be analyzed.
    - `root_rel_path`: A Path object representing the root relative path of the source code file.
    - `reified_symbols`: A list of ReifiedSymbol objects or None, representing symbols extracted from the source code.
- **Control Flow**:
    - Filter the reified_symbols list to include only those with a symbol kind of CALLABLE.
    - Determine if the code requires multi-prompt processing by calling code_requires_multi_prompt.
    - Iterate over the filtered list of callable symbols.
    - For each symbol, if it has a name, create a RawSymbolData object using from_tree_sitter_raw_symbol with various parameters including the symbol, path, and code.
    - Store the created RawSymbolData object in a dictionary with the symbol's name as the key.
    - Check if the dictionary of raw symbol data is empty; if it is, return None.
    - If the dictionary is not empty, return an instance of the class with the dictionary as its data.
- **Output**:
    - Returns an instance of the class containing a dictionary of raw symbol data if any callable symbols are found, otherwise returns None.


---
#### CFunctionRawSymbolCollection.to_dict
The `to_dict` function returns the `data` attribute of the instance as a dictionary.
- **Inputs**:
    - None
- **Control Flow**:
    - The function directly returns the `data` attribute of the instance.
- **Output**:
    - A dictionary where the keys are strings and the values are `RawSymbolData` objects.



---
### CIncludeRawSymbolCollection
- **Type**: `class`
- **Members**:
    - `data`: A dictionary mapping string keys to RawSymbolData objects.
- **Description**: The `CIncludeRawSymbolCollection` class is a specialized collection for handling raw symbol data related to C include statements. It inherits from `RawSymbolCollection` and provides methods to populate the collection using static analysis of C code. The class includes a method `from_static_analysis` that extracts import symbols from a given C code and constructs a dictionary of `RawSymbolData` objects, which is then used to instantiate the collection. The class also provides a `to_dict` method to retrieve the stored data as a dictionary. The `from_llm` method is not implemented, as static analysis is preferred for handling C imports.
- **Inherits From**:
    - RawSymbolCollection

**Methods**

---
#### CIncludeRawSymbolCollection.from_llm
The `from_llm` function is a placeholder method intended to be overridden for creating an instance of the class using LLM (Large Language Model) data, but currently raises a NotImplementedError.
- **Inputs**:
    - `code`: A string representing the code to be processed.
    - `root_rel_path`: A string representing the root relative path for the code.
- **Control Flow**:
    - The function immediately raises a NotImplementedError with a message indicating that static analysis should be used for C imports.
- **Output**:
    - The function does not return any value as it raises an exception.


---
#### CIncludeRawSymbolCollection.from_static_analysis
The `from_static_analysis` function creates an instance of the class with import data extracted from static analysis of C code, or returns None if no imports are found.
- **Inputs**:
    - `code`: A string representing the C source code to be analyzed.
    - `root_rel_path`: A Path object representing the root relative path of the source code file.
- **Control Flow**:
    - Create a CDriverTree object from the provided code and root_rel_path.
    - Determine if the code requires multiple prompts using the code_requires_multi_prompt function.
    - Initialize an empty dictionary to store import data.
    - Iterate over each import symbol extracted from the driver tree.
    - For each import symbol, create a RawSymbolData object with relevant attributes and add it to the import dictionary.
    - Check if the import dictionary is empty; if it is, set output to None, otherwise create an instance of the class with the import dictionary as data.
    - Return the output, which is either None or the class instance with import data.
- **Output**:
    - Returns an instance of the class with import data if imports are found, otherwise returns None.


---
#### CIncludeRawSymbolCollection.to_dict
The `to_dict` function returns the `data` attribute of the instance as a dictionary.
- **Inputs**:
    - None
- **Control Flow**:
    - The function directly returns the `data` attribute of the instance.
- **Output**:
    - A dictionary where the keys are strings and the values are `RawSymbolData` objects.



---
### CVariableCollection
- **Type**: `class`
- **Members**:
    - `data`: A dictionary mapping strings to CVariableData or lists of CVariableData.
- **Description**: The CVariableCollection class is a specialized collection that inherits from IrCollection and is designed to manage a collection of CVariableData objects. It provides a class method, from_llm, which facilitates the creation of a CVariableCollection instance using data from a language model (llm) and a list of raw symbols. This class is part of a system that processes and organizes variable data, likely for further analysis or transformation.
- **Inherits From**:
    - IrCollection

**Methods**

---
#### CVariableCollection.from_llm
The `from_llm` function creates an instance of the class using LLM and a symbol list by calling another class method.
- **Inputs**:
    - `llm`: An instance of the ChatOpenAI class, representing a language model.
    - `symbols_list`: An instance of RawSymbolCollection, representing a collection of raw symbols.
- **Control Flow**:
    - The function calls the class method `from_llm_with_ir_data` with `CVariableData`, `llm`, and `symbols_list` as arguments.
    - The result of the `from_llm_with_ir_data` method call is returned.
- **Output**:
    - An instance of the class, created using the provided LLM and symbol list.



---
### CVariableData
- **Type**: `class`
- **Members**:
    - `system_prompt`: Returns a system prompt string for variable documentation.
    - `user_prompt`: Generates a user prompt string for a given symbol's variable code.
    - `child_to_ir`: Raises NotImplementedError as C variables should not have children.
    - `child_to_field_name`: Raises NotImplementedError as C variables should not have children.
- **Description**: The `CVariableData` class is a specialized class for handling C variable data within a larger system that processes and documents C code. It provides class methods to generate system and user prompts for documenting variables, and explicitly raises errors for operations related to child elements, as C variables do not have children in this context. This class inherits from `VariableData`, indicating it extends or specializes the functionality related to variable data handling.
- **Inherits From**:
    - VariableData

**Methods**

---
#### CVariableData.child_to_field_name
The function raises an error indicating that C variables should not have children.
- **Inputs**:
    - `cls`: The class from which the method is called.
    - `symbol`: An instance of RawSymbolData representing a symbol in the code.
- **Control Flow**:
    - The function immediately raises a NotImplementedError with a specific message.
- **Output**:
    - The function does not return any value as it raises an exception.


---
#### CVariableData.child_to_ir
The function raises a NotImplementedError indicating that C variables should not have children.
- **Inputs**:
    - `cls`: The class reference from which the method is called.
    - `symbol`: An instance of RawSymbolData representing a symbol in the code.
- **Control Flow**:
    - The function immediately raises a NotImplementedError with a specific message.
- **Output**:
    - The function does not return any value as it raises an exception.


---
#### CVariableData.system_prompt
The `system_prompt` function returns a predefined JSON string for documenting variables in C code.
- **Inputs**:
    - None
- **Control Flow**:
    - The function directly returns the constant `VARIABLES_FOUND_SYSTEM_PROMPT_JSON`.
- **Output**:
    - A string containing a JSON schema for documenting variables in C code.


---
#### CVariableData.user_prompt
The function generates a user prompt string containing information about a symbol, including its name and code, and optionally the full file code if available.
- **Inputs**:
    - `cls`: The class reference, typically used in class methods, but not utilized in this function.
    - `symbol`: An instance of RawSymbolData containing information about a symbol, including its name, symbol code, and optionally file code.
- **Control Flow**:
    - Initialize the user_prompt string with a predefined prompt and the symbol's name and code.
    - Check if the symbol has associated file code.
    - If file code is present, append it to the user_prompt string.
    - Return the constructed user_prompt string.
- **Output**:
    - A string containing the user prompt with the symbol's name, code, and optionally the full file code.



---
### CVariableRawSymbolCollection
- **Type**: `class`
- **Members**:
    - `data`: A dictionary mapping variable names to their corresponding RawSymbolData.
- **Description**: The CVariableRawSymbolCollection class is designed to collect and manage raw symbol data for C variables extracted from source code. It inherits from RawSymbolCollection and provides methods to populate its data through static analysis of C code, specifically by utilizing a CDriverTree to extract variable symbols. The class supports conversion of its data to a dictionary format and enforces the use of static analysis for data collection, as indicated by the NotImplementedError in the from_llm method.
- **Inherits From**:
    - RawSymbolCollection

**Methods**

---
#### CVariableRawSymbolCollection.from_llm
The `from_llm` function is a placeholder method intended to be overridden for creating an instance from a language model, but currently raises a NotImplementedError.
- **Inputs**:
    - `code`: A string representing the code to be analyzed or processed.
    - `root_rel_path`: A string representing the root relative path where the code is located.
- **Control Flow**:
    - The function immediately raises a NotImplementedError with a message indicating that static analysis should be used for C variables.
- **Output**:
    - The function does not return any value as it raises an exception.


---
#### CVariableRawSymbolCollection.from_static_analysis
The function performs static analysis on C code to extract variable symbols and returns a collection of raw symbol data or None if no variables are found.
- **Inputs**:
    - `code`: A string containing the C source code to be analyzed.
    - `root_rel_path`: A Path object representing the root relative path of the source code file.
- **Control Flow**:
    - Create a CDriverTree object from the provided code and root_rel_path.
    - Initialize an empty dictionary to store variable raw symbol data.
    - Determine if the code requires multi-prompt processing based on its size.
    - Iterate over each variable symbol extracted from the driver tree.
    - For each symbol with a non-null name, create a RawSymbolData object with various attributes including the code and path.
    - Store the RawSymbolData object in the dictionary using the symbol's name as the key.
    - Return None if no variable symbols were found, otherwise return an instance of the class with the collected data.
- **Output**:
    - Returns an instance of the class containing a dictionary of variable raw symbol data if any variables are found, otherwise returns None.


---
#### CVariableRawSymbolCollection.to_dict
The `to_dict` function returns the `data` attribute of the instance as a dictionary.
- **Inputs**:
    - None
- **Control Flow**:
    - The function directly returns the `data` attribute of the instance without any additional processing.
- **Output**:
    - A dictionary where the keys are strings and the values are `RawSymbolData` objects.



