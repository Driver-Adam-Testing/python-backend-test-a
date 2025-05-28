# Purpose
This Python code file is designed to facilitate the extraction and documentation of Python code symbols, such as classes, functions, and variables, using static analysis tools like ctags. It defines a series of classes and methods that categorize and process these symbols into structured data collections. The file includes classes like `PyVariableData`, `PyFnData`, and `PyClassData`, which are responsible for generating prompts for documentation purposes, specifically tailored for variables, functions, and classes, respectively. These classes also define methods for converting raw symbol data into intermediate representations (IR) and for handling the relationships between symbols, such as methods within classes or nested classes.

The file also contains classes like `PyVariableRawSymbolCollection`, `PyFnRawSymbolCollection`, and `PyClassRawSymbolCollection`, which are responsible for performing static analysis on Python code to extract symbols and organize them into collections. These classes utilize ctags to identify and categorize symbols based on their kind (e.g., class, function, variable) and scope. The extracted symbols are then used to create structured data that can be further processed for documentation generation. Overall, this file provides a comprehensive framework for analyzing Python code and generating detailed documentation for its components.
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
### CLASSES_FOUND_SYSTEM_PROMPT_JSON 
- **Type**: `str`
- **Description**: `CLASSES_FOUND_SYSTEM_PROMPT_JSON` is a string variable that contains a JSON schema template for documenting Python classes. This template guides the user to describe a class, its members, and its inheritance in a structured JSON format. The variable is designed to ensure consistent and detailed documentation of class structures in Python code.
- **Use**: This variable is used to provide a standardized JSON schema for documenting Python classes.


---
### CLASSES_FOUND_USER_PROMPT 
- **Type**: `string`
- **Description**: `CLASSES_FOUND_USER_PROMPT` is a string variable that contains a template prompt for summarizing classes in Python code. The prompt guides the user to provide detailed documentation for classes, focusing on technical details and the key components and purpose of the software.
- **Use**: This variable is used to generate user prompts for documenting classes in Python code.


---
### DATA_STRUCTURES_FOUND_SYSTEM_PROMPT_JSON 
- **Type**: `string`
- **Description**: The `DATA_STRUCTURES_FOUND_SYSTEM_PROMPT_JSON` variable is a string that contains a JSON schema template. This template is used to guide the documentation process for data structures, typically classes, in Python. It specifies the format and content required for documenting data structures, including their type, members, and a description.
- **Use**: This variable is used to provide a structured format for documenting Python data structures.


---
### DATA_STRUCTURES_FOUND_USER_PROMPT 
- **Type**: `string`
- **Description**: The variable `DATA_STRUCTURES_FOUND_USER_PROMPT` is a string that contains a template for a user prompt. This prompt is used to request a summary of a data structure in the provided code. It guides the user to focus on describing the complexity and details of the data structure, particularly in Python where data structures are typically defined as classes.
- **Use**: This variable is used to generate a user prompt for summarizing data structures in Python code.


---
### FUNCTIONS_FOUND_SYSTEM_PROMPT_JSON 
- **Type**: `str`
- **Description**: The `FUNCTIONS_FOUND_SYSTEM_PROMPT_JSON` variable is a multi-line string that contains a detailed system prompt for documenting Python functions. It instructs the user to describe a function using a specific JSON schema, focusing on inputs, control flow, and output.
- **Use**: This variable is used as a template for generating documentation for Python functions.


---
### FUNCTIONS_FOUND_USER_PROMPT 
- **Type**: `string`
- **Description**: `FUNCTIONS_FOUND_USER_PROMPT` is a string variable that contains a template for a user prompt. This prompt is used to instruct the user to summarize a function in the provided code, focusing on inputs, control flow, logic, and output. The template emphasizes providing detail that matches the complexity of the function body.
- **Use**: This variable is used as a template for generating user prompts to guide them in documenting functions.


---
### METHODS_FOUND_SYSTEM_PROMPT_JSON 
- **Type**: `str`
- **Description**: `METHODS_FOUND_SYSTEM_PROMPT_JSON` is a string variable that contains a JSON schema template. This template is used for documenting class methods in Python, focusing on inputs, control flow, and outputs. The schema ensures that the documentation is consistent and follows a specific format.
- **Use**: This variable is used to provide a structured format for documenting Python class methods.


---
### METHODS_FOUND_USER_PROMPT 
- **Type**: `str`
- **Description**: `METHODS_FOUND_USER_PROMPT` is a string variable that contains a template for a user prompt. This prompt is used to request a summary of a class method in the provided code, focusing on inputs, control flow, logic, and output. The prompt guides the user to provide detailed descriptions based on the complexity of the function body.
- **Use**: This variable is used to generate user prompts for summarizing class methods in Python code.


---
### PY_CLASS 
- **Type**: `set`
- **Description**: The variable `PY_CLASS` is a set containing a single string element, 'class'. This set is likely used to categorize or identify Python class symbols in a broader context of symbol extraction or analysis.
- **Use**: This variable is used to define the kind of symbols that are considered Python classes in the context of symbol extraction.


---
### PY_FUNCTIONS 
- **Type**: `set`
- **Description**: `PY_FUNCTIONS` is a global variable defined as a set containing a single string element, 'function'. This set is likely used to categorize or identify Python functions within a larger system, possibly for the purpose of symbol extraction or analysis.
- **Use**: This variable is used to specify the kind of symbols that represent functions in Python, likely for static analysis or code parsing purposes.


---
### PY_METHODS 
- **Type**: `set`
- **Description**: `PY_METHODS` is a global variable defined as a set containing the string 'member'. This set is used to categorize or identify Python methods within a codebase, likely in the context of symbol extraction or analysis.
- **Use**: This variable is used to specify the kind of symbols that represent Python methods when performing static analysis or symbol extraction.


---
### PY_VARIABLES 
- **Type**: `set`
- **Description**: `PY_VARIABLES` is a set containing a single string element, 'variable'. This set is used to categorize or identify Python variables within the context of the code, likely for symbol extraction or analysis purposes.
- **Use**: This variable is used to specify the kind of symbols that are considered as variables in the code analysis process.


---
### SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT 
- **Type**: `str`
- **Description**: `SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT` is a string variable that contains a detailed prompt for explaining the purpose of a large source code file. It guides the user to consider various aspects of the code, such as its functionality, technical components, and whether it defines public APIs or interfaces.
- **Use**: This variable is used to provide a structured prompt for users to generate comprehensive explanations of large source code files.


---
### SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_PY 
- **Type**: `str`
- **Description**: The variable `SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_PY` is a multi-line string that serves as a system prompt for a large-scale Python documentation task. It outlines the role of the user as an expert Python programmer and documentation expert, emphasizing the need to explain code and recognize key components and purposes of software.
- **Use**: This variable is used as a system prompt to guide the behavior of a language model or similar tool in generating detailed documentation for Python code.


---
### SOURCE_CODE_SMALL_PURPOSE_USER_PROMPT 
- **Type**: `string`
- **Description**: This variable contains a system prompt string specifically designed for small Python source code files. It provides guidance for writing concise and clear documentation for small and simple code structures.
- **Use**: This variable is used to provide a system prompt for generating documentation for small Python source code files.


---
### SOURCE_CODE_SMALL_SYSTEM_PROMPT_GENERAL_PY 
- **Type**: `str`
- **Description**: `SOURCE_CODE_SMALL_SYSTEM_PROMPT_GENERAL_PY` is a string variable that contains a system prompt for a language model. This prompt is designed to instruct the model to focus on writing concise and clear documentation for small and simple Python source code files. The prompt emphasizes the importance of being terse and clear in the documentation process.
- **Use**: This variable is used to provide a predefined prompt for generating documentation for small Python source code files.


---
### TECHNICAL_CONCEPTS 
- **Type**: `str`
- **Description**: The `TECHNICAL_CONCEPTS` variable is a multi-line string that provides a template for describing the important technical features and their interactions within a source code file. It emphasizes writing about conceptual use cases, applications, logic, and component interactions rather than focusing on specific classes, functions, or variables.
- **Use**: This variable is used as a guideline or prompt for generating descriptions of technical concepts in source code files.


---
### VARIABLES_FOUND_SYSTEM_PROMPT_JSON 
- **Type**: `string`
- **Description**: The `VARIABLES_FOUND_SYSTEM_PROMPT_JSON` is a string variable that contains a JSON schema template. This template is used to guide the documentation process for Python variables, ensuring that the documentation is structured and consistent. The schema includes fields for the type, description, and use of a variable.
- **Use**: This variable is used to provide a structured template for documenting Python variables.


---
### VARIABLES_FOUND_USER_PROMPT 
- **Type**: `str`
- **Description**: METHODS_FOUND_USER_PROMPT is a string variable that contains a template prompt for summarizing class methods in Python code. It provides guidelines on how to describe the inputs, control flow, logic, and output of a class method, emphasizing the need for detail proportional to the complexity of the method.
- **Use**: This variable is used to provide a structured prompt for generating documentation for class methods.


# Classes

---
### PyClassCollection 
- **Type**: `class`
- **Members**:
    - `data`: A dictionary mapping strings to either a PyClassData instance or a list of PyClassData instances.
- **Description**: The `PyClassCollection` class is a specialized collection class that inherits from `IrCollection`. It is designed to manage a collection of Python class data, specifically instances of `PyClassData` or lists of such instances. The class provides a class method `from_llm` which facilitates the creation of a `PyClassCollection` instance using a language model (`llm`) and a list of raw symbols (`symbols_list`). This method leverages the `from_llm_with_ir_data` method to populate the collection with the appropriate data.
- **Inherits From**:
    - IrCollection

**Methods**

---
#### PyClassCollection.from_llm
The `from_llm` function creates an instance of the class by invoking the `from_llm_with_ir_data` method with `PyClassData`, `llm`, and `symbols_list` as arguments.
- **Inputs**:
    - `cls`: The class itself, used to call class methods.
    - `llm`: An instance of the `ChatOpenAI` class, representing a language model.
    - `symbols_list`: An instance of `RawSymbolCollection`, representing a collection of raw symbols.
- **Control Flow**:
    - The function calls the `from_llm_with_ir_data` method on the class `cls`.
    - It passes `PyClassData`, `llm`, and `symbols_list` as arguments to the method.
- **Output**:
    - An instance of the class `cls` created using the `from_llm_with_ir_data` method.



---
### PyClassData 
- **Type**: `class`
- **Members**:
    - `system_prompt`: Returns a JSON formatted system prompt for documenting Python classes.
    - `user_prompt`: Generates a user prompt string for a given symbol, including its name and code.
    - `child_to_ir`: Maps a symbol's kind to its corresponding intermediate representation (IR) data type.
    - `child_to_field_name`: Maps a symbol's kind to its corresponding scope relation field name.
- **Description**: The `PyClassData` class is a specialized class for handling Python class documentation. It provides class methods to generate system and user prompts for documenting classes, and it maps symbols to their corresponding intermediate representation (IR) data types and field names based on their kind. This class is part of a larger framework for extracting and documenting Python code structures, and it inherits from `ClassData`, which likely provides foundational functionality for handling class-related data.
- **Inherits From**:
    - ClassData

**Methods**

---
#### PyClassData.child_to_field_name
The `child_to_field_name` function maps a `RawSymbolData` object's `symbol_kind` to a corresponding `ScopeRelation` value.
- **Inputs**:
    - `cls`: The class reference, typically used in class methods.
    - `child`: An instance of `RawSymbolData` representing a symbol with a specific kind.
- **Control Flow**:
    - A dictionary `mapping` is defined to map `SymbolKind` values to `ScopeRelation` values.
    - The function returns the value from the `mapping` dictionary corresponding to the `symbol_kind` of the `child` argument.
- **Output**:
    - The function returns a `ScopeRelation` value corresponding to the `symbol_kind` of the `child`, or `None` if no mapping exists.


---
#### PyClassData.child_to_ir
The `child_to_ir` function maps a `RawSymbolData` instance to a corresponding `IrData` type based on its `symbol_kind`.
- **Inputs**:
    - `cls`: The class reference, typically used for class methods.
    - `symbol`: An instance of `RawSymbolData` representing a symbol with a specific kind.
- **Control Flow**:
    - A dictionary `mapping` is defined to associate `SymbolKind` values with corresponding `IrData` types.
    - The function attempts to retrieve the `IrData` type from the `mapping` dictionary using the `symbol.symbol_kind` as the key.
- **Output**:
    - The function returns the corresponding `IrData` type if found in the mapping, otherwise it returns `None`.


---
#### PyClassData.system_prompt
The `system_prompt` function returns a predefined JSON schema string for documenting Python classes.
- **Inputs**:
    - `cls`: The class method's implicit first argument, representing the class itself.
- **Control Flow**:
    - The function directly returns the value of the constant `CLASSES_FOUND_SYSTEM_PROMPT_JSON`.
- **Output**:
    - A string containing a JSON schema for documenting Python classes.


---
#### PyClassData.user_prompt
The `user_prompt` function generates a formatted string prompt for a given symbol, including its name and code, and optionally the full file code if available.
- **Inputs**:
    - `cls`: The class reference, typically used in class methods to access class-level attributes or methods.
    - `symbol`: An instance of `RawSymbolData` containing information about a symbol, including its name, symbol code, and optionally the full file code.
- **Control Flow**:
    - Initialize `user_prompt` with a formatted string containing the class name and symbol code.
    - Check if `symbol.file_code` is present.
    - If `symbol.file_code` is present, append the full file code to `user_prompt`.
- **Output**:
    - A formatted string containing the class name, symbol code, and optionally the full file code.



---
### PyClassRawSymbolCollection 
- **Type**: `class`
- **Members**:
    - `data`: A dictionary mapping class names to their corresponding RawSymbolData.
- **Description**: The `PyClassRawSymbolCollection` class is a specialized collection for handling raw symbol data related to Python classes. It inherits from `RawSymbolCollection` and provides methods to extract and organize class symbols from Python code using static analysis. The class primarily focuses on identifying class symbols and their relationships, such as methods and nested classes, using ctags. It includes a method `from_static_analysis` to populate the collection based on the provided code and file path, and a `to_dict` method to return the stored data as a dictionary.
- **Inherits From**:
    - RawSymbolCollection

**Methods**

---
#### PyClassRawSymbolCollection.from_llm
The `from_llm` function raises a NotImplementedError indicating that static analysis should be used for Py classes.
- **Inputs**:
    - `cls`: The class on which this method is called, typically used to access class-level attributes or methods.
    - `code`: A string representing the code to be analyzed.
    - `root_rel_path`: A string representing the root relative path of the code to be analyzed.
- **Control Flow**:
    - The function immediately raises a NotImplementedError with a specific message.
- **Output**:
    - The function does not return any output as it raises an exception.


---
#### PyClassRawSymbolCollection.from_static_analysis
The `from_static_analysis` function analyzes Python code to extract class and method symbols using ctags and returns a collection of these symbols.
- **Inputs**:
    - `cls`: The class reference to which the method belongs, used to instantiate the output object.
    - `code`: A string containing the Python source code to be analyzed.
    - `root_rel_path`: A Path object representing the root-relative path of the file containing the code.
- **Control Flow**:
    - Determine if the code requires multi-prompt analysis using `code_requires_multi_prompt` function.
    - Extract symbols from the code using `extract_symbols_w_ctags`.
    - Initialize an empty dictionary `class_raw_symbol_data` to store class symbols.
    - Iterate over the extracted symbols and populate `class_raw_symbol_data` with class symbols using `create_raw_symbol_via_ctags`.
    - For each symbol, check if it has a scope and is not an anonymous symbol, then determine if it is a method or nested class and append it to the corresponding class in `class_raw_symbol_data`.
    - Return an instance of `cls` with the collected class symbol data if any symbols were found, otherwise return None.
- **Output**:
    - An instance of the class `cls` containing the extracted class and method symbols, or None if no symbols are found.


---
#### PyClassRawSymbolCollection.to_dict
The `to_dict` function returns the `data` attribute of the class instance as a dictionary.
- **Inputs**:
    - `self`: Refers to the instance of the class from which the method is called.
- **Control Flow**:
    - The function directly returns the `data` attribute of the instance.
- **Output**:
    - A dictionary where keys are strings and values are `RawSymbolData` objects.



---
### PyFnCollection 
- **Type**: `class`
- **Members**:
    - `data`: A dictionary mapping strings to either a PyFnData instance or a list of PyFnData instances.
- **Description**: The `PyFnCollection` class is a specialized collection that inherits from `IrCollection` and is designed to manage a collection of Python function data, represented by the `PyFnData` class. It provides a class method `from_llm` to create an instance of `PyFnCollection` using a language model (`llm`) and a list of raw symbols (`symbols_list`). This method leverages the `from_llm_with_ir_data` function to populate the collection with `PyFnData` instances, facilitating the organization and retrieval of function-related information.
- **Inherits From**:
    - IrCollection

**Methods**

---
#### PyFnCollection.from_llm
The `from_llm` function creates an instance of the class using data from a language model and a collection of raw symbols.
- **Inputs**:
    - `cls`: The class itself, used to call class methods.
    - `llm`: An instance of the ChatOpenAI class, representing a language model.
    - `symbols_list`: A collection of raw symbols, represented by the RawSymbolCollection class.
- **Control Flow**:
    - The function calls the class method `from_llm_with_ir_data` with `PyFnData`, `llm`, and `symbols_list` as arguments.
    - The result of the `from_llm_with_ir_data` method is returned.
- **Output**:
    - An instance of the class, initialized with data from the language model and the raw symbol collection.



---
### PyFnData 
- **Type**: `class`
- **Members**:
    - `system_prompt`: Returns a system prompt string for documenting functions.
    - `user_prompt`: Generates a user prompt string based on the provided symbol data.
    - `child_to_ir`: Raises NotImplementedError as functions should not have children.
    - `child_to_field_name`: Raises NotImplementedError as functions should not have children.
- **Description**: The `PyFnData` class is a specialized subclass of `FnData` designed to handle function-related data in a Python codebase. It provides class methods to generate system and user prompts for documenting functions, utilizing predefined JSON templates. The class also includes methods that raise `NotImplementedError` for handling child elements, as functions are not expected to have children in this context. This class is part of a larger framework for analyzing and documenting Python code, specifically focusing on functions.
- **Inherits From**:
    - FnData

**Methods**

---
#### PyFnData.child_to_field_name
The function `child_to_field_name` raises a `NotImplementedError` indicating that functions should not have children.
- **Inputs**:
    - `cls`: The class reference to which this method belongs.
    - `child`: An instance of `RawSymbolData` representing a child symbol.
- **Control Flow**:
    - The function immediately raises a `NotImplementedError` with a specific message.
- **Output**:
    - The function does not return any output as it raises an exception.


---
#### PyFnData.child_to_ir
The `child_to_ir` function raises a NotImplementedError indicating that functions should not have children.
- **Inputs**:
    - `cls`: The class object that the method is called on, typically representing the class itself.
    - `symbol`: An instance of RawSymbolData, representing the symbol data to be processed.
- **Control Flow**:
    - The function immediately raises a NotImplementedError with a specific message.
- **Output**:
    - The function does not return any value as it raises an exception.


---
#### PyFnData.system_prompt
The `system_prompt` function returns a predefined JSON schema string for documenting Python functions.
- **Inputs**:
    - `cls`: The class method's implicit first argument, representing the class itself.
- **Control Flow**:
    - The function directly returns the constant `FUNCTIONS_FOUND_SYSTEM_PROMPT_JSON`.
- **Output**:
    - A string containing a JSON schema for documenting Python functions.


---
#### PyFnData.user_prompt
The `user_prompt` function generates a formatted string containing a user prompt with the function name and code, and optionally includes the full file code if available.
- **Inputs**:
    - `cls`: The class reference, typically used in class methods to access class-level attributes or methods.
    - `symbol`: An instance of `RawSymbolData` containing information about the symbol, including its name, symbol code, and optionally the full file code.
- **Control Flow**:
    - Initialize a string `user_prompt` with a formatted message including the function name and code from the `symbol` object.
    - Check if `symbol.file_code` is present; if so, append the full file code to the `user_prompt` string.
- **Output**:
    - A formatted string that includes the function name, its code, and optionally the full file code.



---
### PyFnRawSymbolCollection 
- **Type**: `class`
- **Members**:
    - `data`: A dictionary mapping string keys to RawSymbolData objects.
- **Description**: The `PyFnRawSymbolCollection` class is a specialized collection for handling raw symbol data specifically related to Python functions. It inherits from `RawSymbolCollection` and provides methods for creating instances from static analysis of code, using ctags to extract function symbols. The class also includes a method to convert its data into a dictionary format. It is designed to work with static analysis and does not support creation from language model outputs, as indicated by the `NotImplementedError` in the `from_llm` method.
- **Inherits From**:
    - RawSymbolCollection

**Methods**

---
#### PyFnRawSymbolCollection.from_llm
The `from_llm` function raises a NotImplementedError indicating that static analysis should be used for Python functions.
- **Inputs**:
    - `cls`: The class on which this class method is called.
    - `code`: A string representing the code to be analyzed.
    - `root_rel_path`: A string representing the root relative path for the code.
- **Control Flow**:
    - The function immediately raises a NotImplementedError with a specific message.
- **Output**:
    - The function does not return any output as it raises an exception.


---
#### PyFnRawSymbolCollection.from_static_analysis
The `from_static_analysis` function performs a static analysis on the given code to extract callable symbols using ctags.
- **Inputs**:
    - `cls`: The class type that will be used to create the collection of symbols.
    - `code`: A string representing the source code to be analyzed.
    - `root_rel_path`: A Path object representing the root relative path of the source code file.
- **Control Flow**:
    - Calls the `default_ctags_analysis` function with the provided class type, code, and root relative path.
    - Specifies `SymbolKind.CALLABLE` to extract callable symbols from the code.
    - Uses `PY_FUNCTIONS` as the ctags kinds to filter for functions.
    - Sets the delimiter to '.' and `add_symbol_padding` to False.
- **Output**:
    - Returns an instance of the class type `cls` containing the extracted callable symbols, or None if no symbols are found.


---
#### PyFnRawSymbolCollection.to_dict
The `to_dict` function returns the `data` attribute of the class instance as a dictionary.
- **Inputs**:
    - `self`: Refers to the instance of the class containing the `to_dict` method.
- **Control Flow**:
    - The function accesses the `data` attribute of the class instance.
    - It returns the `data` attribute directly without any modification.
- **Output**:
    - A dictionary where keys are strings and values are `RawSymbolData` objects.



---
### PyVariableCollection 
- **Type**: `class`
- **Members**:
    - `data`: A dictionary mapping strings to either a single PyVariableData instance or a list of PyVariableData instances.
- **Description**: The `PyVariableCollection` class is a specialized collection class that inherits from `IrCollection` and is designed to manage a collection of `PyVariableData` objects. It provides a class method `from_llm` to create an instance of `PyVariableCollection` using a language model (`llm`) and a list of raw symbols (`symbols_list`). This class is part of a system that processes and organizes variable data extracted from Python code, facilitating the integration of language model outputs with intermediate representation data.
- **Inherits From**:
    - IrCollection

**Methods**

---
#### PyVariableCollection.from_llm
The `from_llm` function creates an instance of the class using data from a language model and a collection of raw symbols.
- **Inputs**:
    - `cls`: The class itself, which is used to call the class method.
    - `llm`: An instance of the ChatOpenAI class, representing the language model to be used.
    - `symbols_list`: A collection of raw symbols, represented by the RawSymbolCollection class, to be used in the instantiation process.
- **Control Flow**:
    - The function calls another class method `from_llm_with_ir_data` with `PyVariableData`, `llm`, and `symbols_list` as arguments.
    - The `from_llm_with_ir_data` method is responsible for creating and returning an instance of the class.
- **Output**:
    - The function returns an instance of the class it is called on, initialized with data from the language model and the raw symbol collection.



---
### PyVariableData 
- **Type**: `class`
- **Members**:
    - `system_prompt`: Returns a predefined system prompt for variable documentation.
    - `user_prompt`: Generates a user prompt string based on the provided symbol data.
    - `child_to_ir`: Raises an error as variables should not have children.
    - `child_to_field_name`: Raises an error as variables should not have children.
- **Description**: The `PyVariableData` class is a specialized class for handling variable data within a Python codebase, inheriting from `VariableData`. It provides class methods to generate system and user prompts for documenting variables, ensuring that the documentation process is consistent and automated. The class explicitly raises errors for methods related to child elements, as variables are not expected to have children in this context.
- **Inherits From**:
    - VariableData

**Methods**

---
#### PyVariableData.child_to_field_name
The `child_to_field_name` function raises an error indicating that variables should not have children.
- **Inputs**:
    - `cls`: The class object on which this method is called.
    - `child`: An instance of RawSymbolData representing a child symbol.
- **Control Flow**:
    - The function immediately raises a NotImplementedError with a specific message.
- **Output**:
    - The function does not return any value as it raises an exception.


---
#### PyVariableData.child_to_ir
The `child_to_ir` function raises a `NotImplementedError` indicating that variables should not have children.
- **Inputs**:
    - `cls`: The class object on which this method is called, typically a class method.
    - `symbol`: An instance of `RawSymbolData` representing the symbol data to be processed.
- **Control Flow**:
    - The function immediately raises a `NotImplementedError` with a specific message.
- **Output**:
    - The function does not return any value as it raises an exception.


---
#### PyVariableData.system_prompt
The `system_prompt` function returns a predefined JSON schema string for documenting variables.
- **Inputs**:
    - `cls`: The class method's implicit first argument, representing the class itself.
- **Control Flow**:
    - The function directly returns a constant string `VARIABLES_FOUND_SYSTEM_PROMPT_JSON`.
- **Output**:
    - A string containing a JSON schema for documenting variables.


---
#### PyVariableData.user_prompt
The `user_prompt` function generates a formatted string prompt for a given symbol, including its name, code, and optionally the full file code.
- **Inputs**:
    - `cls`: The class reference, typically used in class methods to access class-level attributes or methods.
    - `symbol`: An instance of `RawSymbolData` containing information about the symbol, such as its name, symbol code, and optionally the full file code.
- **Control Flow**:
    - Initialize a string `user_prompt` with a formatted message including the symbol's name and code.
    - Check if the symbol has associated file code.
    - If file code exists, append it to the `user_prompt` string.
- **Output**:
    - A formatted string containing the symbol's name, code, and optionally the full file code.



---
### PyVariableRawSymbolCollection 
- **Type**: `class`
- **Members**:
    - `data`: A dictionary mapping string keys to RawSymbolData objects.
- **Description**: The `PyVariableRawSymbolCollection` class is a specialized collection for handling raw symbol data specifically related to Python variables. It inherits from `RawSymbolCollection` and provides methods for creating instances from static analysis of code, using a default ctags analysis approach. The class is designed to store and manage raw symbol data for variables, facilitating the extraction and organization of variable-related information from Python code. It does not support creation from language model analysis, emphasizing its reliance on static analysis techniques.
- **Inherits From**:
    - RawSymbolCollection

**Methods**

---
#### PyVariableRawSymbolCollection.from_llm
The `from_llm` function raises a NotImplementedError indicating that static analysis should be used for Python variables.
- **Inputs**:
    - `cls`: The class on which this class method is called.
    - `code`: A string representing the code to be analyzed.
    - `root_rel_path`: A string representing the root relative path for the code.
- **Control Flow**:
    - The function immediately raises a NotImplementedError with a specific message.
- **Output**:
    - The function does not return any output as it raises an exception.


---
#### PyVariableRawSymbolCollection.from_static_analysis
The `from_static_analysis` function performs a static analysis on the given code to extract variable symbols using ctags.
- **Inputs**:
    - `cls`: The class type that will be used to create the collection of symbols.
    - `code`: A string containing the source code to be analyzed.
    - `root_rel_path`: A Path object representing the root relative path of the source code file.
- **Control Flow**:
    - Calls the `default_ctags_analysis` function with the provided class type, code, and root relative path.
    - Specifies the symbol kind as `SymbolKind.VARIABLE` and ctags kinds as `PY_VARIABLES`.
    - Sets the delimiter to '.' and enables symbol padding.
- **Output**:
    - Returns an instance of the class specified by `cls` containing the extracted variable symbols, or None if no symbols are found.


---
#### PyVariableRawSymbolCollection.to_dict
The `to_dict` function returns the `data` attribute of the instance as a dictionary.
- **Inputs**:
    - `self`: Refers to the instance of the class where this method is defined.
- **Control Flow**:
    - The function directly returns the `data` attribute of the instance without any additional processing.
- **Output**:
    - A dictionary where the keys are strings and the values are `RawSymbolData` objects.



