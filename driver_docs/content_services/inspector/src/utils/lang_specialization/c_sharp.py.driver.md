# Purpose
This Python code file is designed to facilitate the extraction and documentation of C# code symbols, such as classes, structs, interfaces, enums, methods, and variables. It leverages the `pydantic` library for data validation and management, and utilizes `ctags` for static analysis to extract symbols from C# source code. The file defines several classes that represent different C# constructs, each with methods to generate system and user prompts for documentation purposes. These prompts are structured to guide the generation of detailed documentation for each symbol type, using JSON schemas to ensure consistency.

The code is organized into several key components: data classes for each C# construct (e.g., `CsClassData`, `CsStructData`), collections to manage groups of these constructs (e.g., `CsClassCollection`), and raw symbol collections that handle the extraction of symbols from C# code (e.g., `CsClassRawSymbolCollection`). Each data class includes methods to generate prompts for documentation, map child symbols to their respective types, and provide default instances. The raw symbol collections use static analysis to identify and categorize symbols within C# code, preparing them for documentation. This file is intended to be part of a larger system that automates the documentation of C# code by extracting relevant symbols and generating structured documentation based on predefined templates.
# Imports and Dependencies

---
- `pathlib`
- `typing`
- `pydantic`
- `utils.codemap_ctags`
- `utils.models`


# Global Variables

---
### CLASSES_FOUND_SYSTEM_PROMPT_JSON 
- **Type**: `str`
- **Description**: The `CLASSES_FOUND_SYSTEM_PROMPT_JSON` variable is a string that contains a detailed system prompt for documenting C# classes. It instructs the user to provide a JSON schema-based description of a class, including its description, inheritance, implemented interfaces, and modifiers.
- **Use**: This variable is used to guide the generation of documentation for C# classes by providing a structured prompt for users to follow.


---
### CLASSES_FOUND_USER_PROMPT 
- **Type**: `str`
- **Description**: `CLASSES_FOUND_USER_PROMPT` is a string variable that contains a template prompt for summarizing classes in C# code.
- **Use**: This variable is used to provide a consistent prompt format for generating class summaries in C#.


---
### C_SHARP_CLASSES 
- **Type**: `set`
- **Description**: `C_SHARP_CLASSES` is a set containing a single string element, 'class', which represents the keyword used to define classes in C# programming language.
- **Use**: This variable is used to identify and categorize C# class symbols during code analysis or processing.


---
### C_SHARP_DATA_STRUCTURES 
- **Type**: `set`
- **Description**: `C_SHARP_DATA_STRUCTURES` is a set containing a single string element, 'struct', which represents the keyword used in C# to define a structure data type.
- **Use**: This variable is used to identify and categorize C# struct symbols during code analysis or processing.


---
### C_SHARP_ENUMS 
- **Type**: `set`
- **Description**: `C_SHARP_ENUMS` is a set containing a single string element, 'enum', which represents the keyword used in C# to define enumerations.
- **Use**: This variable is used to identify and categorize C# enum symbols during code analysis or processing.


---
### C_SHARP_ENUM_VALS 
- **Type**: `set`
- **Description**: `C_SHARP_ENUM_VALS` is a set containing a single string element, 'enumerator'. This set is used to categorize or identify C# enum values within the context of the code.
- **Use**: This variable is used to identify and handle C# enum values when processing or analyzing C# code.


---
### C_SHARP_FUNCTIONS 
- **Type**: `set`
- **Description**: `C_SHARP_FUNCTIONS` is a set containing a single string element, 'method', which represents the kind of functions in C# that are categorized as methods.
- **Use**: This variable is used to identify and categorize C# functions that are specifically methods during symbol extraction and analysis.


---
### C_SHARP_INTERFACES 
- **Type**: `set`
- **Description**: `C_SHARP_INTERFACES` is a set containing a single string element, 'interface', which represents the keyword used in C# to define interfaces.
- **Use**: This variable is used to identify and categorize C# interface symbols when parsing or analyzing C# code.


---
### C_SHARP_VARIABLES 
- **Type**: `set`
- **Description**: The `C_SHARP_VARIABLES` variable is a set containing the strings 'field' and 'property'. This set is used to categorize or identify C# language constructs that are considered variables, specifically fields and properties.
- **Use**: This variable is used to identify and categorize C# fields and properties within the code.


---
### ENUMS_FOUND_SYSTEM_PROMPT_JSON 
- **Type**: `str`
- **Description**: `ENUMS_FOUND_SYSTEM_PROMPT_JSON` is a string variable that contains a JSON schema template for documenting enums in C# code. This template is used to guide the generation of documentation by specifying the expected format and content for describing enums.
- **Use**: This variable is used as a template to ensure consistent and structured documentation for enums in C# code.


---
### ENUMS_FOUND_USER_PROMPT 
- **Type**: `str`
- **Description**: `ENUMS_FOUND_USER_PROMPT` is a string variable that contains a template for generating user prompts related to summarizing enums in C# code. It provides a structured format for requesting detailed documentation of enums, including a brief description of the enum.
- **Use**: This variable is used to generate user prompts for documenting enums in C# code, ensuring a consistent format for the documentation process.


---
### INTERFACES_FOUND_SYSTEM_PROMPT_JSON 
- **Type**: `str`
- **Description**: The `INTERFACES_FOUND_SYSTEM_PROMPT_JSON` variable is a string that contains a JSON schema template for documenting interfaces in C# code.
- **Use**: This variable is used to provide a structured format for generating documentation for C# interfaces.


---
### INTERFACES_FOUND_USER_PROMPT 
- **Type**: `str`
- **Description**: INTERFACES_FOUND_USER_PROMPT is a string variable that contains a template for a user prompt used to summarize interfaces in C# code.
- **Use**: This variable is used to provide a structured prompt for summarizing C# interfaces when documenting code.


---
### METHODS_FOUND_SYSTEM_PROMPT_JSON 
- **Type**: `str`
- **Description**: `METHODS_FOUND_SYSTEM_PROMPT_JSON` is a string variable that contains a JSON schema template for documenting methods in C# code. This template guides the documentation process by specifying the structure and content required for method documentation, including a single sentence description, inputs, control flow, and output.
- **Use**: This variable is used to provide a consistent format for documenting methods in C# code, ensuring that all necessary details are captured in a structured manner.


---
### METHODS_FOUND_USER_PROMPT 
- **Type**: `string`
- **Description**: The `METHODS_FOUND_USER_PROMPT` is a string variable that contains a template prompt for summarizing methods in C# code.
- **Use**: This variable is used to provide a structured prompt for users to describe methods, including inputs, control flow, and output.


---
### SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT 
- **Type**: `str`
- **Description**: `SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT` is a string variable that contains a detailed prompt template for explaining the purpose of a large source code file.
- **Use**: This variable is used to guide the generation of a comprehensive explanation of a source code file's purpose, focusing on its functionality, components, and intended use.


---
### SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_CS 
- **Type**: `str`
- **Description**: The variable `SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_CS` is a string that contains a detailed prompt for a C# programmer and software engineering documentation expert. It instructs the expert to write comprehensive documentation for C# code, focusing on explaining technical details and the key conceptual components and purpose of the software.
- **Use**: This variable is used as a system prompt to guide the generation of detailed documentation for large C# codebases.


---
### SOURCE_CODE_SMALL_PURPOSE_USER_PROMPT 
- **Type**: `str`
- **Description**: `SOURCE_CODE_SMALL_PURPOSE_USER_PROMPT` is a string variable that contains a template for generating a user prompt to explain the purpose of a small and simple C# source code file.
- **Use**: This variable is used to provide a structured prompt for users to describe the purpose of small C# code files in a concise manner.


---
### SOURCE_CODE_SMALL_SYSTEM_PROMPT_GENERAL_CS 
- **Type**: `str`
- **Description**: This variable is a string that contains a system prompt for a C# programmer and software engineering documentation expert, specifically tailored for describing small and short source code files in C#.
- **Use**: It is used to provide a consistent and clear prompt for generating documentation for small C# source code files.


---
### STRUCTS_FOUND_SYSTEM_PROMPT_JSON 
- **Type**: `str`
- **Description**: The `STRUCTS_FOUND_SYSTEM_PROMPT_JSON` variable is a string that contains a JSON schema template for documenting C# structs. It provides a structured format for describing the details of a struct, including its description, implemented interfaces, and modifiers.
- **Use**: This variable is used to guide the documentation process for C# structs by providing a consistent schema for capturing and presenting their technical details.


---
### STRUCTS_FOUND_USER_PROMPT 
- **Type**: `str`
- **Description**: The `STRUCTS_FOUND_USER_PROMPT` is a string variable that contains a template prompt for summarizing structs in C# code. It provides guidance on how to describe a struct, emphasizing the need for detail proportional to the complexity of the struct.
- **Use**: This variable is used to generate user prompts for documenting structs in C# code, ensuring that the description matches the complexity of the struct.


---
### VARIABLES_FOUND_SYSTEM_PROMPT_JSON 
- **Type**: `str`
- **Description**: `VARIABLES_FOUND_SYSTEM_PROMPT_JSON` is a string variable that contains a JSON schema template for documenting variables in C# code.
- **Use**: This variable is used to provide a structured format for generating documentation for C# variables.


---
### VARIABLES_FOUND_USER_PROMPT 
- **Type**: `str`
- **Description**: `VARIABLES_FOUND_USER_PROMPT` is a string variable that contains a template for a user prompt used in a documentation generation system for C# variables.
- **Use**: This variable is used to format and provide a consistent prompt for users to input the name of a C# variable they want documented.


---
### _supported_child_ordering 
- **Type**: `list[str]`
- **Description**: The `_supported_child_ordering` variable is a private attribute that defines the order of child elements supported within a class or interface. It is a list of strings representing different scope relations such as fields, methods, and nested classes.
- **Use**: This variable is used to specify the order in which child elements are organized within a class or interface.


# Classes

---
### CsClassCollection 
- **Type**: `class`
- **Members**:
    - `data`: A dictionary mapping strings to CsClassData or lists of CsClassData.
- **Description**: The `CsClassCollection` class is a specialized collection class that inherits from `IrCollection`. It is designed to manage a collection of C# class data, represented by the `CsClassData` type. The class provides a class method `from_llm` which facilitates the creation of a `CsClassCollection` instance using a language model (`llm`) and a list of raw symbols (`symbols_list`). This method leverages the `from_llm_with_ir_data` method to populate the collection with `CsClassData` instances.
- **Inherits From**:
    - IrCollection

**Methods**

---
#### CsClassCollection.from_llm
The `from_llm` function creates an instance of the class using data from a language model and a collection of symbols.
- **Inputs**:
    - `llm`: An instance of the ChatOpenAI class, representing a language model.
    - `symbols_list`: An instance of RawSymbolCollection, representing a collection of raw symbols.
- **Control Flow**:
    - The function calls the `from_llm_with_ir_data` method of the class, passing `CsClassData`, `llm`, and `symbols_list` as arguments.
    - The `from_llm_with_ir_data` method is expected to handle the creation of the class instance using the provided data.
- **Output**:
    - The function returns an instance of the class it is called on, initialized with data from the language model and symbols list.



---
### CsClassData 
- **Type**: `class`
- **Members**:
    - `description`: Stores a description of the class.
    - `inherits_from`: Lists the classes this class inherits from.
    - `implements`: Lists the interfaces this class implements.
    - `modifiers`: Lists the modifiers of the class.
    - `_supported_child_ordering`: Defines the order of child elements like fields, methods, and nested classes.
- **Description**: The `CsClassData` class is a specialized data structure that extends `IrData` to represent C# class metadata, including its description, inheritance, implemented interfaces, and modifiers. It provides methods to generate system and user prompts for class documentation, and maps child symbols to their respective internal representations. The class also supports a default instance creation and defines a specific order for child elements such as fields, methods, and nested classes.
- **Inherits From**:
    - IrData

**Methods**

---
#### CsClassData.child_to_field_name
The `child_to_field_name` function maps a `RawSymbolData` object's `symbol_kind` to a corresponding `ScopeRelation` value.
- **Inputs**:
    - `cls`: The class reference, typically used for class methods.
    - `child`: An instance of `RawSymbolData` representing a symbol with a specific kind.
- **Control Flow**:
    - A dictionary `mapping` is defined to map `SymbolKind` values to `ScopeRelation` values.
    - The function returns the `ScopeRelation` value corresponding to the `symbol_kind` of the `child` using the `get` method on the `mapping` dictionary.
- **Output**:
    - The function returns a `ScopeRelation` value that corresponds to the `symbol_kind` of the provided `RawSymbolData` object, or `None` if no match is found.


---
#### CsClassData.child_to_ir
The `child_to_ir` function maps a given `RawSymbolData` symbol to a corresponding `IrData` type based on its `SymbolKind`.
- **Inputs**:
    - `cls`: The class reference, typically used to access class methods or properties.
    - `symbol`: An instance of `RawSymbolData` representing a symbol with a specific kind that needs to be mapped to an `IrData` type.
- **Control Flow**:
    - A dictionary `mapping` is defined to associate `SymbolKind` values with corresponding `IrData` types or `None`.
    - The function retrieves the `symbol_kind` from the `symbol` input and uses it to look up the corresponding `IrData` type in the `mapping` dictionary.
    - The function returns the `IrData` type associated with the `symbol_kind`, or `None` if no mapping exists.
- **Output**:
    - The function returns a type of `IrData` corresponding to the `symbol_kind` of the input symbol, or `None` if no mapping is defined for that kind.


---
#### CsClassData.default_instance
The `default_instance` function creates and returns a default instance of a class with specific attributes initialized to empty or default values.
- **Inputs**:
    - `cls`: The class for which a default instance is to be created.
- **Control Flow**:
    - The function is called with a class as an argument.
    - It returns an instance of the class with the 'description', 'inherits_from', 'implements', and 'modifiers' attributes initialized to default values.
- **Output**:
    - An instance of the class `cls` with specific attributes set to default values.


---
#### CsClassData.system_prompt
The `system_prompt` function returns a predefined JSON string for documenting C# classes.
- **Inputs**:
    - None
- **Control Flow**:
    - The function directly returns the constant `CLASSES_FOUND_SYSTEM_PROMPT_JSON`.
- **Output**:
    - A string containing a JSON schema for documenting C# classes.


---
#### CsClassData.user_prompt
The `user_prompt` function generates a formatted string prompt for documenting a class, including its name and code, and optionally the full file code if available.
- **Inputs**:
    - `cls`: The class method is being called on, typically used to access class-level attributes or methods.
    - `symbol`: An instance of `RawSymbolData` containing information about a class, including its name, symbol code, and optionally the full file code.
- **Control Flow**:
    - Initialize a string `user_prompt` with a predefined prompt template and append the class name and its symbol code from the `symbol` object.
    - Check if the `symbol` object has a `file_code` attribute that is not empty.
    - If `file_code` is present, append the full file code to the `user_prompt` string.
- **Output**:
    - A formatted string containing the class documentation prompt, including the class name, symbol code, and optionally the full file code.



---
### CsClassRawSymbolCollection 
- **Type**: `class`
- **Members**:
    - `data`: A dictionary mapping string keys to RawSymbolData objects.
- **Description**: The `CsClassRawSymbolCollection` class is a specialized collection for handling raw symbol data extracted from C# code using static analysis. It inherits from `RawSymbolCollection` and provides methods to populate its data by analyzing C# code files, identifying classes, methods, and variables, and organizing them into a structured format. The class supports the extraction of symbols using ctags and handles various C# constructs like classes, methods, and fields, while also considering method overloading and nested class structures. It is designed to be used in scenarios where static analysis is preferred over LLM-based analysis for C# classes.
- **Inherits From**:
    - RawSymbolCollection

**Methods**

---
#### CsClassRawSymbolCollection.from_llm
The `from_llm` function is a class method that raises a NotImplementedError, indicating that static analysis should be used instead for C# classes.
- **Inputs**:
    - `code`: A string representing the code to be analyzed.
    - `root_rel_path`: A string representing the root relative path of the code file.
- **Control Flow**:
    - The function immediately raises a NotImplementedError with a specific message.
- **Output**:
    - The function does not return any output as it raises an exception.


---
#### CsClassRawSymbolCollection.from_static_analysis
The `from_static_analysis` function analyzes C# code to extract and organize class and method symbols using ctags, returning a structured collection of these symbols.
- **Inputs**:
    - `code`: A string containing the C# source code to be analyzed.
    - `root_rel_path`: A Path object representing the root-relative path of the file containing the code.
- **Control Flow**:
    - Determine if the code requires multi-prompt processing using `code_requires_multi_prompt` function.
    - Extract symbols from the code using `extract_symbols_w_ctags` function.
    - Initialize dictionaries for global method counts and raw symbol data for classes.
    - Iterate over extracted symbols to count global methods and create raw symbol data for classes.
    - Iterate over symbols again to organize methods, nested classes, and variables under their respective classes based on scope and kind.
    - Check for overloaded methods and append them to the class's children if applicable.
    - Return a structured collection of class raw symbol data if any classes are found, otherwise return None.
- **Output**:
    - A structured collection of class raw symbol data if any classes are found, otherwise None.


---
#### CsClassRawSymbolCollection.to_dict
The `to_dict` function returns the `data` attribute of the instance as a dictionary.
- **Inputs**:
    - None
- **Control Flow**:
    - The function directly returns the `data` attribute of the instance.
- **Output**:
    - A dictionary where keys are strings and values are `RawSymbolData` objects.



---
### CsEnumCollection 
- **Type**: `class`
- **Members**:
    - `data`: A dictionary mapping strings to CsEnumData or lists of CsEnumData.
- **Description**: The `CsEnumCollection` class is a specialized collection that inherits from `IrCollection` and is designed to manage a collection of C# enum data. It stores its data in a dictionary where the keys are strings and the values are either `CsEnumData` objects or lists of such objects. The class provides a class method `from_llm` which facilitates the creation of a `CsEnumCollection` instance from a language model and a list of raw symbols, leveraging the `CsEnumData` class to process the intermediate representation data.
- **Inherits From**:
    - IrCollection

**Methods**

---
#### CsEnumCollection.from_llm
The `from_llm` function creates an instance of the class by invoking the `from_llm_with_ir_data` method with `CsEnumData`, a language model, and a collection of symbols.
- **Inputs**:
    - `llm`: An instance of the `ChatOpenAI` class, representing a language model.
    - `symbols_list`: An instance of `RawSymbolCollection`, representing a collection of raw symbols.
- **Control Flow**:
    - The function calls `cls.from_llm_with_ir_data` with `CsEnumData`, `llm`, and `symbols_list` as arguments.
    - The result of the `from_llm_with_ir_data` call is returned.
- **Output**:
    - An instance of the class from which the method is called, initialized using the provided language model and symbols list.



---
### CsEnumData 
- **Type**: `class`
- **Members**:
    - `description`: A field that holds a description of the enum data.
    - `_supported_child_ordering`: A private attribute that defines the supported child ordering, defaulting to enumerators.
- **Description**: The `CsEnumData` class is a specialized data structure that extends `IrData` to handle C# enum data. It includes a description field and supports child ordering for enumerators. The class provides several class methods to generate system and user prompts for enums, map child symbols to intermediate representations, and create default instances. It is designed to facilitate the processing and documentation of C# enums within a larger code analysis framework.
- **Inherits From**:
    - IrData

**Methods**

---
#### CsEnumData.child_to_field_name
The `child_to_field_name` function maps a `RawSymbolData` object's `symbol_kind` to a corresponding `ScopeRelation` value.
- **Inputs**:
    - `cls`: The class reference, typically used for class methods.
    - `child`: An instance of `RawSymbolData` representing a symbol with a specific kind.
- **Control Flow**:
    - A dictionary `mapping` is defined to map `SymbolKind.VARIABLE` to `ScopeRelation.ENUMERATOR`.
    - The function attempts to retrieve the `ScopeRelation` value from the `mapping` dictionary using the `symbol_kind` of the `child` argument.
- **Output**:
    - The function returns a `ScopeRelation` value corresponding to the `symbol_kind` of the `child`, or `None` if no mapping is found.


---
#### CsEnumData.child_to_ir
The `child_to_ir` function maps a `RawSymbolData`'s `symbol_kind` to a corresponding `IrData` type or returns `None` if no mapping exists.
- **Inputs**:
    - `cls`: The class reference, typically used to access class-level attributes or methods.
    - `symbol`: An instance of `RawSymbolData` representing a symbol with a `symbol_kind` attribute.
- **Control Flow**:
    - A dictionary `mapping` is defined with `SymbolKind.VARIABLE` mapped to `None`.
    - The function attempts to retrieve a value from `mapping` using `symbol.symbol_kind` as the key.
    - If a mapping exists, the corresponding value is returned; otherwise, `None` is returned.
- **Output**:
    - The function returns a type of `IrData` if a mapping exists for the given `symbol_kind`, otherwise it returns `None`.


---
#### CsEnumData.default_instance
The `default_instance` function creates and returns a default instance of the class with an empty description.
- **Inputs**:
    - `cls`: The class for which a default instance is to be created.
- **Control Flow**:
    - The function is a class method, indicated by the use of `cls` as the first parameter.
    - It returns a new instance of the class `cls` by calling its constructor with a `description` argument.
    - The `description` is set to an instance of `FieldNameWithRawContent` with its `content` attribute initialized to an empty string.
- **Output**:
    - A new instance of the class `cls` with a default description.


---
#### CsEnumData.system_prompt
The `system_prompt` function returns a predefined JSON string for documenting enums in C#.
- **Inputs**:
    - None
- **Control Flow**:
    - The function directly returns the constant `ENUMS_FOUND_SYSTEM_PROMPT_JSON`.
- **Output**:
    - A string containing a JSON schema for documenting C# enums.


---
#### CsEnumData.user_prompt
The `user_prompt` function generates a formatted string prompt for a given enum symbol, including its name, code, and optionally the full file code.
- **Inputs**:
    - `symbol`: An instance of `RawSymbolData` containing information about the enum, including its name, symbol code, and optionally the full file code.
- **Control Flow**:
    - Initialize a string `user_prompt` with a formatted message that includes the enum's name and its symbol code.
    - Check if the `symbol` has `file_code` available.
    - If `file_code` is present, append it to the `user_prompt` string with appropriate formatting.
    - Return the complete `user_prompt` string.
- **Output**:
    - A formatted string containing the enum's name, symbol code, and optionally the full file code.



---
### CsEnumRawSymbolCollection 
- **Type**: `class`
- **Members**:
    - `data`: A dictionary mapping string keys to RawSymbolData objects.
- **Description**: The `CsEnumRawSymbolCollection` class is a specialized collection for handling raw symbol data related to C# enums. It inherits from `RawSymbolCollection` and provides methods to populate the collection using static analysis of C# code. The class includes a class method `from_static_analysis` that extracts symbols from the provided code and organizes them into a dictionary, filtering for C# enums and their values. The `to_dict` method returns this dictionary, allowing for easy access to the raw symbol data.
- **Inherits From**:
    - RawSymbolCollection

**Methods**

---
#### CsEnumRawSymbolCollection.from_llm
The `from_llm` function is a class method placeholder that raises a NotImplementedError, indicating that static analysis should be used for C# enums instead of this method.
- **Inputs**:
    - `cls`: The class on which this method is called, typically passed automatically by Python when the method is called on a class.
    - `code`: A string representing the code to be analyzed.
    - `root_rel_path`: A string representing the root relative path where the code is located.
- **Control Flow**:
    - The function immediately raises a NotImplementedError with a message indicating that static analysis should be used for C# enums.
- **Output**:
    - The function does not return any output as it raises an exception immediately.


---
#### CsEnumRawSymbolCollection.from_static_analysis
The `from_static_analysis` function analyzes C# code to extract and organize enum symbols and their values using ctags.
- **Inputs**:
    - `code`: A string representing the C# code to be analyzed.
    - `root_rel_path`: A Path object representing the root relative path of the file containing the code.
- **Control Flow**:
    - Determine if the code requires multi-prompt processing using `code_requires_multi_prompt` function.
    - Extract symbols from the code using `extract_symbols_w_ctags` function.
    - Initialize an empty dictionary `enum_raw_symbol_data` to store raw symbol data for enums.
    - Iterate over the extracted symbols to identify enums and populate `enum_raw_symbol_data` with raw symbol data created via `create_raw_symbol_via_ctags`.
    - Sort the symbols by line number and iterate over them to identify enum values, appending them as children to their respective enum in `enum_raw_symbol_data`.
    - Return `None` if `enum_raw_symbol_data` is empty; otherwise, return an instance of the class with `enum_raw_symbol_data` as its data.
- **Output**:
    - Returns an instance of the class with extracted enum symbol data or `None` if no enums are found.


---
#### CsEnumRawSymbolCollection.to_dict
The `to_dict` function returns the `data` attribute of the instance as a dictionary.
- **Inputs**:
    - None
- **Control Flow**:
    - The function directly returns the `data` attribute of the instance.
- **Output**:
    - A dictionary where the keys are strings and the values are `RawSymbolData` objects.



---
### CsInterfaceCollection 
- **Type**: `class`
- **Members**:
    - `data`: A dictionary mapping strings to either a CsInterfaceData instance or a list of CsInterfaceData instances.
- **Description**: The `CsInterfaceCollection` class is a specialized collection class that inherits from `IrCollection`. It is designed to manage a collection of C# interface data, specifically instances of `CsInterfaceData`. The class provides a class method `from_llm` which facilitates the creation of a `CsInterfaceCollection` instance using a language model (`llm`) and a list of raw symbols (`symbols_list`). This method leverages the `from_llm_with_ir_data` method to populate the collection with interface data.
- **Inherits From**:
    - IrCollection

**Methods**

---
#### CsInterfaceCollection.from_llm
The `from_llm` function creates an instance of the class using data from a language model and a collection of symbols.
- **Inputs**:
    - `llm`: An instance of the ChatOpenAI class, representing a language model.
    - `symbols_list`: An instance of RawSymbolCollection, representing a collection of symbols to be used in the instantiation process.
- **Control Flow**:
    - The function calls the `from_llm_with_ir_data` method on the class, passing `CsInterfaceData`, `llm`, and `symbols_list` as arguments.
    - The `from_llm_with_ir_data` method is expected to handle the instantiation process using the provided data and return an instance of the class.
- **Output**:
    - An instance of the class from which the method is called, initialized with data from the language model and symbols list.



---
### CsInterfaceData 
- **Type**: `class`
- **Members**:
    - `interfaces_inherited`: A list of interfaces that are inherited by this interface data.
    - `description`: A description of the interface data.
    - `_supported_child_ordering`: A private attribute that defines the order of supported child elements, specifically fields and methods.
- **Description**: The `CsInterfaceData` class is designed to represent and manage data related to C# interfaces within a documentation or code analysis context. It inherits from `IrData` and includes attributes for storing inherited interfaces and a description. The class provides several class methods to generate prompts for system and user interactions, determine the type of intermediate representation (IR) data for child symbols, and map child symbols to field names. It also includes a method to create a default instance of the class with empty content for its attributes.
- **Inherits From**:
    - IrData

**Methods**

---
#### CsInterfaceData.child_to_field_name
The `child_to_field_name` function maps a `RawSymbolData` object's `symbol_kind` to a corresponding `ScopeRelation` value.
- **Inputs**:
    - `cls`: The class reference, typically used for class methods.
    - `child`: An instance of `RawSymbolData` representing a symbol with a specific kind.
- **Control Flow**:
    - A dictionary `mapping` is defined to map `SymbolKind` values to `ScopeRelation` values.
    - The function attempts to retrieve the `ScopeRelation` value from the `mapping` dictionary using the `symbol_kind` of the `child` argument.
- **Output**:
    - The function returns a `ScopeRelation` value corresponding to the `symbol_kind` of the `child`, or `None` if no mapping is found.


---
#### CsInterfaceData.child_to_ir
The `child_to_ir` function maps a `RawSymbolData` object to a corresponding `IrData` type based on the symbol's kind.
- **Inputs**:
    - `cls`: The class reference, typically used to access class methods or properties.
    - `symbol`: An instance of `RawSymbolData` representing a symbol whose kind is to be mapped to an `IrData` type.
- **Control Flow**:
    - A dictionary `mapping` is defined to associate `SymbolKind` values with corresponding `IrData` types or `None`.
    - The function attempts to retrieve the `IrData` type from the `mapping` dictionary using the `symbol.symbol_kind` as the key.
    - If the `symbol_kind` is found in the dictionary, the corresponding `IrData` type is returned; otherwise, `None` is returned.
- **Output**:
    - The function returns a type of `IrData` corresponding to the symbol's kind, or `None` if no mapping exists.


---
#### CsInterfaceData.default_instance
The `default_instance` function creates and returns a default instance of a class with specific default values for its attributes.
- **Inputs**:
    - `cls`: The class for which a default instance is to be created.
- **Control Flow**:
    - The function is called with a class as an argument.
    - It returns an instance of the class, initialized with default values for its attributes.
- **Output**:
    - An instance of the class `cls` with default values for `interfaces_inherited` and `description` attributes.


---
#### CsInterfaceData.system_prompt
The `system_prompt` function returns a predefined JSON string for documenting C# interfaces.
- **Inputs**:
    - None
- **Control Flow**:
    - The function directly returns the value of the constant `INTERFACES_FOUND_SYSTEM_PROMPT_JSON`.
- **Output**:
    - A string containing a JSON schema for documenting C# interfaces.


---
#### CsInterfaceData.user_prompt
The `user_prompt` function generates a formatted string prompt for a user based on a given symbol's data.
- **Inputs**:
    - `symbol`: An instance of `RawSymbolData` containing the name, symbol code, and optionally the full file code of a symbol.
- **Control Flow**:
    - Initialize a string `user_prompt` with a predefined prompt and the symbol's name and code.
    - Check if the symbol has associated file code.
    - If file code exists, append it to the `user_prompt` string.
    - Return the complete `user_prompt` string.
- **Output**:
    - A formatted string containing the user prompt with the symbol's name, code, and optionally the full file code.



---
### CsInterfaceRawSymbolCollection 
- **Type**: `class`
- **Members**:
    - `data`: A dictionary mapping symbol names to their corresponding RawSymbolData.
- **Description**: The CsInterfaceRawSymbolCollection class is a specialized collection for handling raw symbol data specifically related to C# interfaces. It inherits from RawSymbolCollection and provides methods for constructing the collection from static analysis of C# code. The class processes symbols extracted from the code, categorizing them into interfaces and their associated methods and fields, while also handling cases of method overloading. The class is designed to facilitate the organization and retrieval of interface-related symbol data for further processing or analysis.
- **Inherits From**:
    - RawSymbolCollection

**Methods**

---
#### CsInterfaceRawSymbolCollection.from_llm
The `from_llm` function is a class method that raises a NotImplementedError, indicating that static analysis should be used for C# classes instead of this method.
- **Inputs**:
    - `code`: A string representing the code to be analyzed.
    - `root_rel_path`: A string representing the root relative path of the code file.
- **Control Flow**:
    - The function immediately raises a NotImplementedError with a specific message.
- **Output**:
    - The function does not return any output as it raises an exception.


---
#### CsInterfaceRawSymbolCollection.from_static_analysis
The `from_static_analysis` function analyzes C# code to extract and organize interface-related symbols using ctags.
- **Inputs**:
    - `cls`: The class type that this method belongs to, used for creating an instance of the class.
    - `code`: A string containing the C# source code to be analyzed.
    - `root_rel_path`: A Path object representing the root-relative path of the file containing the code.
- **Control Flow**:
    - Determine if the code requires multi-prompt processing using `code_requires_multi_prompt` function.
    - Extract symbols from the code using `extract_symbols_w_ctags` function.
    - Initialize dictionaries for counting global methods and storing raw symbol data for interfaces.
    - Iterate over extracted symbols to count methods and create raw symbol data for interfaces, excluding anonymous symbols.
    - Iterate over symbols again to append method and variable symbols to their respective interface data structures, handling overloaded methods and fields.
    - Return an instance of the class with the structured raw symbol data if any interfaces were found, otherwise return None.
- **Output**:
    - An instance of the class with structured raw symbol data for interfaces, or None if no interfaces are found.


---
#### CsInterfaceRawSymbolCollection.to_dict
The `to_dict` function returns the `data` attribute of the instance as a dictionary.
- **Inputs**:
    - None
- **Control Flow**:
    - The function directly returns the `data` attribute of the instance.
- **Output**:
    - A dictionary where the keys are strings and the values are `RawSymbolData` objects.



---
### CsMethodData 
- **Type**: `class`
- **Members**:
    - `system_prompt`: Returns a system prompt string for documenting methods.
    - `user_prompt`: Generates a user prompt string based on the provided symbol data.
    - `child_to_ir`: Raises a NotImplementedError indicating methods should not have children.
    - `child_to_field_name`: Raises a NotImplementedError indicating methods should not have children.
- **Description**: The `CsMethodData` class is a specialized data structure for handling method-related information in C# code documentation. It inherits from `FnData` and provides class methods to generate system and user prompts for documenting methods, specifically focusing on methods found in C# code. The class also includes methods that raise `NotImplementedError` for handling children, as methods are not expected to have child elements in this context.
- **Inherits From**:
    - FnData

**Methods**

---
#### CsMethodData.child_to_field_name
The `child_to_field_name` function raises a `NotImplementedError` indicating that methods should not have children.
- **Inputs**:
    - `cls`: The class to which this method belongs.
    - `child`: An instance of `RawSymbolData` representing a child symbol.
- **Control Flow**:
    - The function immediately raises a `NotImplementedError` with a specific message.
- **Output**:
    - The function does not return any value as it raises an exception.


---
#### CsMethodData.child_to_ir
The `child_to_ir` function raises a `NotImplementedError` indicating that methods should not have children.
- **Inputs**:
    - `cls`: The class on which this method is called, typically a class method.
    - `symbol`: An instance of `RawSymbolData` representing a symbol in the code.
- **Control Flow**:
    - The function immediately raises a `NotImplementedError` with a specific message.
- **Output**:
    - The function does not return any value as it raises an exception.


---
#### CsMethodData.system_prompt
The `system_prompt` function returns a predefined JSON string used as a system prompt for documenting methods in C#.
- **Inputs**:
    - None
- **Control Flow**:
    - The function directly returns the constant `METHODS_FOUND_SYSTEM_PROMPT_JSON`.
- **Output**:
    - A string containing a JSON schema for documenting C# methods.


---
#### CsMethodData.user_prompt
The `user_prompt` function generates a formatted string prompt for a user based on a given symbol's name and code, optionally including the full file code if available.
- **Inputs**:
    - `cls`: The class reference, typically used in class methods to refer to the class itself.
    - `symbol`: An instance of `RawSymbolData` containing the symbol's name, symbol code, and optionally the full file code.
- **Control Flow**:
    - Initialize `user_prompt` with a formatted string containing a predefined prompt, the symbol's name, and its code.
    - Check if the `symbol` has associated file code.
    - If file code is present, append it to the `user_prompt` string.
    - Return the complete `user_prompt` string.
- **Output**:
    - A string that contains a formatted prompt with the symbol's name, code, and optionally the full file code.



---
### CsStructCollection 
- **Type**: `class`
- **Members**:
    - `data`: A dictionary mapping strings to CsStructData or lists of CsStructData.
- **Description**: The `CsStructCollection` class is a specialized collection that inherits from `IrCollection` and is designed to manage a collection of C# structure data (`CsStructData`). It provides a class method `from_llm` that facilitates the creation of a `CsStructCollection` instance using a language model (`ChatOpenAI`) and a list of raw symbols (`RawSymbolCollection`). This class is part of a system that processes and organizes C# code structures, likely for documentation or analysis purposes.
- **Inherits From**:
    - IrCollection

**Methods**

---
#### CsStructCollection.from_llm
The `from_llm` function creates an instance of the class by invoking the `from_llm_with_ir_data` method with `CsStructData`, a language model, and a collection of symbols.
- **Inputs**:
    - `llm`: An instance of the `ChatOpenAI` class, representing a language model.
    - `symbols_list`: An instance of `RawSymbolCollection`, representing a collection of raw symbols.
- **Control Flow**:
    - The function calls `cls.from_llm_with_ir_data` with `CsStructData`, `llm`, and `symbols_list` as arguments.
    - The result of the `from_llm_with_ir_data` call is returned.
- **Output**:
    - An instance of the class from which the method is called, initialized using the provided language model and symbols list.



---
### CsStructData 
- **Type**: `class`
- **Members**:
    - `description`: Stores a description of the C# struct.
    - `implements`: Holds a list of interfaces implemented by the C# struct.
    - `modifiers`: Contains a list of modifiers applied to the C# struct.
    - `_supported_child_ordering`: Defines the order of child elements like fields, methods, and nested classes.
- **Description**: The `CsStructData` class is designed to represent and manage metadata for C# struct definitions. It inherits from `IrData` and includes attributes to store the struct's description, implemented interfaces, and modifiers. The class also defines a private attribute to specify the order of child elements such as fields, methods, and nested classes. It provides class methods to generate system and user prompts for documentation purposes, map child symbols to their respective intermediate representations, and create default instances of the class.
- **Inherits From**:
    - IrData

**Methods**

---
#### CsStructData.child_to_field_name
The `child_to_field_name` function maps a `RawSymbolData` object's `symbol_kind` to a corresponding `ScopeRelation` value.
- **Inputs**:
    - `cls`: The class reference, typically used for class methods.
    - `child`: An instance of `RawSymbolData` representing a symbol with a specific kind.
- **Control Flow**:
    - A dictionary `mapping` is defined to map `SymbolKind` values to `ScopeRelation` values.
    - The function attempts to retrieve the `ScopeRelation` value from the `mapping` dictionary using the `symbol_kind` attribute of the `child` argument.
    - The function returns the retrieved `ScopeRelation` value or `None` if the `symbol_kind` is not found in the `mapping`.
- **Output**:
    - The function returns a `ScopeRelation` value corresponding to the `symbol_kind` of the `child`, or `None` if no mapping exists.


---
#### CsStructData.child_to_ir
The `child_to_ir` function maps a `RawSymbolData` object's `symbol_kind` to a corresponding `IrData` type or returns `None` if no mapping exists.
- **Inputs**:
    - `cls`: The class reference, typically used for class methods.
    - `symbol`: An instance of `RawSymbolData` representing a symbol with a specific kind that needs to be mapped to an `IrData` type.
- **Control Flow**:
    - A dictionary `mapping` is defined to associate `SymbolKind` values with corresponding `IrData` types or `None`.
    - The function attempts to retrieve the `IrData` type from the `mapping` dictionary using the `symbol.symbol_kind` as the key.
    - If a corresponding `IrData` type is found, it is returned; otherwise, `None` is returned.
- **Output**:
    - The function returns a type of `IrData` corresponding to the `symbol_kind` of the input `symbol`, or `None` if no mapping exists.


---
#### CsStructData.default_instance
The `default_instance` function creates and returns a default instance of a class with specific attributes initialized to empty values.
- **Inputs**:
    - `cls`: The class for which a default instance is to be created.
- **Control Flow**:
    - The function is a class method, indicated by the use of `cls` as the first parameter.
    - It returns an instance of the class `cls` by calling its constructor.
    - The constructor is called with three keyword arguments: `description`, `implements`, and `modifiers`.
    - Each of these arguments is initialized with an empty or default value: `description` is set to an instance of `FieldNameWithRawContent` with an empty string, and both `implements` and `modifiers` are set to instances of `ListedRawContentNoNone` with empty lists.
- **Output**:
    - An instance of the class `cls` with default values for `description`, `implements`, and `modifiers` attributes.


---
#### CsStructData.system_prompt
The `system_prompt` function returns a predefined JSON string for documenting C# structs.
- **Inputs**:
    - None
- **Control Flow**:
    - The function directly returns the value of the constant `STRUCTS_FOUND_SYSTEM_PROMPT_JSON`.
- **Output**:
    - A string containing a JSON schema for documenting C# structs.


---
#### CsStructData.user_prompt
The `user_prompt` function generates a formatted string prompt for a given symbol, including its name, code, and optionally the full file code.
- **Inputs**:
    - `cls`: The class reference, typically used in class methods to refer to the class itself.
    - `symbol`: An instance of `RawSymbolData` containing information about a symbol, including its name, symbol code, and optionally file code.
- **Control Flow**:
    - Initialize a string `user_prompt` with a formatted message including the symbol's name and symbol code.
    - Check if the `symbol` has `file_code` and if so, append the full file code to the `user_prompt`.
    - Return the constructed `user_prompt` string.
- **Output**:
    - A formatted string that includes the symbol's name, symbol code, and optionally the full file code.



---
### CsStructRawSymbolCollection 
- **Type**: `class`
- **Members**:
    - `data`: A dictionary mapping string keys to RawSymbolData objects.
- **Description**: The `CsStructRawSymbolCollection` class is a specialized collection for handling raw symbol data related to C# structures. It inherits from `RawSymbolCollection` and provides methods for extracting and organizing symbols from C# code using static analysis. The class focuses on identifying and categorizing C# data structures, functions, classes, and variables, and it constructs a hierarchical representation of these symbols. The `from_static_analysis` class method is central to its functionality, parsing code to populate the `data` attribute with structured symbol information. This class is designed to facilitate the analysis and documentation of C# code by providing a structured view of its components.
- **Inherits From**:
    - RawSymbolCollection

**Methods**

---
#### CsStructRawSymbolCollection.from_llm
The `from_llm` function is a class method that raises a NotImplementedError, indicating that static analysis should be used instead for C# classes.
- **Inputs**:
    - `code`: A string representing the code to be analyzed.
    - `root_rel_path`: A string representing the root relative path of the code file.
- **Control Flow**:
    - The function immediately raises a NotImplementedError with a specific message.
- **Output**:
    - The function does not return any output as it raises an exception.


---
#### CsStructRawSymbolCollection.from_static_analysis
The `from_static_analysis` function analyzes C# code to extract and organize symbols related to data structures, methods, and variables using static analysis.
- **Inputs**:
    - `code`: A string representing the C# code to be analyzed.
    - `root_rel_path`: A Path object representing the root relative path of the file containing the code.
- **Control Flow**:
    - Determine if the code requires multi-prompt processing using `code_requires_multi_prompt` function.
    - Extract symbols from the code using `extract_symbols_w_ctags` function.
    - Initialize dictionaries for counting global methods and storing raw symbol data for structures.
    - Iterate over the extracted symbols to populate global method counts and raw symbol data for structures.
    - For each symbol, check its scope and kind to determine if it should be processed further.
    - Depending on the symbol kind and scope, append the symbol to the appropriate structure's children in the raw symbol data.
    - Return an instance of the class with the structured raw symbol data if any symbols were processed, otherwise return None.
- **Output**:
    - An instance of the class containing structured raw symbol data if symbols are found, otherwise None.


---
#### CsStructRawSymbolCollection.to_dict
The `to_dict` function returns the `data` attribute of the instance as a dictionary.
- **Inputs**:
    - None
- **Control Flow**:
    - The function directly returns the `data` attribute of the instance.
- **Output**:
    - A dictionary where the keys are strings and the values are `RawSymbolData` objects.



---
### CsVariableData 
- **Type**: `class`
- **Members**:
    - `description`: A field that holds a description of the variable data.
- **Description**: The `CsVariableData` class is a specialized data structure that extends `IrData` to handle variable-related information in a C# context. It provides methods to generate system and user prompts for variable documentation, ensuring that variables are properly described and documented. The class explicitly raises `NotImplementedError` for methods related to child elements, indicating that variables should not have children. It also includes a method to return a default instance of itself with an empty description.
- **Inherits From**:
    - IrData

**Methods**

---
#### CsVariableData.child_to_field_name
The `child_to_field_name` function raises a `NotImplementedError` indicating that variables should not have children.
- **Inputs**:
    - `cls`: The class reference, typically used in class methods to refer to the class itself.
    - `child`: An instance of `RawSymbolData`, representing a symbol that might be considered a child in some contexts.
- **Control Flow**:
    - The function immediately raises a `NotImplementedError` with a specific message.
- **Output**:
    - The function does not return any value as it raises an exception.


---
#### CsVariableData.child_to_ir
The `child_to_ir` function raises a `NotImplementedError` indicating that variables should not have children.
- **Inputs**:
    - `cls`: The class reference from which the method is called.
    - `symbol`: An instance of `RawSymbolData` representing a symbol in the code.
- **Control Flow**:
    - The function immediately raises a `NotImplementedError` with a specific message.
- **Output**:
    - The function does not return any value as it raises an exception.


---
#### CsVariableData.default_instance
The `default_instance` function creates and returns a default instance of the class with an empty description.
- **Inputs**:
    - `cls`: The class for which a default instance is to be created.
- **Control Flow**:
    - The function is a class method, indicated by the use of `cls` as the first parameter.
    - It returns a new instance of the class `cls` by calling its constructor with a `description` argument.
    - The `description` is set to an instance of `FieldNameWithRawContent` with its `content` attribute initialized to an empty string.
- **Output**:
    - A new instance of the class `cls` with a default description.


---
#### CsVariableData.system_prompt
The `system_prompt` function returns a predefined JSON string for documenting variables in C#.
- **Inputs**:
    - None
- **Control Flow**:
    - The function directly returns the constant `VARIABLES_FOUND_SYSTEM_PROMPT_JSON`.
- **Output**:
    - A string containing JSON schema for documenting C# variables.


---
#### CsVariableData.user_prompt
The `user_prompt` function generates a formatted string prompt for a given symbol, including its name, code, and optionally the full file code.
- **Inputs**:
    - `cls`: The class reference, typically used in class methods to refer to the class itself.
    - `symbol`: An instance of `RawSymbolData` containing information about a symbol, including its name, symbol code, and optionally file code.
- **Control Flow**:
    - Initialize a string `user_prompt` with a formatted message including the symbol's name and symbol code.
    - Check if the `symbol` has associated file code.
    - If file code is present, append it to the `user_prompt` string with appropriate formatting.
    - Return the constructed `user_prompt` string.
- **Output**:
    - A formatted string containing the symbol's name, symbol code, and optionally the full file code.



