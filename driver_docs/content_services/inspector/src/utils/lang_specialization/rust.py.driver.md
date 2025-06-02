# Purpose
This Python source code file is designed to facilitate the extraction and documentation of Rust code components, such as macros, traits, data structures, methods, functions, and variables. It leverages the Pydantic library for data validation and management, and it uses a combination of static analysis and language model (LLM) prompts to generate detailed documentation for Rust code. The file defines several classes, each corresponding to a specific Rust code component, such as `RustMacroData`, `RustTraitData`, `RustDataStructureData`, and others. These classes are responsible for generating system and user prompts, handling the conversion of raw symbol data into structured documentation, and managing collections of these components.

The file also includes a set of constants that categorize different types of Rust code elements, such as data structures, functions, methods, variables, macros, traits, and implementations. The primary functionality of this code is to parse Rust source code using ctags, extract relevant symbols, and then use predefined JSON schemas to document these symbols. This documentation process is facilitated by the `ChatOpenAI` model, which generates human-readable descriptions based on the extracted symbols. The code is structured to be part of a larger system, likely intended for use in a documentation generation tool or a code analysis platform, where it can be imported and utilized to automate the documentation of Rust codebases.
# Imports and Dependencies

---
- `pathlib`
- `typing`
- `pydantic`
- `utils.codemap_ctags`
- `utils.models`
- `.ir_common`
- `.symbol_common`


# Global Variables

---
### DATA_STRUCTURES_FOUND_SYSTEM_PROMPT_JSON 
- **Type**: `str`
- **Description**: The variable `DATA_STRUCTURES_FOUND_SYSTEM_PROMPT_JSON` is a string containing a JSON schema template. This template is used to guide the documentation of Rust data structures, specifying the format and content required for the documentation.
- **Use**: This variable is used as a template for generating documentation for Rust data structures, ensuring consistency and completeness in the documentation process.


---
### DATA_STRUCTURES_FOUND_USER_PROMPT 
- **Type**: `str`
- **Description**: The variable `DATA_STRUCTURES_FOUND_USER_PROMPT` is a string that contains a template for a user prompt. This prompt is used to request a summary of a data structure in the provided code. It guides the user to provide a detailed description of the data structure, matching the complexity of the structure.
- **Use**: This variable is used to generate a user prompt for summarizing data structures in code.


---
### FUNCTIONS_FOUND_SYSTEM_PROMPT_JSON 
- **Type**: `string`
- **Description**: The `FUNCTIONS_FOUND_SYSTEM_PROMPT_JSON` is a string variable that contains a JSON schema template. This template is used to guide the documentation of functions written in Rust, specifying the format for describing a function's purpose, inputs, control flow, and output.
- **Use**: This variable is used to provide a structured format for documenting Rust functions.


---
### FUNCTIONS_FOUND_USER_PROMPT 
- **Type**: `str`
- **Description**: The `FUNCTIONS_FOUND_USER_PROMPT` is a multi-line string variable that contains a template for summarizing functions in Rust code. It provides guidelines on how to describe the inputs, control flow, logic, and output of a function, emphasizing the need for detail proportional to the complexity of the function.
- **Use**: This variable is used as a prompt template for generating documentation or summaries of Rust functions.


---
### MACROS_FOUND_SYSTEM_PROMPT_JSON 
- **Type**: `string`
- **Description**: The variable `MACROS_FOUND_SYSTEM_PROMPT_JSON` is a string that contains a detailed system prompt for documenting Rust macros. It provides instructions on how to describe a macro, including its type, description, logic, and usage, using a specific JSON schema.
- **Use**: This variable is used to guide the documentation process for Rust macros by providing a structured prompt.


---
### MACROS_FOUND_USER_PROMPT 
- **Type**: `str`
- **Description**: `MACROS_FOUND_USER_PROMPT` is a string variable that contains a prompt message intended for user interaction. It is used to instruct the user to summarize a data structure, specifically a macro, in the provided code. The prompt guides the user to provide a detailed description based on the complexity of the data structure.
- **Use**: This variable is used to provide a user prompt for summarizing macros in code documentation.


---
### METHODS_FOUND_SYSTEM_PROMPT_JSON 
- **Type**: `str`
- **Description**: `METHODS_FOUND_SYSTEM_PROMPT_JSON` is a string variable that contains a JSON schema template for documenting method implementations in Rust. This template guides the documentation process by specifying the structure and content required for describing methods, including inputs, control flow, and output.
- **Use**: This variable is used to provide a structured format for documenting Rust method implementations.


---
### METHODS_FOUND_USER_PROMPT 
- **Type**: `str`
- **Description**: `METHODS_FOUND_USER_PROMPT` is a string variable that contains a template prompt for summarizing methods in Rust code. It provides guidance on how to describe the inputs, control flow, logic, and output of a method, emphasizing the need for detail proportional to the method's complexity.
- **Use**: This variable is used to generate prompts for documenting Rust methods, ensuring consistent and comprehensive descriptions.


---
### RUST_DATA_STRUCTURE 
- **Type**: `set`
- **Description**: `RUST_DATA_STRUCTURE` is a set containing the strings 'enum' and 'struct'. This set is used to categorize and identify Rust data structures within the codebase.
- **Use**: This variable is used to identify and categorize Rust data structures such as enums and structs.


---
### RUST_FUNCTIONS 
- **Type**: `set`
- **Description**: RUST_FUNCTIONS is a global variable defined as a set containing the string 'function'. This set is used to categorize or identify Rust language constructs that are considered functions.
- **Use**: This variable is used to identify and categorize Rust functions in the code.


---
### RUST_IMPLEMENTATIONS 
- **Type**: `set`
- **Description**: `RUST_IMPLEMENTATIONS` is a set containing a single string element, 'implementation'. This set is used to categorize or identify Rust code elements that are implementations, likely referring to implementation blocks in Rust.
- **Use**: This variable is used to identify and categorize Rust implementation blocks in the code.


---
### RUST_MACROS 
- **Type**: `set`
- **Description**: `RUST_MACROS` is a global variable defined as a set containing a single string element, 'macro'. This set is used to categorize or identify Rust language constructs that are macros.
- **Use**: This variable is used to identify and categorize Rust macros in the code.


---
### RUST_METHODS 
- **Type**: `set`
- **Description**: `RUST_METHODS` is a set containing a single string element, 'method'. This set is used to categorize or identify Rust programming language constructs that are considered methods.
- **Use**: This variable is used to classify or filter symbols that are methods in Rust code analysis.


---
### RUST_TRAITS 
- **Type**: `set`
- **Description**: The `RUST_TRAITS` variable is a set containing a single string element, 'interface'. This set is used to categorize or identify Rust traits within the context of the code.
- **Use**: This variable is used to identify and categorize Rust traits in the codebase.


---
### RUST_VARIABLES 
- **Type**: `set`
- **Description**: `RUST_VARIABLES` is a set containing string elements that represent different types of variables in Rust, specifically 'constant' and 'variable'. This set is part of a collection of sets that categorize various Rust language constructs.
- **Use**: This variable is used to identify and categorize Rust variables during code analysis or processing.


---
### SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT 
- **Type**: `str`
- **Description**: `SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT` is a string variable that contains a detailed prompt for explaining the purpose of a large source code file. It guides the user to provide a comprehensive explanation of the file's purpose, focusing on aspects such as functionality, technical components, and the nature of the code.
- **Use**: This variable is used to instruct users on how to describe the purpose of large source code files in a detailed manner.


---
### SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_RUST 
- **Type**: `str`
- **Description**: This variable is a multi-line string that serves as a system prompt for a large-scale Rust programming documentation task. It provides instructions for generating detailed documentation for Rust code, emphasizing the explanation of technical details and the purpose of software components.
- **Use**: This variable is used as a prompt template for generating detailed documentation for large Rust codebases.


---
### SOURCE_CODE_SMALL_PURPOSE_USER_PROMPT 
- **Type**: `str`
- **Description**: This variable is a string that contains a prompt for users to explain the purpose of a small source code file. It guides users to provide a concise explanation of the file's purpose in 3 to 5 sentences, focusing on the scope and type of code.
- **Use**: This variable is used to instruct users on how to summarize the purpose of small source code files.


---
### SOURCE_CODE_SMALL_SYSTEM_PROMPT_GENERAL_RUST 
- **Type**: `str`
- **Description**: This variable is a string that serves as a system prompt for a Rust programming documentation expert. It provides guidance on how to write documentation for small and simple Rust source code files, emphasizing clarity and conciseness.
- **Use**: This variable is used to provide a template or guideline for generating documentation for small Rust source code files.


---
### TRAITS_FOUND_SYSTEM_PROMPT_JSON 
- **Type**: `string`
- **Description**: The `TRAITS_FOUND_SYSTEM_PROMPT_JSON` variable is a string that contains a JSON schema template for documenting Rust traits. It provides a structured format for describing traits, including their trait bounds, generic types, methods, and a description.
- **Use**: This variable is used to guide the documentation process for Rust traits by providing a consistent schema.


---
### TRAITS_FOUND_USER_PROMPT 
- **Type**: `string`
- **Description**: TRAITS_FOUND_USER_PROMPT is a string variable that contains a template prompt for summarizing a Rust trait in the provided code. It guides the user to provide a detailed description of the trait, focusing on its complexity and the number of methods, generics, and trait bounds it contains.
- **Use**: This variable is used to generate a user prompt for documenting Rust traits.


---
### VARIABLES_FOUND_SYSTEM_PROMPT_JSON 
- **Type**: `str`
- **Description**: `VARIABLES_FOUND_SYSTEM_PROMPT_JSON` is a string variable that contains a JSON-formatted prompt. This prompt is designed to instruct a system on how to document global variables and constants in Python code. It provides a schema for describing the type, description, and use of a variable.
- **Use**: This variable is used to provide a structured prompt for documenting Python global variables and constants.


---
### VARIABLES_FOUND_USER_PROMPT 
- **Type**: `string`
- **Description**: `VARIABLES_FOUND_USER_PROMPT` is a string variable that contains a template for a user prompt. This prompt is used to instruct the user to summarize a global variable or constant in the provided code. The prompt includes guidelines on how to describe the variable, emphasizing the need for detail that matches the complexity of the variable.
- **Use**: This variable is used to generate a user prompt for summarizing global variables or constants in Python code.


---
### _supported_child_ordering 
- **Type**: `list[str]`
- **Description**: The `_supported_child_ordering` variable is a private attribute of the `RustDataStructureData` class. It is a list of strings that specifies the order in which child elements, such as methods and nested data structures, are supported within a Rust data structure.
- **Use**: This variable is used to define the order of child elements in a Rust data structure.


# Classes

---
### RustDataStructureCollection 
- **Type**: `class`
- **Members**:
    - `data`: A dictionary mapping strings to either a single RustDataStructureData instance or a list of such instances.
- **Description**: The RustDataStructureCollection class is a specialized collection class that inherits from IrCollection. It is designed to manage and organize Rust data structures, specifically instances of RustDataStructureData. The class provides a class method, from_llm, which facilitates the creation of a RustDataStructureCollection instance by leveraging language model data and a collection of raw symbols. This class is part of a larger system for analyzing and documenting Rust code, focusing on the organization and representation of data structures within the code.
- **Inherits From**:
    - IrCollection

**Methods**

---
#### RustDataStructureCollection.from_llm
The `from_llm` function creates an instance of the class by invoking the `from_llm_with_ir_data` method with `RustDataStructureData`, `llm`, and `symbols_list` as arguments.
- **Inputs**:
    - `cls`: The class on which this method is called, typically a subclass of `IrCollection`.
    - `llm`: An instance of `ChatOpenAI`, representing a language model used for processing.
    - `symbols_list`: An instance of `RawSymbolCollection`, representing a collection of raw symbols to be processed.
- **Control Flow**:
    - The function calls `cls.from_llm_with_ir_data` with `RustDataStructureData`, `llm`, and `symbols_list` as arguments.
    - The result of the `from_llm_with_ir_data` call is returned as the output of the function.
- **Output**:
    - An instance of the class `cls`, initialized using the `from_llm_with_ir_data` method with the provided arguments.



---
### RustDataStructureData 
- **Type**: `class`
- **Members**:
    - `type`: Holds the type information of the Rust data structure.
    - `members`: Contains a list of members or fields of the Rust data structure.
    - `description`: Provides a textual description of the Rust data structure.
    - `trait_bounds`: Lists the trait bounds associated with the Rust data structure.
    - `_supported_child_ordering`: Defines the order of supported child elements like methods and nested data structures.
- **Description**: The `RustDataStructureData` class is designed to encapsulate metadata about Rust data structures, such as enums or structs, within an intermediate representation (IR) framework. It includes attributes for specifying the type, members, description, and trait bounds of the data structure. The class also provides class methods for generating system and user prompts related to data structures, and for mapping child symbols to their respective IR types or field names. This class is part of a larger system for analyzing and documenting Rust code, particularly focusing on data structures and their components.
- **Inherits From**:
    - IrData

**Methods**

---
#### RustDataStructureData.child_to_field_name
The `child_to_field_name` function maps a `RawSymbolData` object's `symbol_kind` to a corresponding `ScopeRelation` value.
- **Inputs**:
    - `cls`: The class reference, typically used in class methods.
    - `child`: An instance of `RawSymbolData` representing a symbol with a specific kind.
- **Control Flow**:
    - A dictionary `mapping` is defined to map `SymbolKind` values to `ScopeRelation` values.
    - The function attempts to retrieve the `ScopeRelation` value from the `mapping` dictionary using the `symbol_kind` of the `child` argument.
- **Output**:
    - The function returns a `ScopeRelation` value corresponding to the `symbol_kind` of the `child`, or `None` if no mapping exists.


---
#### RustDataStructureData.child_to_ir
The `child_to_ir` function maps a `RawSymbolData`'s `symbol_kind` to a corresponding `IrData` type or returns `None` if no mapping exists.
- **Inputs**:
    - `cls`: The class reference, typically used in class methods to access class attributes or methods.
    - `symbol`: An instance of `RawSymbolData` representing a symbol with a `symbol_kind` attribute that needs to be mapped to an `IrData` type.
- **Control Flow**:
    - A dictionary `mapping` is defined to associate `SymbolKind` values with corresponding `IrData` types.
    - The function attempts to retrieve the `IrData` type from the `mapping` dictionary using the `symbol.symbol_kind` as the key.
    - If the `symbol_kind` is found in the dictionary, the corresponding `IrData` type is returned; otherwise, `None` is returned.
- **Output**:
    - The function returns a type of `IrData` corresponding to the `symbol_kind` of the input `symbol`, or `None` if no mapping exists.


---
#### RustDataStructureData.default_instance
The `default_instance` function creates and returns a default instance of the class with predefined values for its attributes.
- **Inputs**:
    - `cls`: The class for which a default instance is to be created.
- **Control Flow**:
    - The function calls the class constructor `cls()` with specific default values for its attributes.
    - The `type` attribute is set to an instance of `FieldNameWithBackTickContent` with content 'N/A'.
    - The `members` attribute is set to an instance of `ListedBacktickNameRawContentNoNone` with an empty list as content.
    - The `description` attribute is set to an instance of `FieldNameWithRawContent` with content 'Implemented elsewhere'.
    - The `trait_bounds` attribute is set to an instance of `ListedRawContentNoNone` with an empty list as content.
- **Output**:
    - Returns an instance of the class `cls` with default values for its attributes.


---
#### RustDataStructureData.system_prompt
The `system_prompt` function returns a predefined JSON string that serves as a system prompt for documenting Rust data structures.
- **Inputs**:
    - None
- **Control Flow**:
    - The function directly returns the constant `DATA_STRUCTURES_FOUND_SYSTEM_PROMPT_JSON`.
- **Output**:
    - The output is a string containing a JSON schema for documenting Rust data structures.


---
#### RustDataStructureData.user_prompt
The `user_prompt` function generates a user prompt string based on the provided `RawSymbolData` object, including its name and associated code.
- **Inputs**:
    - `cls`: The class method decorator indicating that this method is a class method.
    - `symbol`: An instance of `RawSymbolData` containing the symbol's name and code information.
- **Control Flow**:
    - Initialize `user_prompt` with a predefined string `DATA_STRUCTURES_FOUND_USER_PROMPT` concatenated with the symbol's name.
    - Check if `symbol.file_code` is available; if so, append it to `user_prompt` under a 'Code' section.
    - If `symbol.file_code` is not available, append `symbol.symbol_code` to `user_prompt` under a 'Code' section.
    - Return the constructed `user_prompt` string.
- **Output**:
    - A string that includes the symbol's name and its associated code, formatted as a user prompt.



---
### RustDataStructureRawSymbolCollection 
- **Type**: `class`
- **Members**:
    - `data`: A dictionary mapping symbol names to RawSymbolData or lists of RawSymbolData.
- **Description**: The `RustDataStructureRawSymbolCollection` class is a specialized collection for handling raw symbol data related to Rust data structures. It extends the `RawSymbolCollection` class and provides methods for constructing instances from static analysis of Rust code. The class focuses on extracting and organizing symbols related to Rust data structures and their methods, using ctags for symbol extraction. It includes logic to handle method overloading and nested data structures, ensuring that all relevant symbols are captured and structured appropriately.
- **Inherits From**:
    - RawSymbolCollection

**Methods**

---
#### RustDataStructureRawSymbolCollection.from_llm
The `from_llm` function raises a NotImplementedError indicating that static analysis should be used for Rust classes.
- **Inputs**:
    - `cls`: The class on which this class method is called.
    - `code`: A string representing the code to be analyzed.
    - `root_rel_path`: A string representing the root relative path for the code.
- **Control Flow**:
    - The function immediately raises a NotImplementedError with a specific message.
- **Output**:
    - The function does not return any output as it raises an exception.


---
#### RustDataStructureRawSymbolCollection.from_static_analysis
The `from_static_analysis` function performs static analysis on Rust code to extract and organize symbols related to data structures and methods using ctags.
- **Inputs**:
    - `code`: A string containing the Rust source code to be analyzed.
    - `root_rel_path`: A Path object representing the root relative path of the file being analyzed.
- **Control Flow**:
    - Determine if the code requires multi-prompt analysis using `code_requires_multi_prompt`.
    - Extract symbols from the code using `extract_symbols_w_ctags`.
    - Initialize dictionaries for global method counts and raw symbol data for data structures.
    - Iterate over the extracted symbols to count method occurrences and create raw symbol data for data structures.
    - For each symbol, check if it is a method within an implementation scope and update the data structure's raw symbol data accordingly.
    - Check for nested data structures and update the raw symbol data with nested data structure information.
    - Return an instance of the class with the collected data structure raw symbol data, or None if no data structures were found.
- **Output**:
    - An instance of the class containing the data structure raw symbol data, or None if no data structures were found.


---
#### RustDataStructureRawSymbolCollection.to_dict
The `to_dict` function returns the `data` attribute of the instance as a dictionary.
- **Inputs**:
    - `self`: Represents the instance of the class from which the method is called.
- **Control Flow**:
    - The function directly returns the `data` attribute of the instance without any additional processing.
- **Output**:
    - A dictionary where the keys are strings and the values are of type `RawSymbolData`.



---
### RustFnCollection 
- **Type**: `class`
- **Members**:
    - `data`: A dictionary mapping string keys to either a single RustFnData instance or a list of RustFnData instances.
- **Description**: The `RustFnCollection` class is a specialized collection class that inherits from `IrCollection`. It is designed to manage a collection of Rust function data, represented by the `RustFnData` class. The class provides a class method `from_llm` which facilitates the creation of a `RustFnCollection` instance from a language model and a list of raw symbols, leveraging the `from_llm_with_ir_data` method to populate the collection with `RustFnData` instances.
- **Inherits From**:
    - IrCollection

**Methods**

---
#### RustFnCollection.from_llm
The `from_llm` function creates an instance of the class by invoking the `from_llm_with_ir_data` method with `RustFnData`, `llm`, and `symbols_list` as arguments.
- **Inputs**:
    - `cls`: The class on which this method is called, typically a subclass of `IrCollection`.
    - `llm`: An instance of `ChatOpenAI`, representing a language model used for processing or generating data.
    - `symbols_list`: An instance of `RawSymbolCollection`, representing a collection of raw symbols to be processed.
- **Control Flow**:
    - The function calls `cls.from_llm_with_ir_data` with `RustFnData`, `llm`, and `symbols_list` as arguments.
    - The result of the `from_llm_with_ir_data` call is returned as the output of the function.
- **Output**:
    - An instance of the class `cls`, initialized using the `from_llm_with_ir_data` method with the provided arguments.



---
### RustFnData 
- **Type**: `class`
- **Members**:
    - `system_prompt`: Returns a system prompt string for documenting Rust functions.
    - `user_prompt`: Generates a user prompt string based on the provided symbol data.
    - `child_to_ir`: Raises a NotImplementedError indicating functions should not have children.
    - `child_to_field_name`: Raises a NotImplementedError indicating functions should not have children.
- **Description**: The `RustFnData` class is a specialized subclass of `FnData` designed to handle the documentation of Rust functions. It provides class methods to generate system and user prompts for documenting functions, ensuring that the documentation process is tailored to Rust's syntax and conventions. The class explicitly raises errors for methods related to child elements, as functions do not have children in this context.
- **Inherits From**:
    - FnData

**Methods**

---
#### RustFnData.child_to_field_name
The function `child_to_field_name` raises a `NotImplementedError` indicating that functions should not have children.
- **Inputs**:
    - `cls`: The class to which this method belongs.
    - `child`: An instance of `RawSymbolData` representing a child symbol.
- **Control Flow**:
    - The function immediately raises a `NotImplementedError` with a specific message.
- **Output**:
    - The function does not return any value as it raises an exception.


---
#### RustFnData.child_to_ir
The `child_to_ir` function raises a `NotImplementedError` indicating that functions should not have children.
- **Inputs**:
    - `cls`: The class on which this class method is called.
    - `symbol`: An instance of `RawSymbolData` representing the symbol data to be processed.
- **Control Flow**:
    - The function immediately raises a `NotImplementedError` with the message 'Functions should not have children'.
- **Output**:
    - The function does not return any value as it raises an exception.


---
#### RustFnData.system_prompt
The `system_prompt` function returns a predefined JSON string used as a system prompt for documenting Rust functions.
- **Inputs**:
    - None
- **Control Flow**:
    - The function directly returns the constant `FUNCTIONS_FOUND_SYSTEM_PROMPT_JSON`.
- **Output**:
    - A string containing the JSON schema for documenting Rust functions.


---
#### RustFnData.user_prompt
The `user_prompt` function generates a user prompt string based on the provided `RawSymbolData` object, including its name and associated code.
- **Inputs**:
    - `cls`: The class reference, typically used in class methods.
    - `symbol`: An instance of `RawSymbolData` containing information about a symbol, including its name and code.
- **Control Flow**:
    - Initialize the `user_prompt` string with a predefined prompt and the symbol's name.
    - Check if the `symbol` has `file_code`; if so, append it to the `user_prompt` string.
    - If `file_code` is not present, append `symbol_code` to the `user_prompt` string instead.
    - Return the constructed `user_prompt` string.
- **Output**:
    - A string representing the user prompt, which includes the symbol's name and its associated code.



---
### RustFnRawSymbolCollection 
- **Type**: `class`
- **Members**:
    - `data`: A dictionary mapping function names to RawSymbolData or a list of RawSymbolData.
- **Description**: The `RustFnRawSymbolCollection` class is designed to collect and manage raw symbol data specifically for Rust functions. It inherits from `RawSymbolCollection` and provides methods to populate its data through static analysis of Rust code. The class includes a method `from_static_analysis` that extracts function symbols from the provided code using ctags, filtering out anonymous functions, and stores them in a dictionary. The class also provides a `to_dict` method to return the stored data in dictionary form. It does not support creation from LLM (Language Model) analysis, as indicated by the `from_llm` method raising a `NotImplementedError`.
- **Inherits From**:
    - RawSymbolCollection

**Methods**

---
#### RustFnRawSymbolCollection.from_llm
The `from_llm` function raises a NotImplementedError indicating that static analysis should be used for Rust functions instead of this method.
- **Inputs**:
    - `cls`: The class on which this class method is called.
    - `code`: A string representing the code to be analyzed.
    - `root_rel_path`: A string representing the root relative path of the code file.
- **Control Flow**:
    - The function immediately raises a NotImplementedError with a specific message.
- **Output**:
    - The function does not return any output as it raises an exception.


---
#### RustFnRawSymbolCollection.from_static_analysis
The `from_static_analysis` function performs static analysis on Rust code to extract function symbols and create a collection of raw symbol data.
- **Inputs**:
    - `cls`: The class type that this method is a part of, typically used to create an instance of the class.
    - `code`: A string containing the Rust source code to be analyzed.
    - `root_rel_path`: A Path object representing the root relative path of the file being analyzed.
- **Control Flow**:
    - Determine if the code requires multi-prompt analysis using `code_requires_multi_prompt` function.
    - Extract symbols from the code using `extract_symbols_w_ctags` function with the provided root relative path and code.
    - Initialize an empty dictionary `fn_raw_symbol_data` to store raw symbol data for functions.
    - Iterate over each symbol extracted from the code.
    - For each symbol, check if its kind is in `RUST_FUNCTIONS` and its name does not start with '__anon'.
    - If the symbol meets the criteria, create raw symbol data using `create_raw_symbol_via_ctags` and store it in `fn_raw_symbol_data` with the symbol's name as the key.
    - Check if `fn_raw_symbol_data` is empty; if it is, set `output` to None, otherwise create an instance of `cls` with `fn_raw_symbol_data` as data.
    - Return the `output`.
- **Output**:
    - Returns an instance of the class `cls` containing the raw symbol data if any functions are found, otherwise returns None.


---
#### RustFnRawSymbolCollection.to_dict
The `to_dict` function returns the `data` attribute of the instance as a dictionary.
- **Inputs**:
    - `self`: Represents the instance of the class containing the `data` attribute.
- **Control Flow**:
    - The function directly returns the `data` attribute of the instance without any additional processing.
- **Output**:
    - A dictionary where keys are strings and values are of type `RawSymbolData`.



---
### RustMacroCollection 
- **Type**: `class`
- **Members**:
    - `data`: A dictionary mapping strings to either a single RustMacroData instance or a list of RustMacroData instances.
- **Description**: The RustMacroCollection class is a specialized collection class that inherits from IrCollection and is designed to manage a collection of RustMacroData objects. It provides a class method, from_llm, which facilitates the creation of a RustMacroCollection instance by leveraging language model data and a list of raw symbols. This class is part of a system that processes and organizes Rust macro data, likely for documentation or analysis purposes.
- **Inherits From**:
    - IrCollection

**Methods**

---
#### RustMacroCollection.from_llm
The `from_llm` function creates an instance of the class by invoking the `from_llm_with_ir_data` method with `RustMacroData`, `llm`, and `symbols_list` as arguments.
- **Inputs**:
    - `cls`: The class on which this method is called, typically a subclass of `RustMacroCollection`.
    - `llm`: An instance of `ChatOpenAI`, representing a language model used for processing.
    - `symbols_list`: An instance of `RawSymbolCollection`, representing a collection of raw symbols to be processed.
- **Control Flow**:
    - The function calls `cls.from_llm_with_ir_data` with `RustMacroData`, `llm`, and `symbols_list` as arguments.
    - The result of the `from_llm_with_ir_data` call is returned as the output of the function.
- **Output**:
    - An instance of the class `cls`, initialized using the `from_llm_with_ir_data` method with the provided arguments.



---
### RustMacroData 
- **Type**: `class`
- **Members**:
    - `type`: Holds the type information for the Rust macro.
    - `description`: Contains a description of the Rust macro.
    - `logic`: Stores the logic or operations associated with the Rust macro.
    - `use`: Describes how the Rust macro is used.
- **Description**: The `RustMacroData` class is designed to encapsulate information about Rust macros, including their type, description, logic, and usage. It provides class methods to generate system and user prompts for documenting macros, and it enforces that macros should not have children by raising `NotImplementedError` for related methods. The class also includes a method to create a default instance with empty or default values for its attributes.
- **Inherits From**:
    - IrData

**Methods**

---
#### RustMacroData.child_to_field_name
The function `child_to_field_name` raises a `NotImplementedError` indicating that macros should not have children.
- **Inputs**:
    - `cls`: The class reference from which the method is called.
    - `child`: An instance of `RawSymbolData` representing a child symbol.
- **Control Flow**:
    - The function immediately raises a `NotImplementedError` with a specific message.
- **Output**:
    - The function does not return any value as it raises an exception.


---
#### RustMacroData.child_to_ir
The `child_to_ir` function raises a NotImplementedError indicating that macros should not have children.
- **Inputs**:
    - `cls`: The class method's implicit first argument, representing the class itself.
    - `symbol`: An instance of RawSymbolData, representing the symbol data to be processed.
- **Control Flow**:
    - The function immediately raises a NotImplementedError with a specific message.
- **Output**:
    - The function does not return any value as it raises an exception.


---
#### RustMacroData.default_instance
The `default_instance` function creates and returns a default instance of the class with empty or default values for its attributes.
- **Inputs**:
    - `cls`: The class for which a default instance is to be created.
- **Control Flow**:
    - The function calls the class constructor `cls` with specific default values for its attributes.
    - The `type` attribute is set to an instance of `FieldNameWithBackTickContent` with an empty string as content.
    - The `description` attribute is set to an instance of `FieldNameWithRawContent` with an empty string as content.
    - The `logic` attribute is set to an instance of `ListedRawContentNoNone` with an empty list as content.
    - The `use` attribute is set to an instance of `FieldNameWithRawContent` with an empty string as content.
- **Output**:
    - A new instance of the class `cls` with default values for its attributes.


---
#### RustMacroData.system_prompt
The `system_prompt` function returns a predefined JSON string used as a system prompt for documenting Rust macros.
- **Inputs**:
    - None
- **Control Flow**:
    - The function directly returns the constant `MACROS_FOUND_SYSTEM_PROMPT_JSON`.
- **Output**:
    - A string containing the JSON schema for documenting Rust macros.


---
#### RustMacroData.user_prompt
The `user_prompt` function generates a user prompt string based on the provided `RawSymbolData` object, including its name and associated code.
- **Inputs**:
    - `cls`: The class reference, typically used in class methods.
    - `symbol`: An instance of `RawSymbolData` containing information about a symbol, including its name and code.
- **Control Flow**:
    - Initialize the `user_prompt` string with a predefined prompt followed by the symbol's name.
    - Check if the `symbol` has `file_code`; if true, append the file code to the `user_prompt`.
    - If `file_code` is not present, append the `symbol_code` to the `user_prompt`.
- **Output**:
    - Returns a string that combines a predefined prompt with the symbol's name and its associated code.



---
### RustMacroRawSymbolCollection 
- **Type**: `class`
- **Members**:
    - `data`: A dictionary mapping string keys to either a single RawSymbolData or a list of RawSymbolData.
- **Description**: The RustMacroRawSymbolCollection class is designed to collect and manage raw symbol data specifically for Rust macros. It inherits from RawSymbolCollection and provides methods to populate the collection using static analysis of Rust code. The class includes a class method, from_static_analysis, which utilizes a default ctags analysis to extract macro symbols from the provided code and path. The class also includes a method to convert the collected data into a dictionary format. This class is specialized for handling Rust macro symbols and does not support LLM-based symbol extraction.
- **Inherits From**:
    - RawSymbolCollection

**Methods**

---
#### RustMacroRawSymbolCollection.from_llm
The `from_llm` function raises a NotImplementedError indicating that static analysis should be used for Rust functions.
- **Inputs**:
    - `cls`: The class on which this class method is called.
    - `code`: A string representing the code to be analyzed.
    - `root_rel_path`: A string representing the root relative path for the code.
- **Control Flow**:
    - The function immediately raises a NotImplementedError with a specific message.
- **Output**:
    - The function does not return any output as it raises an exception.


---
#### RustMacroRawSymbolCollection.from_static_analysis
The `from_static_analysis` function performs a static analysis on Rust code to extract and return a collection of raw symbol data for Rust macros.
- **Inputs**:
    - `code`: A string containing the Rust source code to be analyzed.
    - `root_rel_path`: A Path object representing the root relative path of the source code file.
- **Control Flow**:
    - The function calls `default_ctags_analysis` with specific parameters to perform the analysis.
    - It specifies the collection class, code, root relative path, symbol kind, ctags kinds, delimiter, and symbol padding options.
    - The analysis focuses on extracting symbols of kind 'CALLABLE' and specifically 'RUST_MACROS'.
- **Output**:
    - The function returns an instance of the class specified by `collection_cls`, containing the extracted raw symbol data for Rust macros.


---
#### RustMacroRawSymbolCollection.to_dict
The `to_dict` function returns the `data` attribute of the instance as a dictionary.
- **Inputs**:
    - `self`: Represents the instance of the class from which the method is called.
- **Control Flow**:
    - The function directly returns the `data` attribute of the instance.
- **Output**:
    - A dictionary where keys are strings and values are of type `RawSymbolData`.



---
### RustMethodData 
- **Type**: `class`
- **Description**: The `RustMethodData` class is a specialized subclass of `FnData` designed to handle method-related data in Rust code. It provides class methods for generating system and user prompts specific to methods, and it explicitly raises `NotImplementedError` for methods related to child handling, indicating that methods should not have children. This class is part of a larger framework for analyzing and documenting Rust code, focusing on method implementations.
- **Inherits From**:
    - FnData

**Methods**

---
#### RustMethodData.child_to_field_name
The `child_to_field_name` function raises a `NotImplementedError` indicating that methods should not have children.
- **Inputs**:
    - `cls`: The class on which this method is called, typically a class method.
    - `child`: An instance of `RawSymbolData` representing a child symbol.
- **Control Flow**:
    - The function immediately raises a `NotImplementedError` with a specific message.
- **Output**:
    - The function does not return any value as it raises an exception.


---
#### RustMethodData.child_to_ir
The `child_to_ir` function raises a `NotImplementedError` indicating that methods should not have children.
- **Inputs**:
    - `cls`: The class on which this class method is called.
    - `symbol`: An instance of `RawSymbolData` representing a symbol to be converted to an intermediate representation (IR).
- **Control Flow**:
    - The function immediately raises a `NotImplementedError` with the message 'Methods should not have children'.
- **Output**:
    - The function does not return any value as it raises an exception.


---
#### RustMethodData.system_prompt
The `system_prompt` function returns a predefined JSON string for documenting Rust method implementations.
- **Inputs**:
    - None
- **Control Flow**:
    - The function directly returns the constant `METHODS_FOUND_SYSTEM_PROMPT_JSON`.
- **Output**:
    - A string containing JSON schema for documenting Rust method implementations.


---
#### RustMethodData.user_prompt
The `user_prompt` function generates a user prompt string based on the provided `RawSymbolData` object, including its name and associated code.
- **Inputs**:
    - `cls`: The class reference, typically used in class methods.
    - `symbol`: An instance of `RawSymbolData` containing information about a symbol, including its name and code.
- **Control Flow**:
    - Initialize the `user_prompt` string with a predefined prompt message concatenated with the symbol's name.
    - Check if the `symbol` has `file_code`; if so, append it to the `user_prompt` string under a 'Code' section.
    - If `file_code` is not present, append `symbol_code` to the `user_prompt` string under a 'Code' section.
    - Return the constructed `user_prompt` string.
- **Output**:
    - A string containing the user prompt with the symbol's name and code.



---
### RustTraitCollection 
- **Type**: `class`
- **Members**:
    - `data`: A dictionary mapping strings to either a single RustTraitData instance or a list of RustTraitData instances.
- **Description**: The RustTraitCollection class is a specialized collection class that inherits from IrCollection and is designed to manage a collection of RustTraitData objects. It provides a class method, from_llm, which facilitates the creation of a RustTraitCollection instance by leveraging language model data and a list of raw symbols. This class is part of a system that processes and organizes Rust trait data, likely for documentation or analysis purposes.
- **Inherits From**:
    - IrCollection

**Methods**

---
#### RustTraitCollection.from_llm
The `from_llm` function creates an instance of the class by invoking the `from_llm_with_ir_data` method with `RustTraitData`, `llm`, and `symbols_list` as arguments.
- **Inputs**:
    - `cls`: The class on which this method is called, typically a subclass of `IrCollection`.
    - `llm`: An instance of `ChatOpenAI`, which is likely used for language model processing.
    - `symbols_list`: An instance of `RawSymbolCollection`, which contains a collection of raw symbols to be processed.
- **Control Flow**:
    - The function calls `cls.from_llm_with_ir_data` with `RustTraitData`, `llm`, and `symbols_list` as arguments.
    - The result of the `from_llm_with_ir_data` call is returned as the output of the function.
- **Output**:
    - An instance of the class `cls`, initialized using the `from_llm_with_ir_data` method with the provided arguments.



---
### RustTraitData 
- **Type**: `class`
- **Members**:
    - `trait_bounds`: Holds a list of trait bounds associated with the Rust trait.
    - `generic_types`: Contains a list of generic types associated with the Rust trait.
    - `methods`: Stores a list of methods defined for the Rust trait.
    - `description`: Provides a textual description of the Rust trait.
- **Description**: The `RustTraitData` class is designed to encapsulate information about Rust traits, including their trait bounds, generic types, and methods. It provides class methods to generate system and user prompts for documenting these traits, and it ensures that traits do not have children by raising `NotImplementedError` for related methods. The class also includes a method to create a default instance with empty or default values for its attributes.
- **Inherits From**:
    - IrData

**Methods**

---
#### RustTraitData.child_to_field_name
The function `child_to_field_name` raises a `NotImplementedError` indicating that traits should not have children.
- **Inputs**:
    - `cls`: The class reference, typically used in class methods.
    - `child`: An instance of `RawSymbolData` representing a child symbol.
- **Control Flow**:
    - The function immediately raises a `NotImplementedError` with the message 'Traits should not have children'.
- **Output**:
    - The function does not return any value as it raises an exception.


---
#### RustTraitData.child_to_ir
The `child_to_ir` function raises a `NotImplementedError` indicating that traits should not have children.
- **Inputs**:
    - `cls`: The class on which this method is called, typically a class method.
    - `symbol`: An instance of `RawSymbolData` representing a symbol in the code.
- **Control Flow**:
    - The function immediately raises a `NotImplementedError` with a specific message.
- **Output**:
    - The function does not return any value as it raises an exception.


---
#### RustTraitData.default_instance
The `default_instance` function creates and returns a default instance of the class with empty or default values for its attributes.
- **Inputs**:
    - `cls`: The class for which a default instance is to be created.
- **Control Flow**:
    - The function calls the class constructor `cls` with specific default values for its attributes.
    - It initializes `trait_bounds`, `generic_types`, and `methods` with empty `ListedRawContentNoNone` and `ListedBacktickNameRawContentNoNone` objects, respectively.
    - It sets `description` to an empty `FieldNameWithRawContent` object.
- **Output**:
    - A new instance of the class `cls` with default values for its attributes.


---
#### RustTraitData.system_prompt
The `system_prompt` function returns a predefined JSON string for system prompts related to traits.
- **Inputs**:
    - None
- **Control Flow**:
    - The function directly returns the constant `TRAITS_FOUND_SYSTEM_PROMPT_JSON`.
- **Output**:
    - A string containing the JSON schema for system prompts related to traits.


---
#### RustTraitData.user_prompt
The `user_prompt` function generates a user prompt string by appending the symbol's name and its associated code to a predefined prompt template.
- **Inputs**:
    - `cls`: The class method decorator, indicating that this method is a class method and `cls` refers to the class itself.
    - `symbol`: An instance of `RawSymbolData` containing information about a symbol, including its name and code.
- **Control Flow**:
    - Initialize `user_prompt` with a predefined prompt template concatenated with the symbol's name.
    - Check if `symbol.file_code` is available; if so, append it to `user_prompt` under a 'Code' section.
    - If `symbol.file_code` is not available, append `symbol.symbol_code` to `user_prompt` under a 'Code' section.
    - Return the constructed `user_prompt` string.
- **Output**:
    - A string containing the user prompt with the symbol's name and code.



---
### RustTraitsRawSymbolCollection 
- **Type**: `class`
- **Members**:
    - `data`: A dictionary mapping string keys to either a single RawSymbolData or a list of RawSymbolData.
- **Description**: The RustTraitsRawSymbolCollection class is designed to collect and manage raw symbol data specifically for Rust traits. It inherits from RawSymbolCollection and provides methods to populate the collection using static analysis of Rust code. The class includes a class method, from_static_analysis, which utilizes a default ctags analysis to extract and organize trait symbols from the provided code and path. The to_dict method returns the collected data in dictionary form. This class is part of a system that analyzes and documents Rust code, focusing on traits as a specific kind of data structure.
- **Inherits From**:
    - RawSymbolCollection

**Methods**

---
#### RustTraitsRawSymbolCollection.from_llm
The `from_llm` function raises a `NotImplementedError` indicating that static analysis should be used for Rust functions.
- **Inputs**:
    - `cls`: The class on which this class method is called.
    - `code`: A string representing the code to be analyzed.
    - `root_rel_path`: A string representing the root relative path for the code.
- **Control Flow**:
    - The function immediately raises a `NotImplementedError` with a specific message.
- **Output**:
    - The function does not return any output as it raises an exception.


---
#### RustTraitsRawSymbolCollection.from_static_analysis
The `from_static_analysis` function performs a static analysis on Rust code to extract symbols related to data structures, specifically Rust traits, using ctags.
- **Inputs**:
    - `cls`: The class type that will be used to create an instance of the collection.
    - `code`: A string containing the Rust source code to be analyzed.
    - `root_rel_path`: A Path object representing the root relative path of the source code file.
- **Control Flow**:
    - Calls the `default_ctags_analysis` function with the provided class, code, and path.
    - Specifies the symbol kind as `SymbolKind.DATA_STRUCTURE` and ctags kinds as `RUST_TRAITS`.
    - Sets the delimiter to '::' and disables symbol padding.
- **Output**:
    - Returns an instance of the class specified by `cls`, populated with symbols extracted from the static analysis of the provided Rust code.


---
#### RustTraitsRawSymbolCollection.to_dict
The `to_dict` function returns the `data` attribute of the instance as a dictionary.
- **Inputs**:
    - `self`: Represents the instance of the class containing the `data` attribute.
- **Control Flow**:
    - The function directly returns the `data` attribute of the instance without any additional processing.
- **Output**:
    - A dictionary where keys are strings and values are `RawSymbolData` objects.



---
### RustVariableCollection 
- **Type**: `class`
- **Members**:
    - `data`: A dictionary mapping string keys to either a single RustVariableData instance or a list of such instances.
- **Description**: The RustVariableCollection class is a specialized collection class that inherits from IrCollection. It is designed to manage a collection of RustVariableData objects, which can be either individual instances or lists of instances. The class provides a class method, from_llm, which facilitates the creation of a RustVariableCollection instance by leveraging language model data and a collection of raw symbols. This class is part of a larger system for handling and processing Rust code symbols, particularly focusing on variables.
- **Inherits From**:
    - IrCollection

**Methods**

---
#### RustVariableCollection.from_llm
The `from_llm` function creates an instance of the class using data from a language model and a collection of symbols.
- **Inputs**:
    - `cls`: The class on which this method is called, typically a subclass of `IrCollection`.
    - `llm`: An instance of `ChatOpenAI`, representing the language model to be used.
    - `symbols_list`: An instance of `RawSymbolCollection`, representing a collection of symbols to be processed.
- **Control Flow**:
    - Calls the `from_llm_with_ir_data` method on the class `cls` with `RustVariableData`, `llm`, and `symbols_list` as arguments.
    - Returns the result of the `from_llm_with_ir_data` method call.
- **Output**:
    - An instance of the class `cls` initialized with data from the language model and symbols list.



---
### RustVariableData 
- **Type**: `class`
- **Members**:
    - `system_prompt`: Returns a system prompt string for documenting variables.
    - `user_prompt`: Generates a user prompt string based on the provided symbol data.
    - `child_to_ir`: Raises NotImplementedError as variables should not have children.
    - `child_to_field_name`: Raises NotImplementedError as variables should not have children.
- **Description**: The `RustVariableData` class is a specialized subclass of `VariableData` designed to handle the documentation of Rust variables. It provides class methods to generate system and user prompts for documenting variables, ensuring that the documentation process is consistent and follows a predefined format. The class explicitly raises errors for methods related to child elements, as variables do not have children in this context.
- **Inherits From**:
    - VariableData

**Methods**

---
#### RustVariableData.child_to_field_name
The `child_to_field_name` function raises a `NotImplementedError` indicating that variables should not have children.
- **Inputs**:
    - `cls`: The class reference, typically used in class methods.
    - `child`: An instance of `RawSymbolData` representing a child symbol.
- **Control Flow**:
    - The function immediately raises a `NotImplementedError` with a specific message.
- **Output**:
    - The function does not return any value as it raises an exception.


---
#### RustVariableData.child_to_ir
The `child_to_ir` function raises a `NotImplementedError` indicating that variables should not have children.
- **Inputs**:
    - `cls`: The class on which this class method is called.
    - `symbol`: An instance of `RawSymbolData` representing a symbol to be converted to an intermediate representation (IR).
- **Control Flow**:
    - The function immediately raises a `NotImplementedError` with a specific message.
- **Output**:
    - The function does not return any value as it raises an exception.


---
#### RustVariableData.system_prompt
The `system_prompt` function returns a predefined JSON string for system prompts related to variables found.
- **Inputs**:
    - None
- **Control Flow**:
    - The function directly returns the constant `VARIABLES_FOUND_SYSTEM_PROMPT_JSON`.
- **Output**:
    - A string containing the JSON schema for documenting global variables and constants.


---
#### RustVariableData.user_prompt
The `user_prompt` function generates a user prompt string based on the provided `RawSymbolData` object, including its name and associated code.
- **Inputs**:
    - `cls`: The class reference, typically used in class methods.
    - `symbol`: An instance of `RawSymbolData` containing information about a symbol, including its name and code.
- **Control Flow**:
    - Initialize the `user_prompt` string with a predefined prompt and the symbol's name.
    - Check if the `symbol` has `file_code`; if so, append it to the `user_prompt` string.
    - If `file_code` is not present, append `symbol_code` to the `user_prompt` string instead.
    - Return the constructed `user_prompt` string.
- **Output**:
    - A string representing the user prompt, which includes the symbol's name and its associated code.



---
### RustVariablesRawSymbolCollection 
- **Type**: `class`
- **Members**:
    - `data`: A dictionary mapping string keys to RawSymbolData or a list of RawSymbolData.
- **Description**: The RustVariablesRawSymbolCollection class is designed to collect and manage raw symbol data specifically for Rust variables. It inherits from RawSymbolCollection and provides methods to populate its data through static analysis of Rust code. The class includes a method to convert its data into a dictionary format and raises a NotImplementedError for LLM-based data extraction, emphasizing its reliance on static analysis for Rust variable symbols.
- **Inherits From**:
    - RawSymbolCollection

**Methods**

---
#### RustVariablesRawSymbolCollection.from_llm
The `from_llm` function raises a NotImplementedError indicating that static analysis should be used for Rust functions.
- **Inputs**:
    - `cls`: The class on which this class method is called.
    - `code`: A string representing the code to be analyzed.
    - `root_rel_path`: A string representing the root relative path for the code.
- **Control Flow**:
    - The function immediately raises a NotImplementedError with a specific message.
- **Output**:
    - The function does not return any output as it raises an exception.


---
#### RustVariablesRawSymbolCollection.from_static_analysis
The `from_static_analysis` function performs static analysis on Rust code to extract variable symbols and create a collection of raw symbol data.
- **Inputs**:
    - `cls`: The class type that this method is a part of, used to create an instance of the class.
    - `code`: A string containing the Rust source code to be analyzed.
    - `root_rel_path`: A Path object representing the root relative path of the file being analyzed.
- **Control Flow**:
    - Determine if the code requires multi-prompt analysis using `code_requires_multi_prompt` function.
    - Extract symbols from the code using `extract_symbols_w_ctags` function.
    - Initialize an empty dictionary `variable_raw_symbol_data` to store raw symbol data for variables.
    - Iterate over each symbol extracted from the code.
    - For each symbol, check if it is a Rust variable and does not have a scope kind.
    - If the symbol is a valid variable, create raw symbol data using `create_raw_symbol_via_ctags` and store it in `variable_raw_symbol_data`.
    - Check if `variable_raw_symbol_data` is empty; if not, create an instance of the class using the collected data and return it.
    - Return `None` if no variable symbols were found.
- **Output**:
    - Returns an instance of the class containing raw symbol data for variables if any are found, otherwise returns `None`.


---
#### RustVariablesRawSymbolCollection.to_dict
The `to_dict` function returns the `data` attribute of the instance as a dictionary.
- **Inputs**:
    - `self`: The instance of the class containing the `data` attribute.
- **Control Flow**:
    - The function directly returns the `data` attribute of the instance.
- **Output**:
    - A dictionary where keys are strings and values are of type `RawSymbolData`.



