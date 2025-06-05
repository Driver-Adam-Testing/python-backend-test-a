# Purpose
This Python source code file is designed to facilitate the analysis and documentation of Verilog code, specifically focusing on modules, functions, tasks, and data types within Verilog files. It defines several classes that represent collections and individual data structures for Verilog modules, functions/tasks, and data types. These classes are used to generate detailed documentation by leveraging static analysis and potentially integrating with a language model (LLM) for enhanced insights. The file includes constants that categorize different Verilog constructs, such as modules, functions, tasks, data types, and ports, which are used to guide the analysis process.

The code is structured to provide a systematic approach to parsing and documenting Verilog code. It includes classes like `VerilogModuleData`, `VerilogFnTaskData`, and `VerilogDataTypeData`, each with methods to generate system and user prompts for documentation purposes. These classes are part of a broader framework that uses static analysis to extract symbols from Verilog code and then document them according to predefined JSON schemas. The file is not a standalone script but rather a library component intended to be integrated into a larger system that processes Verilog code, providing a structured way to document and understand the components of Verilog source files.
# Imports and Dependencies

---
- `pathlib`
- `typing`
- `utils.models`
- `ir_common`
- `symbol_common`


# Global Variables

---
### DATA_TYPES_FOUND_SYSTEM_PROMPT_JSON 
- **Type**: `str`
- **Description**: The variable `DATA_TYPES_FOUND_SYSTEM_PROMPT_JSON` is a string that contains a JSON schema template for documenting data types in Verilog code. This template is used to guide the documentation process by specifying the structure and content required for describing data types such as ports, registers, and net data types in Verilog.
- **Use**: This variable is used to provide a structured format for documenting Verilog data types in a consistent and detailed manner.


---
### DATA_TYPES_FOUND_USER_PROMPT 
- **Type**: `str`
- **Description**: `DATA_TYPES_FOUND_USER_PROMPT` is a string variable that contains a template for a user prompt. This prompt is used to guide the user in summarizing data types in Verilog code, specifically focusing on ports, registers, and net data types. The prompt provides instructions on how to describe these data types, emphasizing the need for detail that matches the complexity of the data type.
- **Use**: This variable is used to provide a structured prompt for users to document data types in Verilog code.


---
### FUNCTIONS_AND_TASKS_FOUND_SYSTEM_PROMPT_JSON 
- **Type**: `str`
- **Description**: The `FUNCTIONS_AND_TASKS_FOUND_SYSTEM_PROMPT_JSON` is a string variable that contains a JSON schema template. This template is used to guide the documentation process for functions and tasks in Verilog code. It specifies the structure and content required for documenting these elements, including inputs, control flow, and outputs.
- **Use**: This variable is used to provide a structured format for documenting Verilog functions and tasks.


---
### FUNCTIONS_AND_TASKS_FOUND_USER_PROMPT 
- **Type**: `str`
- **Description**: `FUNCTIONS_AND_TASKS_FOUND_USER_PROMPT` is a string variable that contains a template prompt for summarizing functions and tasks in Verilog code. It provides guidelines on how to describe Verilog functions and tasks, emphasizing the need for detail proportional to the complexity of the function or task.
- **Use**: This variable is used to generate user prompts for documenting Verilog functions and tasks.


---
### MODULES_FOUND_SYSTEM_PROMPT_JSON 
- **Type**: `str`
- **Description**: `MODULES_FOUND_SYSTEM_PROMPT_JSON` is a string variable that contains a JSON schema template for documenting Verilog modules. This template guides the documentation process by specifying the structure and content required for describing Verilog modules, including constants, ports, logic and control flow, and a brief description of the module.
- **Use**: This variable is used to provide a structured format for generating detailed documentation of Verilog modules.


---
### MODULES_FOUND_USER_PROMPT 
- **Type**: `str`
- **Description**: `MODULES_FOUND_USER_PROMPT` is a string variable that contains a template for generating user prompts related to summarizing Verilog modules. It provides a structured format for describing the components and functionality of Verilog modules, including their constants, ports, and logic and control flow.
- **Use**: This variable is used to generate user prompts for documenting Verilog modules in a structured JSON format.


---
### SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT 
- **Type**: `str`
- **Description**: `SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT` is a string variable that contains a detailed prompt for explaining the purpose of a large Verilog source code file. It guides the user to write a comprehensive explanation of the file's purpose, focusing on the functionality, technical components, and overall theme of the code.
- **Use**: This variable is used to instruct users on how to document the purpose of large Verilog source code files.


---
### SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_VERILOG 
- **Type**: `str`
- **Description**: The variable `SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_VERILOG` is a string that contains a detailed prompt for a Verilog programmer and technical documentation expert. It outlines the role of the expert in explaining Verilog code, focusing on technical details and the conceptual components and purpose of the software.
- **Use**: This variable is used as a system prompt to guide the generation of detailed documentation for large Verilog source code files.


---
### SOURCE_CODE_SMALL_PURPOSE_USER_PROMPT 
- **Type**: `str`
- **Description**: `SOURCE_CODE_SMALL_PURPOSE_USER_PROMPT` is a string variable that contains a template for a user prompt. This prompt is designed to guide users in explaining the purpose of a small Verilog source code file in a concise manner.
- **Use**: This variable is used to provide a structured prompt for users to describe the purpose of small Verilog source code files.


---
### SOURCE_CODE_SMALL_SYSTEM_PROMPT_GENERAL_VERILOG 
- **Type**: `str`
- **Description**: The variable `SOURCE_CODE_SMALL_SYSTEM_PROMPT_GENERAL_VERILOG` is a string that contains a system prompt for a Verilog programmer who is also a technical documentation expert. It emphasizes the need for clear and concise documentation of small and simple Verilog source code files.
- **Use**: This variable is used to provide a system prompt for generating documentation for small Verilog source code files.


---
### VERILOG_CONSTANTS 
- **Type**: `set`
- **Description**: `VERILOG_CONSTANTS` is a set containing a single string element, 'constant'. This set is used to categorize or identify Verilog constants within the codebase. It is part of a group of similar sets that categorize different Verilog constructs such as modules, functions, tasks, data types, and ports.
- **Use**: This variable is used to identify and categorize Verilog constants in the code.


---
### VERILOG_DATA_TYPES 
- **Type**: `set`
- **Description**: `VERILOG_DATA_TYPES` is a set containing strings that represent different data types used in Verilog, specifically 'register', 'net', and 'port'. These data types are fundamental in Verilog for defining how data is stored and transmitted within a hardware design.
- **Use**: This variable is used to categorize and identify Verilog data types during static analysis or documentation generation.


---
### VERILOG_FUNCTIONS_AND_TASKS 
- **Type**: `set`
- **Description**: `VERILOG_FUNCTIONS_AND_TASKS` is a set containing the strings 'function' and 'task'. This set is used to categorize and identify Verilog functions and tasks within the codebase. Functions in Verilog process a single input and return a single value, while tasks can handle multiple return values.
- **Use**: This variable is used to specify the kinds of callable entities (functions and tasks) that can be identified and processed in Verilog code analysis.


---
### VERILOG_MODULES 
- **Type**: `set`
- **Description**: `VERILOG_MODULES` is a global variable defined as a set containing a single string element, 'module'. This set is used to categorize or identify Verilog modules within the codebase.
- **Use**: This variable is used to specify the kind of Verilog symbols that are considered modules during static analysis.


---
### VERILOG_PORTS 
- **Type**: `set`
- **Description**: `VERILOG_PORTS` is a global variable defined as a set containing a single string element, 'port'. This set is part of a collection of constants that categorize different Verilog components, such as modules, functions, tasks, data types, and constants.
- **Use**: This variable is used to identify and categorize Verilog ports during static analysis or documentation generation.


# Classes

---
### VerilogDataTypeCollection 
- **Type**: `class`
- **Members**:
    - `data`: A dictionary mapping strings to either a VerilogDataTypeData instance or a list of such instances.
- **Description**: The VerilogDataTypeCollection class is a specialized collection class that inherits from IrCollection. It is designed to manage a collection of Verilog data types, represented by the VerilogDataTypeData class. The class provides a class method, from_llm, which facilitates the creation of a VerilogDataTypeCollection instance using a language model and a list of raw symbols, leveraging the from_llm_with_ir_data method to populate the collection with Verilog data type information.
- **Inherits From**:
    - IrCollection

**Methods**

---
#### VerilogDataTypeCollection.from_llm
The `from_llm` function creates an instance of the class using data from a language model and a collection of symbols.
- **Inputs**:
    - `llm`: An instance of the ChatOpenAI class, representing a language model.
    - `symbols_list`: A collection of raw symbols, represented by the RawSymbolCollection class.
- **Control Flow**:
    - The function calls another class method `from_llm_with_ir_data`, passing `VerilogDataTypeData`, `llm`, and `symbols_list` as arguments.
    - The `from_llm_with_ir_data` method is responsible for creating and returning an instance of the class.
- **Output**:
    - The function returns an instance of the class it is called on, initialized with data from the language model and symbol collection.



---
### VerilogDataTypeData 
- **Type**: `class`
- **Members**:
    - `system_prompt`: Returns a system prompt string for documenting Verilog data types.
    - `user_prompt`: Generates a user prompt string based on the provided symbol data.
    - `child_to_ir`: Raises a NotImplementedError indicating data types should not have children.
    - `child_to_field_name`: Raises a NotImplementedError indicating data types should not have children.
- **Description**: The `VerilogDataTypeData` class is designed to handle the documentation of Verilog data types, such as ports, registers, and nets, by providing system and user prompts for generating detailed documentation. It inherits from `VariableData` and includes class methods to generate prompts and handle child data, although it explicitly does not support children, as indicated by the NotImplementedError in the relevant methods.
- **Inherits From**:
    - VariableData

**Methods**

---
#### VerilogDataTypeData.child_to_field_name
The `child_to_field_name` function raises a `NotImplementedError` indicating that data types should not have children.
- **Inputs**:
    - `cls`: The class on which this method is called, typically a class method.
    - `child`: An instance of `RawSymbolData` representing a child symbol.
- **Control Flow**:
    - The function immediately raises a `NotImplementedError` with a specific message.
- **Output**:
    - The function does not return any value as it raises an exception.


---
#### VerilogDataTypeData.child_to_ir
The `child_to_ir` function raises a NotImplementedError indicating that data types should not have children.
- **Inputs**:
    - `cls`: The class on which this method is called, typically a subclass of IrData.
    - `symbol`: An instance of RawSymbolData representing the symbol data to be processed.
- **Control Flow**:
    - The function immediately raises a NotImplementedError with a specific message.
- **Output**:
    - The function does not return any value as it raises an exception.


---
#### VerilogDataTypeData.system_prompt
The `system_prompt` function returns a predefined JSON string for documenting Verilog data types.
- **Inputs**:
    - None
- **Control Flow**:
    - The function directly returns the constant `DATA_TYPES_FOUND_SYSTEM_PROMPT_JSON`.
- **Output**:
    - The function outputs a string containing JSON schema for documenting Verilog data types.


---
#### VerilogDataTypeData.user_prompt
The `user_prompt` function generates a formatted string prompt for a given Verilog symbol, including its name, code, and optionally the full file code.
- **Inputs**:
    - `cls`: The class method reference, typically not used directly in the function logic.
    - `symbol`: An instance of `RawSymbolData` containing the Verilog symbol's name, symbol code, and optionally the full file code.
- **Control Flow**:
    - Initialize `user_prompt` with a formatted string containing a predefined prompt, the symbol's name, and its symbol code.
    - Check if `symbol.file_code` is present; if so, append the full file code to `user_prompt`.
    - Return the constructed `user_prompt` string.
- **Output**:
    - A formatted string that includes the Verilog symbol's name, its code, and optionally the full file code if available.



---
### VerilogDataTypeRawSymbolCollection 
- **Type**: `class`
- **Members**:
    - `data`: A dictionary mapping string keys to either a single RawSymbolData or a list of RawSymbolData.
- **Description**: The VerilogDataTypeRawSymbolCollection class is a specialized collection for handling raw symbol data related to Verilog data types, such as registers, nets, and ports. It inherits from RawSymbolCollection and provides methods for creating instances from static analysis of Verilog code, specifically targeting variable symbols. The class also includes a method to convert its data into a dictionary format, facilitating easy access and manipulation of the raw symbol data.
- **Inherits From**:
    - RawSymbolCollection

**Methods**

---
#### VerilogDataTypeRawSymbolCollection.from_llm
The `from_llm` function is a class method that raises a NotImplementedError, indicating that static analysis should be used instead of LLM for Verilog.
- **Inputs**:
    - `code`: A string representing the Verilog code to be analyzed.
    - `root_rel_path`: A string representing the root relative path for the code.
- **Control Flow**:
    - The function immediately raises a NotImplementedError with the message 'Static analysis should be used for Verilog'.
- **Output**:
    - The function does not return any output as it raises an exception.


---
#### VerilogDataTypeRawSymbolCollection.from_static_analysis
The `from_static_analysis` function performs a static analysis on Verilog code to collect raw symbol data of a specified kind using ctags.
- **Inputs**:
    - `cls`: The class on which this method is called, typically a subclass of `RawSymbolCollection`.
    - `code`: A string containing the Verilog source code to be analyzed.
    - `root_rel_path`: A `Path` object representing the root relative path of the source code file.
- **Control Flow**:
    - The function calls `default_ctags_analysis` with the provided class, code, and root relative path.
    - It specifies the `symbol_kind` as `SymbolKind.VARIABLE` and the `ctags_kinds` as `VERILOG_DATA_TYPES`.
    - The function sets `delimiter` to `None` and `add_symbol_padding` to `False`.
- **Output**:
    - The function returns an instance of the class `cls` populated with raw symbol data collected from the static analysis of the provided Verilog code.


---
#### VerilogDataTypeRawSymbolCollection.to_dict
The `to_dict` function returns the `data` attribute of the class instance as a dictionary.
- **Inputs**:
    - None
- **Control Flow**:
    - The function directly returns the `data` attribute of the class instance without any additional processing or logic.
- **Output**:
    - A dictionary where the keys are strings and the values are `RawSymbolData` objects.



---
### VerilogFnTaskCollection 
- **Type**: `class`
- **Members**:
    - `data`: A dictionary mapping strings to VerilogFnTaskData or lists of VerilogFnTaskData.
- **Description**: The VerilogFnTaskCollection class is a specialized collection class that inherits from IrCollection. It is designed to manage and organize Verilog function and task data, represented by the VerilogFnTaskData class. The class provides a class method, from_llm, which facilitates the creation of a VerilogFnTaskCollection instance using a language model (llm) and a list of raw symbols. This method leverages the from_llm_with_ir_data function to populate the collection with relevant data.
- **Inherits From**:
    - IrCollection

**Methods**

---
#### VerilogFnTaskCollection.from_llm
The `from_llm` function creates an instance of the class using data from a language model and a collection of symbols.
- **Inputs**:
    - `llm`: An instance of the ChatOpenAI class, representing a language model.
    - `symbols_list`: A collection of raw symbols, represented by the RawSymbolCollection class.
- **Control Flow**:
    - The function calls `from_llm_with_ir_data` on the class, passing `VerilogFnTaskData`, `llm`, and `symbols_list` as arguments.
    - The `from_llm_with_ir_data` method is expected to return an instance of the class, which is then returned by the `from_llm` function.
- **Output**:
    - An instance of the class, initialized with data from the language model and the symbol collection.



---
### VerilogFnTaskData 
- **Type**: `class`
- **Members**:
    - `system_prompt`: Returns a system prompt string for documenting Verilog functions and tasks.
    - `user_prompt`: Generates a user prompt string based on the provided symbol data.
    - `child_to_ir`: Raises a NotImplementedError indicating functions should not have children.
    - `child_to_field_name`: Raises a NotImplementedError indicating functions should not have children.
- **Description**: The `VerilogFnTaskData` class is a specialized data class for handling Verilog functions and tasks, inheriting from `FnData`. It provides methods to generate system and user prompts for documenting these Verilog constructs. The class explicitly raises errors for methods related to child elements, as functions and tasks do not have children in this context.
- **Inherits From**:
    - FnData

**Methods**

---
#### VerilogFnTaskData.child_to_field_name
The `child_to_field_name` function raises a NotImplementedError indicating that functions should not have children.
- **Inputs**:
    - `cls`: The class object from which the method is called.
    - `child`: An instance of RawSymbolData representing a child symbol.
- **Control Flow**:
    - The function immediately raises a NotImplementedError with a specific message.
- **Output**:
    - The function does not return any value as it raises an exception.


---
#### VerilogFnTaskData.child_to_ir
The `child_to_ir` function raises a NotImplementedError indicating that functions should not have children.
- **Inputs**:
    - `cls`: The class on which this method is called, typically a subclass of IrData.
    - `symbol`: An instance of RawSymbolData representing a symbol to be converted to an intermediate representation (IR).
- **Control Flow**:
    - The function immediately raises a NotImplementedError with the message 'Functions should not have children'.
- **Output**:
    - The function does not return any value as it raises an exception.


---
#### VerilogFnTaskData.system_prompt
The `system_prompt` function returns a predefined JSON string for documenting Verilog functions and tasks.
- **Inputs**:
    - None
- **Control Flow**:
    - The function directly returns the constant `FUNCTIONS_AND_TASKS_FOUND_SYSTEM_PROMPT_JSON`.
- **Output**:
    - A string containing a JSON schema for documenting Verilog functions and tasks.


---
#### VerilogFnTaskData.user_prompt
The `user_prompt` function generates a formatted string prompt for a given Verilog symbol, including its name and code, and optionally the full file code if available.
- **Inputs**:
    - `cls`: The class reference, typically used in class methods to refer to the class itself.
    - `symbol`: An instance of `RawSymbolData` containing information about a Verilog symbol, including its name, symbol code, and optionally the full file code.
- **Control Flow**:
    - Initialize a string `user_prompt` with a predefined prompt template concatenated with the symbol's name and its code.
    - Check if the `symbol` has `file_code` available.
    - If `file_code` is available, append it to the `user_prompt` string with appropriate formatting.
    - Return the constructed `user_prompt` string.
- **Output**:
    - A formatted string that includes the symbol's name, its code, and optionally the full file code if it exists.



---
### VerilogFnTaskRawSymbolCollection 
- **Type**: `class`
- **Members**:
    - `data`: A dictionary mapping string keys to either a single RawSymbolData or a list of RawSymbolData.
- **Description**: The VerilogFnTaskRawSymbolCollection class is a specialized collection for handling raw symbol data related to Verilog functions and tasks. It inherits from RawSymbolCollection and provides methods for creating instances from static analysis of Verilog code, specifically targeting callable symbols like functions and tasks. The class does not support creation from language model analysis, emphasizing the use of static analysis for Verilog. It also includes a method to convert the stored data into a dictionary format.
- **Inherits From**:
    - RawSymbolCollection

**Methods**

---
#### VerilogFnTaskRawSymbolCollection.from_llm
The `from_llm` function is a class method that raises a NotImplementedError, indicating that static analysis should be used instead of LLM for Verilog.
- **Inputs**:
    - `code`: A string representing the Verilog code to be analyzed.
    - `root_rel_path`: A string representing the root relative path for the code.
- **Control Flow**:
    - The function immediately raises a NotImplementedError with a message indicating that static analysis should be used for Verilog.
- **Output**:
    - The function does not return any output as it raises an exception.


---
#### VerilogFnTaskRawSymbolCollection.from_static_analysis
The `from_static_analysis` function performs a static analysis on Verilog code to identify callable symbols such as functions and tasks.
- **Inputs**:
    - `cls`: The class on which this method is called, typically a subclass of `RawSymbolCollection`.
    - `code`: A string containing the Verilog source code to be analyzed.
    - `root_rel_path`: A `Path` object representing the root relative path of the source code file.
- **Control Flow**:
    - The function calls `default_ctags_analysis` with the provided class, code, and path, specifying `SymbolKind.CALLABLE` to focus on callable symbols.
    - It uses `VERILOG_FUNCTIONS_AND_TASKS` to filter for Verilog functions and tasks.
    - The function sets `delimiter` to `None` and `add_symbol_padding` to `False` to configure the analysis behavior.
- **Output**:
    - The function returns an instance of the class `cls`, populated with the results of the static analysis for callable symbols in the provided Verilog code.


---
#### VerilogFnTaskRawSymbolCollection.to_dict
The `to_dict` function returns the `data` attribute of the class instance as a dictionary mapping strings to `RawSymbolData` objects.
- **Inputs**:
    - None
- **Control Flow**:
    - The function directly returns the `data` attribute of the class instance without any additional processing or logic.
- **Output**:
    - A dictionary where keys are strings and values are `RawSymbolData` objects, representing the data stored in the class instance.



---
### VerilogModuleCollection 
- **Type**: `class`
- **Members**:
    - `data`: A dictionary mapping strings to VerilogModuleData or lists of VerilogModuleData.
- **Description**: The VerilogModuleCollection class is a specialized collection class that inherits from IrCollection and is designed to manage a collection of VerilogModuleData objects. It provides a class method, from_llm, which facilitates the creation of a VerilogModuleCollection instance using a language model (llm) and a list of raw symbols. This class is part of a system that processes and organizes Verilog module data, likely for analysis or documentation purposes.
- **Inherits From**:
    - IrCollection

**Methods**

---
#### VerilogModuleCollection.from_llm
The `from_llm` function creates an instance of the class using data from a language model and a collection of symbols.
- **Inputs**:
    - `llm`: An instance of the `ChatOpenAI` class, representing a language model.
    - `symbols_list`: An instance of `RawSymbolCollection`, representing a collection of symbols to be used in the instantiation process.
- **Control Flow**:
    - The function calls `cls.from_llm_with_ir_data` with `VerilogModuleData`, `llm`, and `symbols_list` as arguments.
    - The function returns the result of the `cls.from_llm_with_ir_data` call, which is an instance of the class.
- **Output**:
    - The function returns an instance of the class it is called on, initialized with data from the language model and the symbol collection.



---
### VerilogModuleData 
- **Type**: `class`
- **Members**:
    - `description`: Holds the raw content description of the Verilog module.
    - `constants`: Stores a list of constants with their descriptions, excluding None values.
    - `ports`: Contains a list of ports with their descriptions, allowing None values.
    - `logic_and_control_flow`: Includes a list of logic and control flow elements, allowing None values.
- **Description**: The `VerilogModuleData` class is a specialized data structure for representing Verilog modules within an intermediate representation (IR) framework. It extends the `IrData` class and encapsulates details about a Verilog module, including its description, constants, ports, and logic and control flow elements. The class provides class methods for generating system and user prompts for documentation purposes, and it enforces that modules should not have children by raising `NotImplementedError` for related methods. It also includes a method to create a default instance of the class with empty or default values for its attributes.
- **Inherits From**:
    - IrData

**Methods**

---
#### VerilogModuleData.child_to_field_name
The `child_to_field_name` function raises a NotImplementedError indicating that modules should not have children.
- **Inputs**:
    - `cls`: The class reference from which the method is called.
    - `child`: An instance of RawSymbolData representing a child symbol.
- **Control Flow**:
    - The function immediately raises a NotImplementedError with the message 'Modules should not have children'.
- **Output**:
    - The function does not return any value as it raises an exception.


---
#### VerilogModuleData.child_to_ir
The `child_to_ir` function raises a NotImplementedError indicating that modules should not have children.
- **Inputs**:
    - `cls`: The class on which this method is called, typically a subclass of IrData.
    - `symbol`: An instance of RawSymbolData representing a symbol in the code.
- **Control Flow**:
    - The function immediately raises a NotImplementedError with the message 'Modules should not have children'.
- **Output**:
    - The function does not return any value as it raises an exception.


---
#### VerilogModuleData.default_instance
The `default_instance` function creates and returns a default instance of the class with empty or default values for its attributes.
- **Inputs**:
    - `cls`: The class for which a default instance is to be created.
- **Control Flow**:
    - The function is a class method, indicated by the use of `cls` as the first parameter.
    - It returns an instance of the class `cls` by calling its constructor with specific default values for its attributes.
    - The attributes `description`, `constants`, `ports`, and `logic_and_control_flow` are initialized with instances of specific classes, each having empty or default content.
- **Output**:
    - An instance of the class `cls` with default values for its attributes.


---
#### VerilogModuleData.system_prompt
The `system_prompt` function returns a predefined JSON string for documenting Verilog modules.
- **Inputs**:
    - None
- **Control Flow**:
    - The function directly returns the value of the constant `MODULES_FOUND_SYSTEM_PROMPT_JSON`.
- **Output**:
    - The function outputs a string containing a JSON schema for documenting Verilog modules.


---
#### VerilogModuleData.user_prompt
The `user_prompt` function generates a formatted string prompt for documenting a Verilog module using the provided symbol data.
- **Inputs**:
    - `cls`: The class reference, typically used in class methods.
    - `symbol`: An instance of `RawSymbolData` containing the name, symbol code, and optionally the full file code of a Verilog module.
- **Control Flow**:
    - Initialize the `user_prompt` string with a predefined prompt template and the module's name and code from the `symbol` object.
    - Check if the `symbol` object contains `file_code`; if so, append the full file code to the `user_prompt` string.
- **Output**:
    - Returns a formatted string that includes the module's name, symbol code, and optionally the full file code, intended for use as a documentation prompt.



---
### VerilogModuleRawSymbolCollection 
- **Type**: `class`
- **Members**:
    - `data`: A dictionary mapping string keys to RawSymbolData or lists of RawSymbolData.
- **Description**: The VerilogModuleRawSymbolCollection class is a specialized collection for handling raw symbol data related to Verilog modules. It inherits from RawSymbolCollection and provides methods for creating instances from static analysis of Verilog code. The class is designed to work with Verilog module symbols, utilizing static analysis to populate its data structure, and it does not support creation from language model analysis, as indicated by the NotImplementedError in the from_llm method.
- **Inherits From**:
    - RawSymbolCollection

**Methods**

---
#### VerilogModuleRawSymbolCollection.from_llm
The `from_llm` function is a class method that raises a NotImplementedError, indicating that static analysis should be used instead of LLM for Verilog.
- **Inputs**:
    - `code`: A string representing the Verilog code to be analyzed.
    - `root_rel_path`: A string representing the root relative path of the Verilog code file.
- **Control Flow**:
    - The function immediately raises a NotImplementedError with a message indicating that static analysis should be used for Verilog.
- **Output**:
    - The function does not return any output as it raises an exception.


---
#### VerilogModuleRawSymbolCollection.from_static_analysis
The `from_static_analysis` function performs a static analysis on Verilog code to collect module symbols using ctags.
- **Inputs**:
    - `code`: A string containing the Verilog source code to be analyzed.
    - `root_rel_path`: A Path object representing the root relative path of the source code file.
- **Control Flow**:
    - The function calls `default_ctags_analysis` with the provided class, code, and root relative path.
    - It specifies the symbol kind as `SymbolKind.MODULE` and the ctags kinds as `VERILOG_MODULES`.
    - The function sets the delimiter to `None` and `add_symbol_padding` to `False`.
- **Output**:
    - The function returns an instance of the class `cls` populated with module symbols extracted from the static analysis of the provided Verilog code.


---
#### VerilogModuleRawSymbolCollection.to_dict
The `to_dict` function returns the `data` attribute of the class instance as a dictionary.
- **Inputs**:
    - `self`: The instance of the class containing the `data` attribute.
- **Control Flow**:
    - The function directly returns the `data` attribute of the class instance without any additional processing.
- **Output**:
    - A dictionary where the keys are strings and the values are `RawSymbolData` objects.



