# Purpose
This Python source code file is designed to facilitate the extraction and documentation of various components from assembly code using a language model (LLM). It defines a series of classes and methods that handle the identification and documentation of data structures, subroutines, macros, and variables within assembly code. The file is structured around the concept of symbol collections, where each type of assembly component (e.g., data structures, subroutines) has a corresponding class that manages its extraction and conversion into a documented format. The classes utilize prompts to interact with the LLM, guiding it to extract relevant information and format it according to predefined JSON schemas.

The file is organized into two main sections: symbol extraction classes and intermediate representation (IR) classes. The symbol extraction classes, such as `AssemblyDataStructureRawSymbolCollection` and `AssemblySubroutineRawSymbolCollection`, are responsible for using the LLM to identify and collect raw symbols from the assembly code. The IR classes, like `AssemblyDataStructureData` and `AssemblySubroutineData`, then take these raw symbols and convert them into a structured format that can be used for documentation purposes. This file is intended to be part of a larger system that automates the documentation of assembly code, providing a clear and structured approach to extracting and describing the various components within the code.
# Imports and Dependencies

---
- `pathlib.Path`
- `typing.Self`
- `utils.models.ChatOpenAI`
- `default_llm_analysis`
- `DataStructureData`
- `FnData`
- `IrCollection`
- `IrData`
- `VariableData`
- `RawSymbolCollection`
- `RawSymbolData`
- `SymbolKind`


# Global Variables

---
### DATA_STRUCTURES_CHECKER_SYSTEM_PROMPT_JSON 
- **Type**: `str`
- **Description**: The variable `DATA_STRUCTURES_CHECKER_SYSTEM_PROMPT_JSON` is a string that contains a JSON schema template. This template is used to instruct a system to list important data structures defined in a given assembly code. It specifies that the response should be a JSON array of data structure names.
- **Use**: This variable is used as a system prompt for extracting data structures from assembly code using a language model.


---
### DATA_STRUCTURES_FOUND_SYSTEM_PROMPT_JSON 
- **Type**: `str`
- **Description**: The variable `DATA_STRUCTURES_FOUND_SYSTEM_PROMPT_JSON` is a string that contains a JSON schema template. This template is used to guide the documentation process for data structures found in assembly code. It specifies the format and content required for documenting data structures, including their type, members, and a description.
- **Use**: This variable is used to provide a structured format for documenting data structures in assembly code.


---
### DATA_STRUCTURES_FOUND_USER_PROMPT 
- **Type**: `str`
- **Description**: The variable `DATA_STRUCTURES_FOUND_USER_PROMPT` is a string that contains a template for summarizing data structures in a given code. It provides guidelines on how to describe data structures, emphasizing the importance of matching the complexity of the description to the complexity of the data structure itself.
- **Use**: This variable is used to prompt users to summarize data structures in code, ensuring detailed and appropriate documentation.


---
### FUNCTIONS_CHECKER_SYSTEM_PROMPT_JSON 
- **Type**: `str`
- **Description**: `FUNCTIONS_CHECKER_SYSTEM_PROMPT_JSON` is a string variable that contains a JSON schema template. This template is used to list functions, subroutines, or procedures defined in assembly code. It specifies the format for the response, ensuring that only fully defined and implemented functions are included.
- **Use**: This variable is used as a system prompt to guide the extraction of function-related information from assembly code.


---
### FUNCTIONS_FOUND_SYSTEM_PROMPT_JSON 
- **Type**: `str`
- **Description**: `FUNCTIONS_FOUND_SYSTEM_PROMPT_JSON` is a string variable that contains a JSON schema template. This template is used to guide the documentation of functions, subroutines, or procedures in assembly code. It specifies the structure and fields required for documenting these elements, including a single sentence description, inputs, control flow, and output.
- **Use**: This variable is used to provide a structured format for documenting functions in assembly code.


---
### FUNCTIONS_FOUND_USER_PROMPT 
- **Type**: `str`
- **Description**: `FUNCTIONS_FOUND_USER_PROMPT` is a string variable that contains a template for summarizing functions, subroutines, or procedures in assembly code. It provides guidelines on how to describe the inputs, control flow, and output of a function, with an emphasis on matching the detail to the complexity of the function.
- **Use**: This variable is used to generate prompts for documenting functions in assembly code.


---
### IMPORTS_SYSTEM_PROMPT_JSON 
- **Type**: `str`
- **Description**: `IMPORTS_SYSTEM_PROMPT_JSON` is a string variable that contains a JSON schema template. This template is used to identify and list the imports and dependencies in a given code snippet. The schema specifies that the response should be a JSON object with a single key, `data`, which is an array of import names.
- **Use**: This variable is used to guide the extraction of import statements from code by providing a structured format for the output.


---
### MACRO_CHECKER_SYSTEM_PROMPT_JSON 
- **Type**: `str`
- **Description**: `MACRO_CHECKER_SYSTEM_PROMPT_JSON` is a string variable that contains a JSON schema prompt for identifying macros in assembly code. This prompt is used to instruct a language model to list macros defined in a given assembly code snippet.
- **Use**: This variable is used to provide a structured prompt for extracting macro definitions from assembly code using a language model.


---
### MACRO_FOUND_SYSTEM_PROMPT_JSON 
- **Type**: `str`
- **Description**: `MACRO_FOUND_SYSTEM_PROMPT_JSON` is a string variable that contains a JSON schema template. This template is used to describe macros in assembly code, focusing on inputs, control flow, and output. It is part of a system designed to generate detailed documentation for assembly macros.
- **Use**: This variable is used to provide a structured format for documenting macros in assembly code.


---
### MACRO_FOUND_USER_PROMPT 
- **Type**: `str`
- **Description**: `MACRO_FOUND_USER_PROMPT` is a string variable that contains a template for summarizing macros in assembly code. It provides a structured prompt for describing the inputs, control flow, logic, and output of a macro.
- **Use**: This variable is used to guide the documentation process for macros in assembly code by providing a consistent format for summarization.


---
### SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT 
- **Type**: `str`
- **Description**: `SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT` is a string variable that contains a multi-paragraph prompt intended for users to explain the purpose of a given assembly source code file. The prompt guides users to provide a detailed explanation without speculative language and suggests considering specific questions to frame their response.
- **Use**: This variable is used to prompt users to provide a comprehensive explanation of the purpose of an assembly source code file.


---
### SOURCE_CODE_SMALL_PURPOSE_USER_PROMPT 
- **Type**: `str`
- **Description**: `SOURCE_CODE_SMALL_PURPOSE_USER_PROMPT` is a string variable that contains a template for generating a concise explanation of a source code file's purpose. It provides guidance on how to structure the explanation, focusing on the scope and key technical components of the code.
- **Use**: This variable is used to prompt users to provide a brief and focused description of a source code file's purpose.


---
### SOURCE_CODE_SYSTEM_PROMPT_GENERAL_DEFAULT 
- **Type**: `string`
- **Description**: The variable `SOURCE_CODE_SYSTEM_PROMPT_GENERAL_DEFAULT` is a string that contains a detailed prompt for a software engineering documentation expert. It outlines the role of the expert in explaining software, focusing on technical details and key conceptual components.
- **Use**: This variable is used as a system prompt for guiding documentation experts in their task of explaining software code.


---
### VARIABLES_CHECKER_SYSTEM_PROMPT_JSON 
- **Type**: `str`
- **Description**: `VARIABLES_CHECKER_SYSTEM_PROMPT_JSON` is a string variable that contains a JSON schema formatted prompt. This prompt is used to instruct a system to list any global variables defined in a given assembly code. The prompt specifies the format in which the response should be returned, ensuring consistency in the output.
- **Use**: This variable is used to provide a structured prompt for extracting global variable names from assembly code.


---
### VARIABLES_FOUND_SYSTEM_PROMPT_JSON 
- **Type**: `str`
- **Description**: `VARIABLES_FOUND_SYSTEM_PROMPT_JSON` is a string variable that contains a JSON schema template. This template is used to guide the documentation of global variables found in assembly code. It specifies the format for describing the type, description, and use of a variable.
- **Use**: This variable is used to provide a structured format for documenting global variables in assembly code.


---
### VARIABLES_FOUND_USER_PROMPT 
- **Type**: `str`
- **Description**: `VARIABLES_FOUND_USER_PROMPT` is a string variable that contains a template prompt for summarizing a global variable in a given code. It provides instructions on how to describe a global variable, emphasizing the need for detail that matches the complexity of the variable.
- **Use**: This variable is used to provide a consistent prompt for summarizing global variables in code documentation.


# Classes

---
### AssemblyDataStructureCollection 
- **Type**: `class`
- **Members**:
    - `data`: A dictionary mapping strings to either a single AssemblyDataStructureData instance or a list of such instances.
- **Description**: The `AssemblyDataStructureCollection` class is a specialized collection class that inherits from `IrCollection`. It is designed to manage a collection of assembly data structures, represented by the `AssemblyDataStructureData` class. The class provides a class method `from_llm` which facilitates the creation of an instance of `AssemblyDataStructureCollection` by leveraging a language model (LLM) and a collection of raw symbols. This method utilizes the `from_llm_with_ir_data` method to transform raw symbol data into intermediate representation (IR) data, specifically for assembly data structures.
- **Inherits From**:
    - IrCollection

**Methods**

---
#### AssemblyDataStructureCollection.from_llm
The `from_llm` function creates an instance of the class using LLM data and a list of symbols.
- **Inputs**:
    - `llm`: An instance of the `ChatOpenAI` class, representing a language model used for processing.
    - `symbols_list`: An instance of `RawSymbolCollection`, representing a collection of symbols to be used in the process.
- **Control Flow**:
    - The function calls `from_llm_with_ir_data` on the class, passing `AssemblyDataStructureData`, `llm`, and `symbols_list` as arguments.
- **Output**:
    - The function returns an instance of the class initialized with the provided LLM data and symbols list.



---
### AssemblyDataStructureData 
- **Type**: `class`
- **Members**:
    - `system_prompt`: Returns a predefined system prompt for documenting data structures.
    - `user_prompt`: Generates a user prompt string for a given symbol, including its name and code.
    - `child_to_ir`: Raises a NotImplementedError as assembly data structures should not have children.
    - `child_to_field_name`: Raises a NotImplementedError as assembly data structures should not have children.
- **Description**: The `AssemblyDataStructureData` class is a specialized class for handling assembly data structures within a documentation framework. It inherits from `DataStructureData` and provides class methods to generate system and user prompts for documenting assembly data structures. The class explicitly raises `NotImplementedError` for methods related to child data structures, indicating that assembly data structures are not expected to have children in this context.
- **Inherits From**:
    - DataStructureData

**Methods**

---
#### AssemblyDataStructureData.child_to_field_name
The `child_to_field_name` function raises an error indicating that assembly data structures should not have children.
- **Inputs**:
    - `cls`: The class object from which the method is called.
    - `child`: An instance of `RawSymbolData` representing a child symbol.
- **Control Flow**:
    - The function immediately raises a `NotImplementedError` with a specific message.
- **Output**:
    - The function does not return any value as it raises an exception.


---
#### AssemblyDataStructureData.child_to_ir
The `child_to_ir` function raises a `NotImplementedError` indicating that assembly data structures should not have children.
- **Inputs**:
    - `cls`: The class type from which the method is called, typically a class method.
    - `symbol`: An instance of `RawSymbolData` representing a symbol in the assembly code.
- **Control Flow**:
    - The function immediately raises a `NotImplementedError` with a specific message.
- **Output**:
    - The function does not return any value as it raises an exception.


---
#### AssemblyDataStructureData.system_prompt
The `system_prompt` function returns a predefined JSON string for documenting data structures in assembly code.
- **Inputs**:
    - None
- **Control Flow**:
    - The function directly returns the constant `DATA_STRUCTURES_FOUND_SYSTEM_PROMPT_JSON`.
- **Output**:
    - The function outputs a string containing a JSON schema for documenting data structures.


---
#### AssemblyDataStructureData.user_prompt
The `user_prompt` function generates a formatted string that includes a predefined prompt and the details of a given symbol.
- **Inputs**:
    - `cls`: The class reference from which the method is called, typically used in class methods.
    - `symbol`: An instance of `RawSymbolData` containing the name and file code of a symbol to be documented.
- **Control Flow**:
    - The function constructs a string by concatenating a predefined prompt (`DATA_STRUCTURES_FOUND_USER_PROMPT`) with the name of the symbol and its associated file code.
    - The function returns the constructed string.
- **Output**:
    - A formatted string that includes a prompt, the symbol's name, and its file code.



---
### AssemblyDataStructureRawSymbolCollection 
- **Type**: `class`
- **Members**:
    - `data`: A dictionary mapping string keys to RawSymbolData objects.
- **Description**: The `AssemblyDataStructureRawSymbolCollection` class is a specialized collection for handling raw symbol data related to assembly data structures. It inherits from `RawSymbolCollection` and provides methods for creating instances from static analysis or using a language model (LLM) for extraction. The class stores its data in a dictionary and can convert this data to a dictionary format. The `from_static_analysis` method is not implemented, indicating that static analysis is not supported, while the `from_llm` method utilizes a default LLM analysis function to populate the collection.
- **Inherits From**:
    - RawSymbolCollection

**Methods**

---
#### AssemblyDataStructureRawSymbolCollection.from_llm
The `from_llm` function performs a default LLM analysis to extract data structures from assembly code using a specified system prompt.
- **Inputs**:
    - `cls`: The class on which this method is called, typically a subclass of `RawSymbolCollection`.
    - `llm`: An instance of `ChatOpenAI` used for language model-based analysis.
    - `code`: A string containing the assembly code to be analyzed.
    - `root_rel_path`: A string representing the root relative path of the code file.
- **Control Flow**:
    - Calls the `default_llm_analysis` function with the provided class, LLM instance, code, root relative path, and specific prompts for data structure extraction.
    - Passes the `SymbolKind.DATA_STRUCTURE` to specify the kind of symbols to be extracted.
- **Output**:
    - Returns the result of the `default_llm_analysis` function, which is either an instance of the class or `None` if the analysis fails.


---
#### AssemblyDataStructureRawSymbolCollection.from_static_analysis
The `from_static_analysis` function is a class method placeholder for parsing assembly code using static analysis, which is not implemented and raises a NotImplementedError.
- **Inputs**:
    - `cls`: The class on which this method is called, typically the class itself.
    - `code`: A string representing the assembly code to be analyzed.
    - `root_rel_path`: A Path object representing the root relative path of the code file.
- **Control Flow**:
    - The function immediately raises a NotImplementedError with a message indicating that assembly parsing uses LLM extraction instead of static analysis.
- **Output**:
    - The function does not return any output as it raises an exception.


---
#### AssemblyDataStructureRawSymbolCollection.to_dict
The `to_dict` function returns the `data` attribute of the class instance as a dictionary.
- **Inputs**:
    - None
- **Control Flow**:
    - The function directly returns the `data` attribute of the class instance.
- **Output**:
    - A dictionary where keys are strings and values are `RawSymbolData` objects.



---
### AssemblyMacroCollection 
- **Type**: `class`
- **Members**:
    - `data`: A dictionary mapping strings to either a single AssemblyMacroData instance or a list of such instances.
- **Description**: The `AssemblyMacroCollection` class is a specialized collection designed to manage and store assembly macro data. It inherits from `IrCollection` and utilizes a dictionary to hold its data, where each key is a string and the value is either an `AssemblyMacroData` object or a list of such objects. The class provides a class method `from_llm` to create an instance of `AssemblyMacroCollection` by leveraging a language model (LLM) and a list of raw symbols, facilitating the conversion of raw symbol data into intermediate representation (IR) data specific to assembly macros.
- **Inherits From**:
    - IrCollection

**Methods**

---
#### AssemblyMacroCollection.from_llm
The `from_llm` function creates an instance of the class using LLM data and a collection of symbols.
- **Inputs**:
    - `llm`: An instance of the `ChatOpenAI` class, representing a language model used for processing.
    - `symbols_list`: An instance of `RawSymbolCollection`, representing a collection of raw symbols to be used in the process.
- **Control Flow**:
    - The function calls `from_llm_with_ir_data` on the class, passing `AssemblyMacroData`, `llm`, and `symbols_list` as arguments.
- **Output**:
    - The function returns an instance of the class initialized with the provided LLM data and symbols list.



---
### AssemblyMacroData 
- **Type**: `class`
- **Members**:
    - `system_prompt`: Returns a predefined system prompt for documenting macros.
    - `user_prompt`: Generates a user prompt string using the provided symbol's name and file code.
    - `child_to_ir`: Raises a NotImplementedError indicating that assembly macros should not have children.
    - `child_to_field_name`: Raises a NotImplementedError indicating that assembly macros should not have children.
- **Description**: The `AssemblyMacroData` class is a specialized subclass of `FnData` designed to handle the documentation of assembly macros. It provides class methods to generate system and user prompts for macro documentation, ensuring that the correct context and information are used when documenting these macros. The class explicitly raises errors for methods related to child elements, as assembly macros are not expected to have children, reflecting its focus on standalone macro documentation.
- **Inherits From**:
    - FnData

**Methods**

---
#### AssemblyMacroData.child_to_field_name
The `child_to_field_name` function raises an error indicating that assembly macros should not have children.
- **Inputs**:
    - `cls`: The class type that the method is bound to, typically used to access class-level attributes or methods.
    - `child`: An instance of `RawSymbolData` representing a child symbol that is not expected to exist for assembly macros.
- **Control Flow**:
    - The function immediately raises a `NotImplementedError` with a specific message.
- **Output**:
    - The function does not return any value as it raises an exception.


---
#### AssemblyMacroData.child_to_ir
The `child_to_ir` function raises a `NotImplementedError` indicating that assembly macros should not have children.
- **Inputs**:
    - `cls`: The class type on which this method is called, typically a class method.
    - `symbol`: An instance of `RawSymbolData` representing the symbol data to be processed.
- **Control Flow**:
    - The function immediately raises a `NotImplementedError` with a specific message.
- **Output**:
    - The function does not return any value as it raises an exception.


---
#### AssemblyMacroData.system_prompt
The `system_prompt` function returns a predefined JSON string for macro documentation.
- **Inputs**:
    - None
- **Control Flow**:
    - The function directly returns the constant `MACRO_FOUND_SYSTEM_PROMPT_JSON`.
- **Output**:
    - The output is a string containing JSON schema instructions for documenting macros.


---
#### AssemblyMacroData.user_prompt
The `user_prompt` function generates a formatted string containing a user prompt and the associated code from a given symbol.
- **Inputs**:
    - `cls`: The class reference, typically used in class methods.
    - `symbol`: An instance of `RawSymbolData` containing the name and file code of a symbol.
- **Control Flow**:
    - The function constructs a string by concatenating a predefined macro prompt with the symbol's name.
    - It appends two newline characters followed by the label 'Code:' and another two newline characters.
    - Finally, it appends the file code from the symbol to the constructed string.
- **Output**:
    - The function returns a formatted string that includes the macro prompt, the symbol's name, and its associated code.



---
### AssemblyMacroRawSymbolCollection 
- **Type**: `class`
- **Members**:
    - `data`: A dictionary mapping string keys to RawSymbolData objects.
- **Description**: The `AssemblyMacroRawSymbolCollection` class is a specialized collection for handling raw symbol data related to assembly macros. It inherits from `RawSymbolCollection` and provides methods for creating instances from static analysis or using a language model (LLM) for analysis. The class is designed to facilitate the extraction and management of macro symbols in assembly code, leveraging LLMs for parsing and analysis. It includes a method to convert the collection data into a dictionary format.
- **Inherits From**:
    - RawSymbolCollection

**Methods**

---
#### AssemblyMacroRawSymbolCollection.from_llm
The `from_llm` function performs a default LLM analysis using specified parameters to extract callable symbols from code.
- **Inputs**:
    - `cls`: The class on which this method is called, typically a subclass of `RawSymbolCollection`.
    - `llm`: An instance of `ChatOpenAI`, representing the language model to be used for analysis.
    - `code`: A string containing the source code to be analyzed.
    - `root_rel_path`: A string representing the root relative path of the source code file.
- **Control Flow**:
    - Calls the `default_llm_analysis` function with the provided class, LLM instance, code, root relative path, and additional parameters.
    - Passes `MACRO_CHECKER_SYSTEM_PROMPT_JSON` as the system prompt and an empty string as the user prompt.
    - Specifies `SymbolKind.CALLABLE` to indicate the type of symbols to be extracted.
- **Output**:
    - Returns the result of the `default_llm_analysis` function, which is either an instance of the class `cls` or `None` if the analysis fails.


---
#### AssemblyMacroRawSymbolCollection.from_static_analysis
The `from_static_analysis` function is a placeholder for a method intended to perform static analysis on assembly code, but it currently raises a NotImplementedError.
- **Inputs**:
    - `cls`: The class on which this class method is called, typically a subclass of RawSymbolCollection.
    - `code`: A string representing the assembly code to be analyzed.
    - `root_rel_path`: A Path object representing the root relative path of the code file.
- **Control Flow**:
    - The function immediately raises a NotImplementedError with a message indicating that assembly parsing uses LLM extraction.
- **Output**:
    - The function does not return any output as it raises an exception immediately.


---
#### AssemblyMacroRawSymbolCollection.to_dict
The `to_dict` function returns the `data` attribute of the class instance as a dictionary.
- **Inputs**:
    - None
- **Control Flow**:
    - The function directly returns the `data` attribute of the class instance.
- **Output**:
    - A dictionary where the keys are strings and the values are `RawSymbolData` objects.



---
### AssemblySubroutineCollection 
- **Type**: `class`
- **Members**:
    - `data`: A dictionary mapping strings to either a single AssemblySubroutineData instance or a list of such instances.
- **Description**: The AssemblySubroutineCollection class is a specialized collection designed to manage and organize assembly subroutine data. It inherits from the IrCollection class and primarily stores its data in a dictionary where keys are strings and values are either a single AssemblySubroutineData object or a list of these objects. The class provides a class method, from_llm, which facilitates the creation of an AssemblySubroutineCollection instance by leveraging a language model (llm) and a list of raw symbols, converting them into intermediate representation data using the AssemblySubroutineData class.
- **Inherits From**:
    - IrCollection

**Methods**

---
#### AssemblySubroutineCollection.from_llm
The `from_llm` function creates an instance of the class by invoking the `from_llm_with_ir_data` method with `AssemblySubroutineData`, a language model, and a collection of symbols.
- **Inputs**:
    - `llm`: An instance of the `ChatOpenAI` class, representing a language model used for processing.
    - `symbols_list`: An instance of `RawSymbolCollection`, representing a collection of raw symbols to be processed.
- **Control Flow**:
    - The function calls `cls.from_llm_with_ir_data` with `AssemblySubroutineData`, `llm`, and `symbols_list` as arguments.
    - The result of the `from_llm_with_ir_data` call is returned as the output of the function.
- **Output**:
    - The function returns an instance of the class it is called on, initialized using the provided language model and symbol collection.



---
### AssemblySubroutineData 
- **Type**: `class`
- **Members**:
    - `system_prompt`: Returns a predefined JSON string for system prompts related to functions.
    - `user_prompt`: Generates a user prompt string using the symbol's name and file code.
    - `child_to_ir`: Raises NotImplementedError as assembly functions should not have children.
    - `child_to_field_name`: Raises NotImplementedError as assembly functions should not have children.
- **Description**: The `AssemblySubroutineData` class is a specialized subclass of `FnData` designed to handle assembly subroutine data. It provides class methods to generate system and user prompts for documenting assembly functions, specifically focusing on functions without children. The class raises `NotImplementedError` for methods related to child processing, indicating that assembly functions are not expected to have child elements. This class is part of a larger framework for extracting and documenting assembly code components using language models.
- **Inherits From**:
    - FnData

**Methods**

---
#### AssemblySubroutineData.child_to_field_name
The `child_to_field_name` function raises an error indicating that assembly functions should not have children.
- **Inputs**:
    - `cls`: The class type that the method is bound to, typically used to access class-level attributes or methods.
    - `child`: An instance of `RawSymbolData` representing a child symbol that is not expected to exist for assembly functions.
- **Control Flow**:
    - The function immediately raises a `NotImplementedError` with a specific message.
- **Output**:
    - The function does not return any value; it raises an exception instead.


---
#### AssemblySubroutineData.child_to_ir
The `child_to_ir` function raises a `NotImplementedError` indicating that assembly functions should not have children.
- **Inputs**:
    - `cls`: The class type from which the method is called.
    - `symbol`: An instance of `RawSymbolData` representing the symbol data to be processed.
- **Control Flow**:
    - The function immediately raises a `NotImplementedError` with a specific message.
- **Output**:
    - The function does not return any value as it raises an exception.


---
#### AssemblySubroutineData.system_prompt
The `system_prompt` function returns a predefined JSON string used for documenting functions, subroutines, and procedures in assembly code.
- **Inputs**:
    - None
- **Control Flow**:
    - The function directly returns a constant string `FUNCTIONS_FOUND_SYSTEM_PROMPT_JSON`.
- **Output**:
    - The function outputs a string containing a JSON schema for documenting functions, subroutines, and procedures.


---
#### AssemblySubroutineData.user_prompt
The `user_prompt` function generates a formatted string containing a user prompt and the code associated with a given symbol.
- **Inputs**:
    - `cls`: The class object that the method is bound to, typically used in class methods.
    - `symbol`: An instance of `RawSymbolData` containing information about a symbol, including its name and associated code.
- **Control Flow**:
    - The function constructs a string by concatenating a predefined user prompt with the symbol's name and its associated code.
    - The string is formatted to include the symbol's name and code in a specific layout.
- **Output**:
    - The function returns a formatted string that includes a user prompt, the symbol's name, and its associated code.



---
### AssemblySubroutineRawSymbolCollection 
- **Type**: `class`
- **Members**:
    - `data`: A dictionary mapping string keys to RawSymbolData objects.
- **Description**: The `AssemblySubroutineRawSymbolCollection` class is designed to manage a collection of raw symbol data specifically for assembly subroutines. It inherits from `RawSymbolCollection` and provides methods to populate the collection using large language model (LLM) analysis. The class includes a method `from_llm` that performs LLM-based analysis to extract callable symbols from assembly code, while the `from_static_analysis` method is not implemented, indicating reliance on LLM for parsing. The `to_dict` method returns the internal data dictionary.
- **Inherits From**:
    - RawSymbolCollection

**Methods**

---
#### AssemblySubroutineRawSymbolCollection.from_llm
The `from_llm` function performs a default LLM analysis on a given code snippet using a specified collection class and LLM model.
- **Inputs**:
    - `cls`: The class type that will be used as the collection class for the analysis.
    - `llm`: An instance of the ChatOpenAI model used for the analysis.
    - `code`: The source code to be analyzed.
    - `root_rel_path`: The root relative path of the source code file.
- **Control Flow**:
    - Calls the `default_llm_analysis` function with the provided parameters.
    - Passes the `cls` as the `collection_cls` parameter to `default_llm_analysis`.
    - Uses `llm`, `code`, and `root_rel_path` as arguments for the analysis.
    - Sets `system_prompt` to `FUNCTIONS_CHECKER_SYSTEM_PROMPT_JSON` and `user_prompt` to an empty string.
    - Specifies `symbol_kind` as `SymbolKind.CALLABLE`.
- **Output**:
    - Returns the result of the `default_llm_analysis` function, which is either an instance of the class or `None`.


---
#### AssemblySubroutineRawSymbolCollection.from_static_analysis
The `from_static_analysis` function is a class method placeholder for parsing assembly code using static analysis, which is not implemented and raises a NotImplementedError.
- **Inputs**:
    - `cls`: The class on which this method is called, typically the class itself.
    - `code`: A string representing the assembly code to be analyzed.
    - `root_rel_path`: A Path object representing the root relative path of the code file.
- **Control Flow**:
    - The function immediately raises a NotImplementedError with a message indicating that assembly parsing uses LLM extraction instead of static analysis.
- **Output**:
    - The function does not return any output as it raises an exception.


---
#### AssemblySubroutineRawSymbolCollection.to_dict
The `to_dict` function returns the `data` attribute of the class instance as a dictionary.
- **Inputs**:
    - None
- **Control Flow**:
    - The function directly returns the `data` attribute of the class instance without any additional processing.
- **Output**:
    - A dictionary where the keys are strings and the values are `RawSymbolData` objects.



---
### AssemblyVariableCollection 
- **Type**: `class`
- **Members**:
    - `data`: A dictionary mapping string keys to either a single AssemblyVariableData instance or a list of such instances.
- **Description**: The `AssemblyVariableCollection` class is a specialized collection designed to manage and organize assembly variable data. It inherits from `IrCollection` and provides a structure to store assembly variable information in a dictionary format, where each key is a string and the value is either a single `AssemblyVariableData` object or a list of such objects. The class includes a class method `from_llm` that facilitates the creation of an `AssemblyVariableCollection` instance by leveraging a language model (LLM) and a collection of raw symbols, converting them into intermediate representation (IR) data.
- **Inherits From**:
    - IrCollection

**Methods**

---
#### AssemblyVariableCollection.from_llm
The `from_llm` function creates an instance of the class using LLM data and a collection of raw symbols.
- **Inputs**:
    - `llm`: An instance of the `ChatOpenAI` class, representing the language model to be used for data extraction.
    - `symbols_list`: An instance of `RawSymbolCollection`, representing a collection of raw symbols to be processed.
- **Control Flow**:
    - The function calls `from_llm_with_ir_data` on the class, passing `AssemblyVariableData`, `llm`, and `symbols_list` as arguments.
    - The function returns the result of the `from_llm_with_ir_data` call, which is an instance of the class.
- **Output**:
    - An instance of the class (`Self`) initialized with data extracted from the LLM and the provided symbols list.



---
### AssemblyVariableData 
- **Type**: `class`
- **Members**:
    - `system_prompt`: Returns a system prompt string for documenting variables.
    - `user_prompt`: Generates a user prompt string using a given symbol's name and file code.
    - `child_to_ir`: Raises NotImplementedError as assembly variables should not have children.
    - `child_to_field_name`: Raises NotImplementedError as assembly variables should not have children.
- **Description**: The `AssemblyVariableData` class is a specialized class for handling assembly variable data, inheriting from `VariableData`. It provides class methods to generate system and user prompts for documenting variables in assembly code. The class explicitly raises `NotImplementedError` for methods related to child elements, as assembly variables are not expected to have children. This class is part of a larger framework for extracting and documenting symbols in assembly code using language models.
- **Inherits From**:
    - VariableData

**Methods**

---
#### AssemblyVariableData.child_to_field_name
The `child_to_field_name` function raises a `NotImplementedError` indicating that assembly variables should not have children.
- **Inputs**:
    - `cls`: The class type that the method is bound to, typically used to access class-level attributes or methods.
    - `child`: An instance of `RawSymbolData` representing a child symbol that is being queried for a field name.
- **Control Flow**:
    - The function immediately raises a `NotImplementedError` with a specific message.
- **Output**:
    - The function does not return any value as it raises an exception.


---
#### AssemblyVariableData.child_to_ir
The `child_to_ir` function raises a `NotImplementedError` indicating that assembly variables should not have children.
- **Inputs**:
    - `cls`: The class type from which the method is called.
    - `symbol`: An instance of `RawSymbolData` representing a symbol in the assembly code.
- **Control Flow**:
    - The function immediately raises a `NotImplementedError` with a specific message.
- **Output**:
    - The function does not return any value as it raises an exception.


---
#### AssemblyVariableData.system_prompt
The `system_prompt` function returns a predefined JSON string for documenting variables in assembly code.
- **Inputs**:
    - None
- **Control Flow**:
    - The function directly returns the constant `VARIABLES_FOUND_SYSTEM_PROMPT_JSON`.
- **Output**:
    - The function outputs a string containing JSON schema instructions for documenting variables.


---
#### AssemblyVariableData.user_prompt
The `user_prompt` function generates a formatted string containing a user prompt and the code associated with a given symbol.
- **Inputs**:
    - `symbol`: An instance of `RawSymbolData` containing the name and file code of a symbol.
- **Control Flow**:
    - The function constructs a string by concatenating a predefined user prompt with the symbol's name and its associated code.
- **Output**:
    - A formatted string that includes the user prompt, the symbol's name, and its file code.



---
### AssemblyVariableRawSymbolCollection 
- **Type**: `class`
- **Members**:
    - `data`: A dictionary mapping string keys to RawSymbolData objects.
- **Description**: The `AssemblyVariableRawSymbolCollection` class is a specialized collection for handling raw symbol data related to assembly variables. It inherits from `RawSymbolCollection` and provides methods to populate the collection using large language model (LLM) analysis. The class includes a method `from_llm` to perform this analysis and populate the collection with variable symbols extracted from assembly code. Additionally, it provides a `to_dict` method to return the internal data dictionary.
- **Inherits From**:
    - RawSymbolCollection

**Methods**

---
#### AssemblyVariableRawSymbolCollection.from_llm
The `from_llm` function performs a default LLM analysis using the provided parameters to extract variable symbols from code.
- **Inputs**:
    - `cls`: The class type that will be used as the collection class for the analysis.
    - `llm`: An instance of the ChatOpenAI model used for language model analysis.
    - `code`: The source code string to be analyzed.
    - `root_rel_path`: The root relative path of the source code file being analyzed.
- **Control Flow**:
    - Calls the `default_llm_analysis` function with the provided class, LLM instance, code, and root relative path.
    - Passes a predefined system prompt for variable checking and an empty user prompt to the analysis function.
    - Specifies the symbol kind as `SymbolKind.VARIABLE` for the analysis.
- **Output**:
    - Returns the result of the `default_llm_analysis` function, which is either an instance of the class or None if the analysis fails.


---
#### AssemblyVariableRawSymbolCollection.from_static_analysis
The `from_static_analysis` function is a placeholder for a method intended to perform static analysis on assembly code, but it currently raises a NotImplementedError.
- **Inputs**:
    - `cls`: The class on which this class method is called, typically a subclass of RawSymbolCollection.
    - `code`: A string representing the assembly code to be analyzed.
    - `root_rel_path`: A Path object representing the root relative path of the code file.
- **Control Flow**:
    - The function immediately raises a NotImplementedError with a message indicating that assembly parsing uses LLM extraction.
- **Output**:
    - The function does not return any output as it raises an exception immediately.


---
#### AssemblyVariableRawSymbolCollection.to_dict
The `to_dict` function returns the `data` attribute of the class instance as a dictionary.
- **Inputs**:
    - None
- **Control Flow**:
    - The function directly returns the `data` attribute of the class instance without any additional processing.
- **Output**:
    - A dictionary where the keys are strings and the values are `RawSymbolData` objects.



