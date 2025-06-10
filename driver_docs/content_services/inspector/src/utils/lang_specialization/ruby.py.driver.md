# Purpose
This Python code file is designed to facilitate the extraction and documentation of Ruby code components, specifically classes and modules, using static analysis. It leverages the `pydantic` library for data validation and management, and integrates with a utility function `extract_symbols_w_ctags` to parse Ruby code symbols. The file defines several classes, such as `RubyMethodData`, `RubyAttributeData`, `RubyClassData`, and `RubyModuleData`, which are responsible for generating structured documentation prompts for Ruby methods, attributes, classes, and modules, respectively. These classes use JSON schemas to ensure consistent documentation output, and they provide methods to generate prompts for both system and user interactions.

The file also includes classes like `RubyClassRawSymbolCollection` and `RubyModuleRawSymbolCollection`, which are responsible for collecting and organizing raw symbol data extracted from Ruby code. These classes use static analysis to identify and categorize Ruby classes and modules, along with their associated methods and attributes. The code is structured to support the generation of detailed documentation for Ruby code, focusing on the technical aspects and relationships between different code components. This file is intended to be part of a larger system that automates the documentation process for Ruby codebases, providing a structured and consistent approach to generating technical documentation.
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
### ATTRIBUTES_FOUND_SYSTEM_PROMPT_JSON 
- **Type**: `str`
- **Description**: The `ATTRIBUTES_FOUND_SYSTEM_PROMPT_JSON` is a string variable that contains a JSON schema template. This template is used to guide the documentation process for attributes in Ruby code, ensuring that the documentation follows a specific format. The schema includes fields for the type, description, and use of the attribute.
- **Use**: This variable is used to provide a structured format for documenting Ruby attributes, ensuring consistency and completeness in the documentation process.


---
### ATTRIBUTES_FOUND_USER_PROMPT 
- **Type**: `str`
- **Description**: `ATTRIBUTES_FOUND_USER_PROMPT` is a string variable that contains a template for generating user prompts related to summarizing attributes in Ruby code. The prompt instructs the user to provide a detailed description of an attribute, matching the complexity of the attribute being described.
- **Use**: This variable is used to generate user prompts for documenting attributes in Ruby code.


---
### CLASSES_FOUND_SYSTEM_PROMPT_JSON 
- **Type**: `str`
- **Description**: `CLASSES_FOUND_SYSTEM_PROMPT_JSON` is a string variable that contains a JSON schema template for documenting Ruby classes. This template guides the documentation process by specifying the structure and content required for describing Ruby classes, including fields like description, inheritance, and included modules.
- **Use**: This variable is used to provide a structured format for generating documentation for Ruby classes.


---
### CLASSES_FOUND_USER_PROMPT 
- **Type**: `str`
- **Description**: `CLASSES_FOUND_USER_PROMPT` is a string variable that contains a prompt message intended for user interaction. This prompt is used to instruct users on how to summarize a class in the provided code, emphasizing the need for detail that matches the complexity of the class.
- **Use**: This variable is used to guide users in providing detailed summaries of classes in code documentation.


---
### METHODS_FOUND_SYSTEM_PROMPT_JSON 
- **Type**: `str`
- **Description**: `METHODS_FOUND_SYSTEM_PROMPT_JSON` is a string variable that contains a JSON schema template for documenting Ruby methods. This template guides the user to provide a structured description of a method, including a single sentence summary, inputs, control flow, and output.
- **Use**: This variable is used to provide a consistent format for documenting Ruby methods by specifying the required JSON schema.


---
### METHODS_FOUND_USER_PROMPT 
- **Type**: `str`
- **Description**: `METHODS_FOUND_USER_PROMPT` is a string variable that contains a template for generating user prompts related to documenting methods in Ruby code. The prompt instructs the user to summarize a method by describing its inputs, control flow, logic, and output, with a focus on providing detail that matches the complexity of the method body.
- **Use**: This variable is used to generate user prompts for documenting Ruby methods, ensuring that the documentation is detailed and matches the method's complexity.


---
### MODULES_FOUND_SYSTEM_PROMPT_JSON 
- **Type**: `str`
- **Description**: The `MODULES_FOUND_SYSTEM_PROMPT_JSON` variable is a string that contains a JSON schema template for documenting Ruby modules. This template is used to guide the documentation process by specifying the structure and fields required for describing a Ruby module, including its description, included modules, extended modules, and prepended modules.
- **Use**: This variable is used as a template to ensure consistent and comprehensive documentation of Ruby modules.


---
### MODULES_FOUND_USER_PROMPT 
- **Type**: `str`
- **Description**: The `MODULES_FOUND_USER_PROMPT` is a string variable that contains a template for a user prompt. This prompt is used to instruct users on how to summarize a module in Ruby code, focusing on the complexity and details of the module.
- **Use**: This variable is used to provide a consistent and structured prompt for users to document Ruby modules.


---
### RUBY_ATTRIBUTES 
- **Type**: `set`
- **Description**: RUBY_ATTRIBUTES is a set containing a single string element 'accessor'. This set is used to categorize or identify Ruby attributes within the context of the code.
- **Use**: This variable is used to check or match against Ruby attributes when processing or analyzing Ruby code.


---
### RUBY_CLASSES 
- **Type**: `set`
- **Description**: The `RUBY_CLASSES` variable is a set containing a single string element, 'class'. This set is used to identify or categorize Ruby class symbols within the code. It is part of a larger system that processes Ruby code to extract and document various components such as classes, modules, and methods.
- **Use**: This variable is used to identify Ruby class symbols during static analysis or code processing.


---
### RUBY_CLASS_AND_MODULE_METHODS 
- **Type**: `set`
- **Description**: `RUBY_CLASS_AND_MODULE_METHODS` is a set containing the string 'singletonMethod'. This set is used to categorize Ruby methods that are associated with classes and modules, specifically singleton methods.
- **Use**: This variable is used to identify and categorize singleton methods in Ruby classes and modules.


---
### RUBY_INSTANCE_METHODS 
- **Type**: `set`
- **Description**: `RUBY_INSTANCE_METHODS` is a set containing the string 'method'. This set is used to categorize or identify Ruby instance methods within the code.
- **Use**: This variable is used to check or classify symbols as Ruby instance methods in the context of static analysis or symbol extraction.


---
### RUBY_MODULES 
- **Type**: `set`
- **Description**: `RUBY_MODULES` is a set containing a single string element, "module". This set is used to categorize or identify Ruby modules within the codebase.
- **Use**: This variable is used to check or classify symbols as Ruby modules during static analysis or code processing.


---
### SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT 
- **Type**: `str`
- **Description**: `SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT` is a string variable that contains a detailed prompt for explaining the purpose of a large source code file. It guides the user to provide a comprehensive explanation of the code's purpose, focusing on its functionality, technical components, and any public APIs or interfaces it may define.
- **Use**: This variable is used to generate a user prompt for explaining the purpose of large source code files in a detailed manner.


---
### SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_RUBY 
- **Type**: `str`
- **Description**: The variable `SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_RUBY` is a string that contains a detailed prompt for a system designed to generate documentation for Ruby code. It emphasizes the expertise of the user in Ruby programming and documentation, and outlines the task of explaining technical details and conceptual components of Ruby software.
- **Use**: This variable is used as a system prompt to guide the generation of detailed documentation for large Ruby codebases.


---
### SOURCE_CODE_SMALL_PURPOSE_USER_PROMPT 
- **Type**: `str`
- **Description**: `SOURCE_CODE_SMALL_PURPOSE_USER_PROMPT` is a string variable that contains a template for generating a user prompt. This prompt is designed to guide users in explaining the purpose of a small and simple source code file in a concise manner.
- **Use**: This variable is used to provide a structured prompt for users to describe the purpose of small source code files.


---
### SOURCE_CODE_SMALL_SYSTEM_PROMPT_GENERAL_RUBY 
- **Type**: `str`
- **Description**: `SOURCE_CODE_SMALL_SYSTEM_PROMPT_GENERAL_RUBY` is a string variable that contains a prompt template for generating documentation for small and simple Ruby source code files. It emphasizes the need for clarity and brevity in the documentation process.
- **Use**: This variable is used as a template for generating concise documentation for small Ruby source code files.


---
### _supported_child_ordering 
- **Type**: `list[str]`
- **Description**: The `_supported_child_ordering` variable is a private attribute defined within the `RubyClassData` and `RubyModuleData` classes. It is a list of strings that specifies the order in which child elements, such as attributes and methods, are expected to appear within a Ruby class or module.
- **Use**: This variable is used to define the expected order of child elements in Ruby classes and modules.


# Classes

---
### RubyAttributeData 
- **Type**: `class`
- **Members**:
    - `system_prompt`: Returns a system prompt string for documenting Ruby attributes.
    - `user_prompt`: Generates a user prompt string for a given Ruby symbol.
    - `child_to_ir`: Raises NotImplementedError as attributes should not have children.
    - `child_to_field_name`: Raises NotImplementedError as attributes should not have children.
- **Description**: The RubyAttributeData class is a specialized class for handling Ruby attribute data within a documentation system. It provides class methods to generate system and user prompts specifically tailored for documenting Ruby attributes. The class also includes methods that raise NotImplementedError for child-related operations, indicating that attributes are not expected to have children in this context. This class inherits from VariableData, suggesting it is part of a larger framework for managing variable-like data structures.
- **Inherits From**:
    - VariableData

**Methods**

---
#### RubyAttributeData.child_to_field_name
The `child_to_field_name` function raises a `NotImplementedError` indicating that attributes should not have children.
- **Inputs**:
    - `cls`: The class on which this method is called, typically a class method.
    - `child`: An instance of `RawSymbolData` representing a child symbol.
- **Control Flow**:
    - The function immediately raises a `NotImplementedError` with a specific message.
- **Output**:
    - The function does not return any value as it raises an exception.


---
#### RubyAttributeData.child_to_ir
The `child_to_ir` function raises a `NotImplementedError` indicating that attributes should not have children.
- **Inputs**:
    - `cls`: The class object that the method is bound to, typically used in class methods.
    - `symbol`: An instance of `RawSymbolData` representing a symbol in the code, which is intended to be converted to an intermediate representation (IR).
- **Control Flow**:
    - The function immediately raises a `NotImplementedError` with a specific message.
- **Output**:
    - The function does not return any value as it raises an exception.


---
#### RubyAttributeData.system_prompt
The `system_prompt` function returns a predefined JSON string for documenting Ruby attributes.
- **Inputs**:
    - None
- **Control Flow**:
    - The function directly returns the constant `ATTRIBUTES_FOUND_SYSTEM_PROMPT_JSON`.
- **Output**:
    - The output is a string containing a JSON schema for documenting Ruby attributes.


---
#### RubyAttributeData.user_prompt
The `user_prompt` function generates a formatted string prompt for a given symbol, including its name, attribute code, and optionally its full file code.
- **Inputs**:
    - `symbol`: An instance of `RawSymbolData` containing the symbol's name, symbol code, and optionally the full file code.
- **Control Flow**:
    - Initialize a string `user_prompt` with a formatted message including the symbol's name and symbol code.
    - Check if the `symbol` has a `file_code` attribute.
    - If `file_code` is present, append the full file code to the `user_prompt`.
    - Return the constructed `user_prompt` string.
- **Output**:
    - A formatted string containing the symbol's name, attribute code, and optionally the full file code.



---
### RubyClassCollection 
- **Type**: `class`
- **Members**:
    - `data`: A dictionary mapping strings to RubyClassData or lists of RubyClassData.
- **Description**: The RubyClassCollection class is a specialized collection class that inherits from IrCollection and is designed to manage a collection of RubyClassData objects. It provides a class method, from_llm, which facilitates the creation of a RubyClassCollection instance from a language model and a list of raw symbols. This class is part of a system that processes and organizes Ruby class data, likely for documentation or analysis purposes.
- **Inherits From**:
    - IrCollection

**Methods**

---
#### RubyClassCollection.from_llm
The `from_llm` function creates an instance of the class using data from a language model and a collection of symbols.
- **Inputs**:
    - `llm`: An instance of the `ChatOpenAI` class, representing a language model.
    - `symbols_list`: An instance of `RawSymbolCollection`, representing a collection of raw symbols.
- **Control Flow**:
    - The function calls `from_llm_with_ir_data` on the class (`cls`) with `RubyClassData`, `llm`, and `symbols_list` as arguments.
    - The result of the `from_llm_with_ir_data` call is returned.
- **Output**:
    - An instance of the class (`Self`) initialized with data from the language model and symbols list.



---
### RubyClassData 
- **Type**: `class`
- **Members**:
    - `description`: Stores a description of the Ruby class.
    - `inherits_from`: Lists the classes this Ruby class inherits from.
    - `includes`: Lists the modules included in this Ruby class.
    - `extends`: Lists the modules extended by this Ruby class.
    - `prepends`: Lists the modules prepended to this Ruby class.
    - `_supported_child_ordering`: Defines the order of child elements like attributes and methods.
- **Description**: The `RubyClassData` class is a specialized data structure for representing Ruby classes, inheriting from `IrData`. It includes attributes to describe the class, its inheritance, and its module interactions, such as includes, extends, and prepends. The class provides class methods for generating system and user prompts, mapping child symbols to internal representations, and creating default instances. It is designed to facilitate the documentation and analysis of Ruby class structures, supporting the organization of class attributes and methods in a specific order.
- **Inherits From**:
    - IrData

**Methods**

---
#### RubyClassData.child_to_field_name
The `child_to_field_name` function maps a `RawSymbolData` object's `scope_relation` to a corresponding field name string.
- **Inputs**:
    - `cls`: The class reference, typically used for class methods.
    - `child`: An instance of `RawSymbolData` which contains information about a symbol, including its `scope_relation`.
- **Control Flow**:
    - A dictionary `mapping` is defined to map specific `ScopeRelation` values to themselves.
    - The function attempts to retrieve the field name from the `mapping` dictionary using the `scope_relation` attribute of the `child` argument.
- **Output**:
    - The function returns a string representing the field name corresponding to the `scope_relation` of the `child`, or `None` if the `scope_relation` is not found in the mapping.


---
#### RubyClassData.child_to_ir
The `child_to_ir` function maps a `RawSymbolData` object to a corresponding `IrData` class based on the symbol's kind.
- **Inputs**:
    - `cls`: The class reference from which this class method is called.
    - `symbol`: An instance of `RawSymbolData` representing a symbol with a specific kind.
- **Control Flow**:
    - A dictionary `mapping` is defined to associate `SymbolKind.CALLABLE` with `RubyMethodData` and `SymbolKind.VARIABLE` with `RubyAttributeData`.
    - The function attempts to retrieve the corresponding `IrData` class from the `mapping` dictionary using the `symbol.symbol_kind` as the key.
- **Output**:
    - The function returns an `IrData` class (`RubyMethodData` or `RubyAttributeData`) if the `symbol_kind` is found in the mapping, otherwise it returns `None`.


---
#### RubyClassData.default_instance
The `default_instance` function creates and returns a new instance of the class with default empty values for its attributes.
- **Inputs**:
    - `cls`: The class for which a default instance is to be created.
- **Control Flow**:
    - The function is called as a class method, taking the class itself as an argument.
    - A new instance of the class is created using the class constructor.
    - The instance is initialized with default values: an empty string for `description` and empty lists for `inherits_from`, `includes`, `extends`, and `prepends`.
    - The newly created instance is returned.
- **Output**:
    - A new instance of the class with default attribute values.


---
#### RubyClassData.system_prompt
The `system_prompt` function returns a predefined JSON string for documenting Ruby classes.
- **Inputs**:
    - None
- **Control Flow**:
    - The function directly returns the constant `CLASSES_FOUND_SYSTEM_PROMPT_JSON`.
- **Output**:
    - The function outputs a string containing a JSON schema for documenting Ruby classes.


---
#### RubyClassData.user_prompt
The `user_prompt` function generates a formatted string prompt for a given symbol, including its name and code, and optionally the full file code if available.
- **Inputs**:
    - `cls`: The class reference from which this class method is called.
    - `symbol`: An instance of `RawSymbolData` containing the name, symbol code, and optionally the full file code of the symbol.
- **Control Flow**:
    - Initialize a string `user_prompt` with a formatted message including the symbol's name and its code.
    - Check if the `symbol` has `file_code` available.
    - If `file_code` is available, append it to the `user_prompt` string.
    - Return the constructed `user_prompt` string.
- **Output**:
    - A formatted string containing the symbol's name, its code, and optionally the full file code.



---
### RubyClassRawSymbolCollection 
- **Type**: `class`
- **Members**:
    - `data`: A dictionary mapping string keys to RawSymbolData objects.
- **Description**: The RubyClassRawSymbolCollection class is designed to handle collections of raw symbol data specifically for Ruby classes. It inherits from RawSymbolCollection and provides methods to populate its data from static analysis of Ruby code. The class processes symbols extracted from the code, categorizing them into classes, attributes, class methods, and instance methods, and organizes them into a structured dictionary format. This class is essential for managing and accessing raw symbol data related to Ruby classes, facilitating further analysis or processing.
- **Inherits From**:
    - RawSymbolCollection

**Methods**

---
#### RubyClassRawSymbolCollection.from_llm
The `from_llm` function raises a NotImplementedError indicating that static analysis should be used for Ruby classes.
- **Inputs**:
    - `cls`: The class on which this method is called, typically a class method.
    - `code`: A string representing the code to be analyzed.
    - `root_rel_path`: A string representing the root relative path of the code file.
- **Control Flow**:
    - The function immediately raises a NotImplementedError with a specific message.
- **Output**:
    - The function does not return any output as it raises an exception.


---
#### RubyClassRawSymbolCollection.from_static_analysis
The `from_static_analysis` function analyzes Ruby code to extract class and module symbols and their relationships using ctags, returning a collection of these symbols.
- **Inputs**:
    - `code`: A string containing the Ruby source code to be analyzed.
    - `root_rel_path`: A Path object representing the root-relative path of the file containing the code.
- **Control Flow**:
    - Determine if the code requires multi-prompt processing using `code_requires_multi_prompt` function.
    - Extract symbols from the code using `extract_symbols_w_ctags` function.
    - Initialize an empty dictionary `class_raw_symbol_data` to store class-related symbol data.
    - Iterate over the extracted symbols to identify Ruby classes and create raw symbol data for each class using `create_raw_symbol_via_ctags`.
    - For each symbol, check if it is a Ruby attribute, class/module method, or instance method within a class scope, and append the corresponding raw symbol data to the class's children.
    - Return `None` if no class symbols are found, otherwise return an instance of the class with the collected symbol data.
- **Output**:
    - Returns an instance of the class containing the collected class symbol data, or `None` if no class symbols are found.


---
#### RubyClassRawSymbolCollection.to_dict
The `to_dict` function returns the `data` attribute of the instance as a dictionary.
- **Inputs**:
    - None
- **Control Flow**:
    - The function directly returns the `data` attribute of the instance.
- **Output**:
    - A dictionary where the keys are strings and the values are `RawSymbolData` objects.



---
### RubyMethodData 
- **Type**: `class`
- **Members**:
    - `system_prompt`: Returns a system prompt string for documenting Ruby methods.
    - `user_prompt`: Generates a user prompt string for a given Ruby method symbol.
    - `child_to_ir`: Raises NotImplementedError as methods should not have children.
    - `child_to_field_name`: Raises NotImplementedError as methods should not have children.
- **Description**: The RubyMethodData class is a specialized class for handling Ruby method documentation within a larger system that processes code symbols. It inherits from FnData and provides class methods to generate system and user prompts specifically tailored for Ruby methods. The class also explicitly raises errors for operations related to child symbols, as methods are not expected to have children in this context.
- **Inherits From**:
    - FnData

**Methods**

---
#### RubyMethodData.child_to_field_name
The `child_to_field_name` function raises a `NotImplementedError` indicating that methods should not have children.
- **Inputs**:
    - `cls`: The class on which this method is called, typically a class method.
    - `child`: An instance of `RawSymbolData` representing a child symbol.
- **Control Flow**:
    - The function immediately raises a `NotImplementedError` with a specific message.
- **Output**:
    - The function does not return any value as it raises an exception.


---
#### RubyMethodData.child_to_ir
The `child_to_ir` function raises a `NotImplementedError` indicating that methods should not have children.
- **Inputs**:
    - `cls`: The class on which this class method is called.
    - `symbol`: An instance of `RawSymbolData` representing a symbol that might be converted to an intermediate representation (IR).
- **Control Flow**:
    - The function immediately raises a `NotImplementedError` with the message 'Methods should not have children'.
- **Output**:
    - The function does not return any value as it raises an exception.


---
#### RubyMethodData.system_prompt
The `system_prompt` function returns a predefined JSON string used for documenting Ruby methods.
- **Inputs**:
    - None
- **Control Flow**:
    - The function directly returns the constant `METHODS_FOUND_SYSTEM_PROMPT_JSON`.
- **Output**:
    - The output is a string containing a JSON schema for documenting Ruby methods.


---
#### RubyMethodData.user_prompt
The `user_prompt` function generates a formatted string prompt for a given symbol, including its name and code, and optionally the full file code if available.
- **Inputs**:
    - `symbol`: An instance of `RawSymbolData` containing the name, symbol code, and optionally the full file code of a method or attribute.
- **Control Flow**:
    - Initialize a string `user_prompt` with a formatted message containing the method name and its code from the `symbol` object.
    - Check if the `symbol` object has `file_code` available.
    - If `file_code` is available, append the full file code to the `user_prompt` string.
- **Output**:
    - A formatted string containing the method name, its code, and optionally the full file code.



---
### RubyModuleCollection 
- **Type**: `class`
- **Members**:
    - `data`: A dictionary mapping strings to RubyModuleData or lists of RubyModuleData.
- **Description**: The RubyModuleCollection class is a specialized collection class that inherits from IrCollection and is designed to manage a collection of RubyModuleData objects. It provides a class method, from_llm, which facilitates the creation of a RubyModuleCollection instance from a language model and a list of raw symbols, leveraging the from_llm_with_ir_data method to populate the collection with RubyModuleData instances. This class is part of a system that processes and organizes Ruby module data, likely for documentation or analysis purposes.
- **Inherits From**:
    - IrCollection

**Methods**

---
#### RubyModuleCollection.from_llm
The `from_llm` function creates an instance of the class by invoking the `from_llm_with_ir_data` method with `RubyModuleData`, a language model, and a collection of raw symbols.
- **Inputs**:
    - `llm`: An instance of the `ChatOpenAI` class, representing a language model.
    - `symbols_list`: An instance of `RawSymbolCollection`, representing a collection of raw symbols.
- **Control Flow**:
    - The function calls the `from_llm_with_ir_data` method on the class, passing `RubyModuleData`, `llm`, and `symbols_list` as arguments.
    - The result of the `from_llm_with_ir_data` method call is returned.
- **Output**:
    - The function returns an instance of the class it is called on, initialized using the `from_llm_with_ir_data` method with the provided language model and symbols list.



---
### RubyModuleData 
- **Type**: `class`
- **Members**:
    - `description`: Stores a description of the Ruby module.
    - `includes`: Holds a list of modules included by this Ruby module.
    - `extends`: Holds a list of modules extended by this Ruby module.
    - `prepends`: Holds a list of modules prepended to this Ruby module.
    - `_supported_child_ordering`: Defines the order of child elements like attributes and methods.
- **Description**: The `RubyModuleData` class is designed to represent metadata about a Ruby module, including its description, included modules, extended modules, and prepended modules. It provides class methods to generate system and user prompts for documentation purposes, and to map child symbols to their respective intermediate representation (IR) data types. The class also supports defining the order of child elements such as attributes and methods, and offers a method to create a default instance of itself with empty fields.
- **Inherits From**:
    - IrData

**Methods**

---
#### RubyModuleData.child_to_field_name
The `child_to_field_name` function maps a `RawSymbolData` object's `scope_relation` to a corresponding field name string.
- **Inputs**:
    - `cls`: The class reference, typically used for class methods.
    - `child`: An instance of `RawSymbolData` which contains information about a symbol, including its `scope_relation`.
- **Control Flow**:
    - A dictionary `mapping` is defined to map specific `ScopeRelation` values to themselves.
    - The function attempts to retrieve the field name from the `mapping` dictionary using the `scope_relation` attribute of the `child` argument.
- **Output**:
    - The function returns a string representing the field name corresponding to the `scope_relation` of the `child`, or `None` if the `scope_relation` is not in the mapping.


---
#### RubyModuleData.child_to_ir
The `child_to_ir` function maps a `RawSymbolData` object to a corresponding `IrData` class based on its symbol kind.
- **Inputs**:
    - `cls`: The class on which this method is called, typically a subclass of `IrData`.
    - `symbol`: An instance of `RawSymbolData` representing a symbol with a specific kind, such as a callable or variable.
- **Control Flow**:
    - A dictionary `mapping` is defined to associate `SymbolKind.CALLABLE` with `RubyMethodData` and `SymbolKind.VARIABLE` with `RubyAttributeData`.
    - The function attempts to retrieve the corresponding `IrData` class from the `mapping` dictionary using the `symbol.symbol_kind` as the key.
- **Output**:
    - The function returns the `IrData` class associated with the symbol's kind, or `None` if the kind is not found in the mapping.


---
#### RubyModuleData.default_instance
The `default_instance` function creates and returns a default instance of the class with empty content for its attributes.
- **Inputs**:
    - `cls`: The class for which a default instance is to be created.
- **Control Flow**:
    - The function is a class method, indicated by the `cls` parameter, which refers to the class itself.
    - It returns an instance of the class by calling `cls()` with specific default arguments.
    - The `description` attribute is initialized with an instance of `FieldNameWithRawContent` with empty content.
    - The `includes`, `extends`, and `prepends` attributes are initialized with instances of `ListedRawContentNoNone` with empty lists as content.
- **Output**:
    - The function returns an instance of the class with default values for its attributes.


---
#### RubyModuleData.system_prompt
The `system_prompt` function returns a predefined JSON string for documenting Ruby modules.
- **Inputs**:
    - None
- **Control Flow**:
    - The function directly returns the constant `MODULES_FOUND_SYSTEM_PROMPT_JSON`.
- **Output**:
    - A string containing a JSON schema for documenting Ruby modules.


---
#### RubyModuleData.user_prompt
The `user_prompt` function generates a formatted string prompt for a given symbol, including its name and code, and optionally the full file code if available.
- **Inputs**:
    - `symbol`: An instance of `RawSymbolData` containing the name, symbol code, and optionally the full file code of a symbol.
- **Control Flow**:
    - Initialize a string `user_prompt` with a predefined prompt and the symbol's name and code.
    - Check if the symbol has associated full file code.
    - If full file code is present, append it to the `user_prompt`.
    - Return the constructed `user_prompt` string.
- **Output**:
    - A formatted string that includes the symbol's name, its code, and optionally the full file code.



---
### RubyModuleRawSymbolCollection 
- **Type**: `class`
- **Members**:
    - `data`: A dictionary mapping symbol names to their corresponding RawSymbolData.
- **Description**: The RubyModuleRawSymbolCollection class is designed to collect and manage raw symbol data specifically for Ruby modules. It inherits from RawSymbolCollection and provides methods to populate its data from static analysis of Ruby code. The class processes symbols extracted from code using ctags, identifying module-related symbols and organizing them into a structured format. It supports the addition of attributes and methods to modules, categorizing them based on their scope and kind, and allows for conversion of the collected data into a dictionary format.
- **Inherits From**:
    - RawSymbolCollection

**Methods**

---
#### RubyModuleRawSymbolCollection.from_llm
The `from_llm` function raises a NotImplementedError indicating that static analysis should be used for Ruby modules.
- **Inputs**:
    - `code`: A string representing the code to be analyzed.
    - `root_rel_path`: A string representing the root relative path of the code.
- **Control Flow**:
    - The function immediately raises a NotImplementedError with a specific message.
- **Output**:
    - The function does not return any output as it raises an exception.


---
#### RubyModuleRawSymbolCollection.from_static_analysis
The `from_static_analysis` function analyzes Ruby code to extract module symbols and their associated attributes and methods, returning a structured collection of these symbols.
- **Inputs**:
    - `code`: A string containing the Ruby source code to be analyzed.
    - `root_rel_path`: A `Path` object representing the root-relative path of the file containing the Ruby code.
- **Control Flow**:
    - Determine if the code requires multi-prompt processing using `code_requires_multi_prompt` function.
    - Extract symbols from the code using `extract_symbols_w_ctags` function.
    - Initialize an empty dictionary `module_raw_symbol_data` to store module symbols and their data.
    - Iterate over the extracted symbols to identify and store module symbols in `module_raw_symbol_data`.
    - For each symbol, check if it is an attribute, class/module method, or instance method within a module scope, and append it to the corresponding module's children in `module_raw_symbol_data`.
    - Return `None` if no module symbols are found, otherwise return an instance of the class with the collected module symbol data.
- **Output**:
    - Returns an instance of the class containing the module symbol data if any modules are found, otherwise returns `None`.


---
#### RubyModuleRawSymbolCollection.to_dict
The `to_dict` function returns the `data` attribute of the instance as a dictionary.
- **Inputs**:
    - None
- **Control Flow**:
    - The function directly returns the `data` attribute of the instance without any additional processing.
- **Output**:
    - A dictionary where the keys are strings and the values are `RawSymbolData` objects.



