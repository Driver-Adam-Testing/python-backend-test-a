# Purpose
This Python code is designed to facilitate the extraction and documentation of Java code components, specifically focusing on classes, interfaces, methods, and fields. It leverages static analysis tools, such as ctags, to parse Java source files and identify these components. The code defines several classes, such as `JavaClassData`, `JavaInterfaceData`, `JavaMethodData`, and `JavaFieldData`, which are used to structure and store metadata about Java code elements. These classes include methods for generating prompts for language models to create documentation, as well as methods for handling the hierarchical relationships between Java code elements, such as methods within classes or fields within interfaces.

The code also includes collections like `JavaClassCollection` and `JavaInterfaceCollection` to manage groups of these data objects. The primary functionality is to parse Java source code, extract relevant symbols, and prepare structured data that can be used to generate detailed documentation. This is achieved through a combination of static analysis and integration with language models, as indicated by the use of classes like `ChatOpenAI`. The code is structured to support the generation of JSON-formatted documentation, ensuring that the output is consistent and machine-readable.
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
- **Type**: ``str``
- **Description**: `CLASSES_FOUND_SYSTEM_PROMPT_JSON` is a string variable that contains a JSON schema template for documenting Java classes. This template is used to guide the documentation process by specifying the structure and content required for describing Java classes, including their description, implemented interfaces, extended classes, and modifiers.
- **Use**: This variable is used as a system prompt to ensure consistent and structured documentation of Java classes.


---
### CLASSES_FOUND_USER_PROMPT 
- **Type**: `str`
- **Description**: `CLASSES_FOUND_USER_PROMPT` is a string variable that contains a template for a user prompt. This prompt is used to request a summary of a Java class from the provided code. The prompt guides the user to provide a detailed description of the class, matching the complexity of the class being described.
- **Use**: This variable is used to generate a user prompt for summarizing Java classes in the provided code.


---
### FIELDS_FOUND_SYSTEM_PROMPT_JSON 
- **Type**: `str`
- **Description**: `FIELDS_FOUND_SYSTEM_PROMPT_JSON` is a string variable that contains a JSON schema template for documenting Java fields. This template is used to guide the documentation process by specifying the structure and content required for field documentation. It includes fields for type, description, use, and modifiers of a field.
- **Use**: This variable is used to provide a structured format for documenting Java fields in a consistent and detailed manner.


---
### FIELDS_FOUND_USER_PROMPT 
- **Type**: ``str``
- **Description**: `FIELDS_FOUND_USER_PROMPT` is a string variable that contains a template for a user prompt. This prompt is used to instruct users on how to summarize a field in the code provided, with guidance on the level of detail required based on the complexity of the field.
- **Use**: This variable is used to generate user prompts for documenting fields in Java code.


---
### INTERFACES_FOUND_SYSTEM_PROMPT_JSON 
- **Type**: `str`
- **Description**: The `INTERFACES_FOUND_SYSTEM_PROMPT_JSON` is a string variable that contains a system prompt template for documenting Java interfaces. It instructs the user to provide a JSON response with a description of the interface and any interfaces it extends.
- **Use**: This variable is used to guide the documentation process for Java interfaces by providing a structured prompt template.


---
### INTERFACES_FOUND_USER_PROMPT 
- **Type**: ``str``
- **Description**: `INTERFACES_FOUND_USER_PROMPT` is a string variable that contains a template for a user prompt. This prompt is used to request a summary of a Java interface from the provided code. It guides the user to provide a detailed description of the interface, matching the complexity of the interface with the length of the explanation.
- **Use**: This variable is used to generate user prompts for summarizing Java interfaces in the code.


---
### JAVA_CLASSES 
- **Type**: `set`
- **Description**: `JAVA_CLASSES` is a set containing the strings 'class' and 'enum'. This set is used to categorize Java symbols that represent classes and enumerations.
- **Use**: This variable is used to identify and categorize Java class and enum symbols during code analysis.


---
### JAVA_FIELDS 
- **Type**: `set`
- **Description**: `JAVA_FIELDS` is a set containing a single string element, 'field'. This set is used to categorize or identify Java fields within a codebase.
- **Use**: This variable is used to identify and categorize Java fields when analyzing Java code.


---
### JAVA_INTERFACES 
- **Type**: `set`
- **Description**: `JAVA_INTERFACES` is a global variable defined as a set containing a single string element, 'interface'. This set is used to categorize or identify Java symbols that are interfaces within the context of the code.
- **Use**: It is used to check or classify Java symbols as interfaces when processing or analyzing Java code.


---
### JAVA_METHODS 
- **Type**: `set`
- **Description**: `JAVA_METHODS` is a set containing a single string element, 'method'. This set is used to categorize or identify Java methods within a codebase. It is part of a group of similar sets that categorize different Java constructs like interfaces, classes, and fields.
- **Use**: This variable is used to identify and categorize Java methods in the code.


---
### METHODS_FOUND_SYSTEM_PROMPT_JSON 
- **Type**: `str`
- **Description**: `METHODS_FOUND_SYSTEM_PROMPT_JSON` is a string variable that contains a JSON schema template for documenting Java class methods. This template guides the documentation process by specifying the structure and content required for method descriptions, including inputs, control flow, output, and modifiers.
- **Use**: This variable is used to provide a structured format for generating detailed documentation of Java class methods.


---
### METHODS_FOUND_USER_PROMPT 
- **Type**: `str`
- **Description**: `METHODS_FOUND_USER_PROMPT` is a string variable that contains a template for a user prompt. This prompt is used to instruct users on how to summarize a method in the provided code, focusing on inputs, control flow, logic, and output. The prompt emphasizes providing detail that matches the complexity of the method body.
- **Use**: This variable is used to guide users in documenting methods by providing a structured prompt template.


---
### SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT 
- **Type**: ``str``
- **Description**: `SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT` is a string variable that contains a detailed prompt for explaining the purpose of a large source code file. It guides the user to provide a comprehensive explanation of the code's purpose, focusing on its functionality, technical components, and any public APIs or interfaces it may define.
- **Use**: This variable is used to instruct users on how to document the purpose of large source code files.


---
### SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_JAVA 
- **Type**: ``str``
- **Description**: This variable is a string that contains a prompt for a large system Java documentation task. It is designed to guide a language model in generating detailed documentation for Java code, focusing on explaining technical details and the purpose of the software.
- **Use**: This variable is used as a prompt to instruct a language model on how to generate comprehensive documentation for large Java systems.


---
### SOURCE_CODE_SMALL_PURPOSE_USER_PROMPT 
- **Type**: ``str``
- **Description**: `SOURCE_CODE_SMALL_PURPOSE_USER_PROMPT` is a string variable that contains a template for a user prompt. This prompt is designed to guide users in explaining the purpose of a small piece of source code in a concise manner. It includes questions to consider, such as the scope of functionality provided by the code.
- **Use**: This variable is used to provide a structured prompt for users to describe the purpose of small source code files.


---
### SOURCE_CODE_SMALL_SYSTEM_PROMPT_GENERAL_JAVA 
- **Type**: `str`
- **Description**: This variable is a string that contains a system prompt for a language model, specifically tailored for documenting small and simple Java source code files. It emphasizes the need for clarity and brevity in the documentation process.
- **Use**: It is used as a prompt to guide a language model in generating concise and clear documentation for small Java source code files.


---
### _supported_child_ordering 
- **Type**: `list[str]`
- **Description**: The `_supported_child_ordering` variable is a private attribute that holds a list of strings representing the order of child elements that are supported within a Java class or interface. The list includes `ScopeRelation.METHOD`, `ScopeRelation.FIELD`, `ScopeRelation.NESTED_CLASS`, and `ScopeRelation.NESTED_INTERFACE`, indicating the types of child elements that can be organized within these structures.
- **Use**: This variable is used to define the order in which child elements are supported within Java classes and interfaces.


# Classes

---
### JavaClassCollection 
- **Type**: `class`
- **Members**:
    - `data`: A dictionary mapping strings to either a JavaClassData instance or a list of JavaClassData instances.
- **Description**: The `JavaClassCollection` class is a specialized collection class that inherits from `IrCollection`. It is designed to manage a collection of Java class data, represented by the `JavaClassData` type. The class provides a class method `from_llm` which facilitates the creation of a `JavaClassCollection` instance using a language model (`ChatOpenAI`) and a list of raw symbols (`RawSymbolCollection`). This method leverages the `from_llm_with_ir_data` method to populate the collection with structured data about Java classes.
- **Inherits From**:
    - IrCollection

**Methods**

---
#### JavaClassCollection.from_llm
The `from_llm` function creates an instance of the class using data from a language model and a collection of symbols.
- **Inputs**:
    - `llm`: An instance of the ChatOpenAI class, representing a language model.
    - `symbols_list`: A collection of raw symbols, represented by the RawSymbolCollection class.
- **Control Flow**:
    - The function calls the `from_llm_with_ir_data` method on the class, passing `JavaClassData`, `llm`, and `symbols_list` as arguments.
    - The `from_llm_with_ir_data` method is expected to handle the instantiation process using the provided language model and symbols.
- **Output**:
    - Returns an instance of the class that called the method, initialized with data from the language model and symbols list.



---
### JavaClassData 
- **Type**: `class`
- **Members**:
    - `modifiers`: Holds a list of modifiers for the Java class.
    - `interfaces_implemented`: Stores a list of interfaces implemented by the Java class.
    - `classes_extended`: Contains a list of classes extended by the Java class.
    - `description`: Provides a textual description of the Java class.
    - `_supported_child_ordering`: Defines the order of child elements like methods, fields, nested classes, and interfaces.
- **Description**: The `JavaClassData` class is a specialized data structure that extends `IrData` to represent Java class metadata, including its modifiers, implemented interfaces, extended classes, and a description. It provides class methods to generate system and user prompts for documenting Java classes, and maps child symbols to their respective internal representations. The class also supports default instantiation with empty or default values for its attributes.
- **Inherits From**:
    - IrData

**Methods**

---
#### JavaClassData.child_to_field_name
The `child_to_field_name` function maps a `RawSymbolData` object's `symbol_kind` to a corresponding `ScopeRelation` value.
- **Inputs**:
    - `cls`: The class reference, typically used for class methods.
    - `child`: An instance of `RawSymbolData` representing a symbol with a specific kind.
- **Control Flow**:
    - A dictionary `mapping` is defined to map `SymbolKind` values to `ScopeRelation` values.
    - The function returns the `ScopeRelation` value corresponding to the `symbol_kind` of the `child` using the `get` method on the `mapping` dictionary.
- **Output**:
    - The function returns a `ScopeRelation` value that corresponds to the `symbol_kind` of the provided `RawSymbolData` object.


---
#### JavaClassData.child_to_ir
The `child_to_ir` function maps a given `RawSymbolData` to a corresponding `IrData` type based on the symbol's kind.
- **Inputs**:
    - `cls`: The class reference, typically used to access class-level attributes or methods.
    - `symbol`: An instance of `RawSymbolData` representing a symbol whose kind will determine the mapping to an `IrData` type.
- **Control Flow**:
    - A dictionary `mapping` is defined to associate `SymbolKind` values with corresponding `IrData` types or `None`.
    - The function retrieves the `symbol_kind` from the `symbol` argument and uses it to look up the corresponding value in the `mapping` dictionary.
    - The function returns the `IrData` type associated with the `symbol_kind`, or `None` if no mapping exists.
- **Output**:
    - The function returns a type of `IrData` corresponding to the `symbol_kind` of the input `symbol`, or `None` if the symbol kind is not mapped.


---
#### JavaClassData.default_instance
The `default_instance` function creates and returns a default instance of the class with empty or default values for its attributes.
- **Inputs**:
    - `cls`: The class for which a default instance is to be created.
- **Control Flow**:
    - The function is a class method, indicated by the `cls` parameter, which refers to the class itself.
    - It returns an instance of the class `cls` by calling its constructor with specific default values for its attributes.
    - The attributes `modifiers`, `interfaces_implemented`, and `classes_extended` are initialized with empty `ListedRawContentNoNone` objects.
    - The `description` attribute is initialized with an empty `FieldNameWithRawContent` object.
- **Output**:
    - An instance of the class `cls` with default values for its attributes.


---
#### JavaClassData.system_prompt
The `system_prompt` function returns a predefined JSON schema string for documenting Java classes.
- **Inputs**:
    - None
- **Control Flow**:
    - The function directly returns the value of the constant `CLASSES_FOUND_SYSTEM_PROMPT_JSON`.
- **Output**:
    - A string containing a JSON schema for documenting Java classes.


---
#### JavaClassData.user_prompt
The `user_prompt` function generates a formatted string prompt for a given Java class or method symbol, including its name and code, and optionally the full file code if available.
- **Inputs**:
    - `cls`: The class reference from which this class method is called.
    - `symbol`: An instance of `RawSymbolData` containing information about a Java class or method, including its name, symbol code, and optionally the full file code.
- **Control Flow**:
    - Initialize a string `user_prompt` with a predefined prompt string `CLASSES_FOUND_USER_PROMPT` followed by the symbol's name and its code.
    - Check if the `symbol` has `file_code` available.
    - If `file_code` is available, append it to the `user_prompt` string with a header indicating it is the full file code.
    - Return the constructed `user_prompt` string.
- **Output**:
    - A formatted string containing the prompt for the given symbol, including its name, code, and optionally the full file code.



---
### JavaClassRawSymbolCollection 
- **Type**: `class`
- **Members**:
    - `data`: A dictionary mapping string keys to RawSymbolData objects.
- **Description**: The `JavaClassRawSymbolCollection` class is a specialized collection for handling raw symbol data extracted from Java class files. It extends the `RawSymbolCollection` class and provides methods for constructing the collection from static analysis of Java code. The class primarily focuses on identifying and organizing Java class symbols, methods, fields, and nested classes or interfaces using ctags. It includes a method `from_static_analysis` that processes Java code to extract relevant symbols and organize them into a structured dictionary format, which can then be used for further analysis or documentation purposes.
- **Inherits From**:
    - RawSymbolCollection

**Methods**

---
#### JavaClassRawSymbolCollection.from_llm
The `from_llm` function raises a NotImplementedError indicating that static analysis should be used for Java classes.
- **Inputs**:
    - `code`: A string representing the code to be analyzed.
    - `root_rel_path`: A string representing the root relative path of the code.
- **Control Flow**:
    - The function immediately raises a NotImplementedError with a specific message.
- **Output**:
    - The function does not return any output as it raises an exception.


---
#### JavaClassRawSymbolCollection.from_static_analysis
The `from_static_analysis` function analyzes Java code to extract and organize class and interface symbols using ctags.
- **Inputs**:
    - `code`: A string containing the Java source code to be analyzed.
    - `root_rel_path`: A Path object representing the root relative path of the file being analyzed.
- **Control Flow**:
    - Determine if the code requires multi-prompt processing using `code_requires_multi_prompt` function.
    - Extract symbols from the code using `extract_symbols_w_ctags` function.
    - Initialize an empty dictionary `class_raw_symbol_data` to store raw symbol data for classes.
    - Iterate over the extracted symbols to identify Java classes and create raw symbol data for each class using `create_raw_symbol_via_ctags`.
    - For each symbol, check if it is a method, nested class, interface, or field within a class and append the corresponding raw symbol data to the appropriate class in `class_raw_symbol_data`.
    - Return `None` if no class symbols are found, otherwise return an instance of the class with the collected symbol data.
- **Output**:
    - The function returns an instance of the class containing the organized raw symbol data for Java classes, or `None` if no class symbols are found.


---
#### JavaClassRawSymbolCollection.to_dict
The `to_dict` function returns the `data` attribute of the instance as a dictionary.
- **Inputs**:
    - None
- **Control Flow**:
    - The function directly returns the `data` attribute of the instance without any additional processing.
- **Output**:
    - A dictionary where the keys are strings and the values are `RawSymbolData` objects.



---
### JavaFieldData 
- **Type**: `class`
- **Members**:
    - `type`: Represents the type of the Java field.
    - `description`: Provides a description of the Java field.
    - `use`: Describes how the Java field is used.
    - `modifiers`: Lists the modifiers applied to the Java field.
- **Description**: The `JavaFieldData` class is designed to encapsulate metadata about Java fields, including their type, description, usage, and modifiers. It provides class methods to generate system and user prompts for documenting fields, and it ensures that fields do not have children by raising `NotImplementedError` for related methods. The class also offers a `default_instance` method to create a default instance with empty or default values for its attributes.
- **Inherits From**:
    - IrData

**Methods**

---
#### JavaFieldData.child_to_field_name
The `child_to_field_name` function raises a `NotImplementedError` indicating that fields should not have children.
- **Inputs**:
    - `cls`: The class object that the method is bound to, typically used in class methods.
    - `child`: An instance of `RawSymbolData` representing a child symbol.
- **Control Flow**:
    - The function immediately raises a `NotImplementedError` with a specific message.
- **Output**:
    - The function does not return any value as it raises an exception.


---
#### JavaFieldData.child_to_ir
The `child_to_ir` function raises a `NotImplementedError` indicating that fields should not have children.
- **Inputs**:
    - `cls`: The class on which this method is called, typically a subclass of `IrData`.
    - `symbol`: An instance of `RawSymbolData` representing a symbol in the code.
- **Control Flow**:
    - The function immediately raises a `NotImplementedError` with a specific message.
- **Output**:
    - The function does not return any value as it raises an exception.


---
#### JavaFieldData.default_instance
The `default_instance` function creates and returns a default instance of the class with empty or default values for its fields.
- **Inputs**:
    - `cls`: The class for which a default instance is to be created.
- **Control Flow**:
    - The function is a class method, indicated by the use of `cls` as the first parameter.
    - It returns an instance of the class `cls` by calling its constructor with specific default values for its fields.
    - The `type` field is initialized with an instance of `FieldNameWithBackTickContent` with an empty string as content.
    - The `description` and `use` fields are initialized with instances of `FieldNameWithRawContent` with empty strings as content.
    - The `modifiers` field is initialized with an instance of `ListedRawContentNoNone` with an empty list as content.
- **Output**:
    - An instance of the class `cls` with default values for its fields.


---
#### JavaFieldData.system_prompt
The `system_prompt` function returns a predefined JSON string for documenting Java fields.
- **Inputs**:
    - None
- **Control Flow**:
    - The function directly returns the constant `FIELDS_FOUND_SYSTEM_PROMPT_JSON`.
- **Output**:
    - The output is a string containing a JSON schema for documenting Java fields.


---
#### JavaFieldData.user_prompt
The `user_prompt` function generates a formatted string prompt for a user based on the provided symbol data.
- **Inputs**:
    - `symbol`: An instance of `RawSymbolData` containing the name, symbol code, and optionally file code of a symbol.
- **Control Flow**:
    - Initialize a string `user_prompt` with a formatted message including the symbol's name and symbol code.
    - Check if the `symbol` has `file_code` and, if so, append it to the `user_prompt`.
    - Return the constructed `user_prompt` string.
- **Output**:
    - A formatted string containing the symbol's name, symbol code, and optionally the full file code.



---
### JavaInterfaceCollection 
- **Type**: `class`
- **Members**:
    - `data`: A dictionary mapping strings to either a JavaInterfaceData object or a list of such objects.
- **Description**: The `JavaInterfaceCollection` class is a specialized collection class that inherits from `IrCollection`. It is designed to manage a collection of Java interface data, represented by the `JavaInterfaceData` class. The class provides a class method `from_llm` which facilitates the creation of a `JavaInterfaceCollection` instance from a language model and a list of raw symbols, using the `JavaInterfaceData` class to process the data. This class is part of a system that likely involves the analysis and documentation of Java code, focusing on interfaces.
- **Inherits From**:
    - IrCollection

**Methods**

---
#### JavaInterfaceCollection.from_llm
The `from_llm` function creates an instance of the class by invoking the `from_llm_with_ir_data` method with `JavaInterfaceData`, a language model, and a collection of symbols.
- **Inputs**:
    - `llm`: An instance of the `ChatOpenAI` class, representing a language model.
    - `symbols_list`: An instance of `RawSymbolCollection`, representing a collection of raw symbols.
- **Control Flow**:
    - The function calls the `from_llm_with_ir_data` method on the class `cls`, passing `JavaInterfaceData`, `llm`, and `symbols_list` as arguments.
- **Output**:
    - The function returns an instance of the class `cls` created using the `from_llm_with_ir_data` method.



---
### JavaInterfaceData 
- **Type**: `class`
- **Members**:
    - `interfaces_extended`: A list of interfaces that this Java interface extends.
    - `description`: A textual description of the Java interface.
    - `_supported_child_ordering`: A private attribute defining the order of supported child elements like methods and fields.
- **Description**: The `JavaInterfaceData` class is a specialized data structure that extends `IrData` and is designed to represent and document Java interfaces. It includes attributes for listing extended interfaces and providing a description of the interface. The class also defines a private attribute for supported child ordering, which includes methods, fields, nested classes, and interfaces. It provides class methods to generate system and user prompts for documenting Java interfaces, and it maps child symbols to their respective intermediate representations or field names.
- **Inherits From**:
    - IrData

**Methods**

---
#### JavaInterfaceData.child_to_field_name
The `child_to_field_name` function maps a `RawSymbolData` object's `symbol_kind` to a corresponding `ScopeRelation` value.
- **Inputs**:
    - `cls`: The class reference, typically used in class methods.
    - `child`: An instance of `RawSymbolData` representing a symbol with a specific kind.
- **Control Flow**:
    - A dictionary `mapping` is defined to map `SymbolKind` values to `ScopeRelation` values.
    - The function returns the value from the `mapping` dictionary corresponding to the `symbol_kind` of the `child` argument.
- **Output**:
    - The function returns a `ScopeRelation` value corresponding to the `symbol_kind` of the `child` argument, or `None` if no match is found.


---
#### JavaInterfaceData.child_to_ir
The `child_to_ir` function maps a `RawSymbolData` instance to a corresponding `IrData` type based on the symbol's kind.
- **Inputs**:
    - `cls`: The class reference, typically used to call class methods.
    - `symbol`: An instance of `RawSymbolData` representing a symbol with a specific kind.
- **Control Flow**:
    - A dictionary `mapping` is defined to associate `SymbolKind` values with corresponding `IrData` types or `None`.
    - The function retrieves the `symbol_kind` from the `symbol` argument and uses it to look up the corresponding `IrData` type in the `mapping` dictionary.
    - The function returns the `IrData` type associated with the `symbol_kind`, or `None` if no mapping exists.
- **Output**:
    - The function returns a type of `IrData` corresponding to the `symbol_kind` of the input `symbol`, or `None` if the symbol kind is not mapped.


---
#### JavaInterfaceData.default_instance
The `default_instance` function creates and returns a default instance of the class with empty content for its fields.
- **Inputs**:
    - `cls`: The class for which a default instance is to be created.
- **Control Flow**:
    - The function is a class method, indicated by the use of `cls` as its first parameter.
    - It returns an instance of the class `cls` by calling its constructor.
    - The constructor is called with two keyword arguments: `interfaces_extended` and `description`.
    - `interfaces_extended` is initialized with an instance of `ListedRawContentNoNone` with an empty list as its content.
    - `description` is initialized with an instance of `FieldNameWithRawContent` with an empty string as its content.
- **Output**:
    - An instance of the class `cls` with default values for its fields.


---
#### JavaInterfaceData.system_prompt
The `system_prompt` function returns a predefined JSON string for documenting Java interfaces.
- **Inputs**:
    - None
- **Control Flow**:
    - The function directly returns the constant `INTERFACES_FOUND_SYSTEM_PROMPT_JSON`.
- **Output**:
    - A string containing a JSON schema for documenting Java interfaces.


---
#### JavaInterfaceData.user_prompt
The `user_prompt` function generates a formatted string prompt for documenting a Java interface or method using the provided symbol data.
- **Inputs**:
    - `cls`: The class reference, typically used in class methods.
    - `symbol`: An instance of RawSymbolData containing the name, symbol code, and optionally the full file code of the Java interface or method to be documented.
- **Control Flow**:
    - Initialize a string `user_prompt` with a predefined prompt template concatenated with the symbol's name and code.
    - Check if the `symbol` has associated file code; if so, append it to the `user_prompt` string.
    - Return the constructed `user_prompt` string.
- **Output**:
    - A formatted string that serves as a prompt for documenting a Java interface or method, including its name, code, and optionally the full file code.



---
### JavaInterfaceRawSymbolCollection 
- **Type**: `class`
- **Members**:
    - `data`: A dictionary mapping string keys to RawSymbolData objects.
- **Description**: The `JavaInterfaceRawSymbolCollection` class is a specialized collection for handling raw symbol data related to Java interfaces. It extends the `RawSymbolCollection` class and provides methods for constructing the collection from static analysis of Java code. The class focuses on extracting and organizing symbols that represent Java interfaces and their associated methods, classes, and fields using ctags. It does not support creation from LLM (Language Model) and raises a `NotImplementedError` for such attempts, emphasizing the use of static analysis for Java interfaces.
- **Inherits From**:
    - RawSymbolCollection

**Methods**

---
#### JavaInterfaceRawSymbolCollection.from_llm
The `from_llm` function raises a NotImplementedError indicating that static analysis should be used for Java interfaces.
- **Inputs**:
    - `code`: A string representing the code to be analyzed.
    - `root_rel_path`: A string representing the root relative path of the code file.
- **Control Flow**:
    - The function immediately raises a NotImplementedError with a specific message.
- **Output**:
    - The function does not return any output as it raises an exception.


---
#### JavaInterfaceRawSymbolCollection.from_static_analysis
The `from_static_analysis` function analyzes Java code to extract and organize interface symbols and their related components using static analysis.
- **Inputs**:
    - `code`: A string containing the Java source code to be analyzed.
    - `root_rel_path`: A Path object representing the root-relative path to the file containing the Java code.
- **Control Flow**:
    - Determine if the code requires multi-prompt processing using `code_requires_multi_prompt`.
    - Extract symbols from the code using `extract_symbols_w_ctags`.
    - Initialize an empty dictionary `interface_raw_symbol_data` to store interface-related symbol data.
    - Iterate over the extracted symbols to identify and process interface symbols, creating raw symbol data for each and storing it in `interface_raw_symbol_data`.
    - For each symbol, check its kind and scope to determine if it is a method, class, interface, or field within an interface, and append the corresponding raw symbol data to the appropriate interface entry in `interface_raw_symbol_data`.
    - Return an instance of the class with the collected interface symbol data if any symbols were found, otherwise return None.
- **Output**:
    - An instance of the class containing the interface symbol data if any interfaces are found, otherwise None.


---
#### JavaInterfaceRawSymbolCollection.to_dict
The `to_dict` function returns the `data` attribute of the instance as a dictionary.
- **Inputs**:
    - None
- **Control Flow**:
    - The function directly returns the `data` attribute of the instance without any additional processing.
- **Output**:
    - A dictionary where the keys are strings and the values are `RawSymbolData` objects.



---
### JavaMethodData 
- **Type**: `class`
- **Members**:
    - `single_sentence`: A brief description of the Java method.
    - `modifiers`: A list of modifiers applied to the Java method.
    - `inputs`: A list of input parameters for the Java method.
    - `control_flow`: A list describing the control flow of the Java method.
    - `output`: A description of the output of the Java method.
- **Description**: The `JavaMethodData` class is a specialized data structure that extends `IrData` to encapsulate information about Java methods. It includes fields for a single sentence description, method modifiers, input parameters, control flow details, and output description. The class provides class methods to generate system and user prompts for documenting Java methods, and it enforces that methods should not have children by raising `NotImplementedError` for related methods. It also provides a `default_instance` method to create an instance with default values.
- **Inherits From**:
    - IrData

**Methods**

---
#### JavaMethodData.child_to_field_name
The `child_to_field_name` function raises a `NotImplementedError` indicating that methods should not have children.
- **Inputs**:
    - `cls`: The class on which this method is called, typically a class method.
    - `child`: An instance of `RawSymbolData` representing a child symbol.
- **Control Flow**:
    - The function immediately raises a `NotImplementedError` with a specific message.
- **Output**:
    - The function does not return any value as it raises an exception.


---
#### JavaMethodData.child_to_ir
The `child_to_ir` function raises a NotImplementedError indicating that methods should not have children.
- **Inputs**:
    - `cls`: The class on which this method is called, typically a subclass of IrData.
    - `symbol`: An instance of RawSymbolData representing a symbol in the code.
- **Control Flow**:
    - The function immediately raises a NotImplementedError with a specific message.
- **Output**:
    - The function does not return any value as it raises an exception.


---
#### JavaMethodData.default_instance
The `default_instance` function creates and returns a default instance of the class with empty or default values for its attributes.
- **Inputs**:
    - `cls`: The class for which a default instance is to be created.
- **Control Flow**:
    - The function is a class method, indicated by the `cls` parameter, which refers to the class itself.
    - It returns an instance of the class by calling the class constructor with default or empty values for each of the class's attributes.
- **Output**:
    - An instance of the class with default or empty values for its attributes.


---
#### JavaMethodData.system_prompt
The `system_prompt` function returns a predefined JSON string for documenting Java class methods.
- **Inputs**:
    - None
- **Control Flow**:
    - The function directly returns the constant `METHODS_FOUND_SYSTEM_PROMPT_JSON`.
- **Output**:
    - A string containing a JSON schema for documenting Java class methods.


---
#### JavaMethodData.user_prompt
The `user_prompt` function generates a formatted string prompt for a user based on a given symbol's name and code, optionally including the full file code if available.
- **Inputs**:
    - `symbol`: An instance of `RawSymbolData` containing the name, symbol code, and optionally the full file code of a symbol.
- **Control Flow**:
    - Initialize a string `user_prompt` with a formatted message including the symbol's name and code.
    - Check if the `symbol` has `file_code` and, if so, append the full file code to `user_prompt`.
- **Output**:
    - A formatted string that includes the symbol's name, its code, and optionally the full file code.



