# Purpose
This Python code file is designed to facilitate the analysis and categorization of source code symbols across various programming languages. It provides a structured approach to identify and classify symbols such as variables, functions, classes, and modules using different parsing techniques, including ctags, Tree-sitter, and language models (LLMs). The file defines several enumerations and data classes to represent languages, parser types, symbol kinds, and scope relations, which are crucial for understanding the context and relationships of symbols within the code. The `Lang` class, for instance, helps determine the programming language based on file extensions, while the `SymbolKind` and `ScopeRelation` classes categorize symbols and their hierarchical relationships.

The file also includes functions for creating and managing symbol data, such as `create_raw_symbol_via_ctags` and `create_raw_symbol_via_llm`, which generate symbol representations using different parsing methods. Additionally, the `disambiguate_header` function uses a language model to determine whether a header file is more aligned with C or C++ standards. The code is structured to be part of a larger system, likely a library or module, that can be imported and used for static code analysis or code intelligence tasks. It does not define a public API but provides essential building blocks for symbol extraction and analysis, making it a specialized tool for developers and systems that require detailed code structure insights.
# Imports and Dependencies

---
- `abc`
- `textwrap`
- `dataclasses`
- `enum`
- `pathlib`
- `typing`
- `openai`
- `pydantic`
- `utils.codemap_ctags`
- `utils.models`
- `shared.chunking.text_splitter`


# Global Variables

---
### ASSEMBLY 
- **Type**: `IntEnum`
- **Description**: The `ASSEMBLY` variable is an enumeration member of the `Lang` class, which is a subclass of `IntEnum`. It represents the integer value 6, corresponding to the assembly language in the context of this enumeration.
- **Use**: This variable is used to identify and categorize assembly language files based on their file extensions.


---
### ATTRIBUTE 
- **Type**: `StrEnum`
- **Description**: `ATTRIBUTE` is a member of the `ScopeRelation` enumeration, which is a subclass of `StrEnum`. This enumeration defines various types of relationships that a child symbol can have with its parent scope, such as methods, nested classes, and attributes.
- **Use**: `ATTRIBUTE` is used to represent the relationship of a child symbol being an attribute of its parent scope in the `ScopeRelation` enumeration.


---
### BLIND_ADVANCE_IF_NO_END_LINE 
- **Type**: `int`
- **Description**: `BLIND_ADVANCE_IF_NO_END_LINE` is an integer constant set to 200. It is used as a default value for the number of lines to advance when an end line is not specified in certain operations, such as symbol extraction or parsing.
- **Use**: This variable is used to determine how many lines to advance when an end line is not explicitly provided, ensuring that operations can continue without interruption.


---
### BLIND_PADDING_BOTTOM 
- **Type**: `int`
- **Description**: `BLIND_PADDING_BOTTOM` is an integer variable set to 10. It is used to define the number of lines to be added as padding at the bottom when extracting code segments.
- **Use**: This variable is used to ensure that a certain number of lines are included as padding at the bottom of a code segment during extraction.


---
### BLIND_PADDING_TOP 
- **Type**: `int`
- **Description**: `BLIND_PADDING_TOP` is an integer constant set to 100. It is used to define the number of lines to pad at the top when extracting code segments.
- **Use**: This variable is used to calculate the starting line for code extraction, ensuring that additional context is included above the specified start line.


---
### C 
- **Type**: `IntEnum`
- **Description**: The variable `C` is a member of the `Lang` enumeration class, which is an `IntEnum`. It represents the integer value `0`, corresponding to the C programming language. This enumeration is used to categorize different programming languages by associating them with specific integer values.
- **Use**: The `C` variable is used to identify and differentiate the C programming language within the `Lang` enumeration.


---
### CALL 
- **Type**: `Enum`
- **Description**: The `CALL` variable is an enumeration member of the `SymbolKind` Enum class. It represents a specific kind of symbol that can be identified in code, specifically a function or method call.
- **Use**: This variable is used to categorize and identify symbols in code as function or method calls within the `SymbolKind` enumeration.


---
### CALLABLE 
- **Type**: `Enum`
- **Description**: `CALLABLE` is an enumeration member of the `SymbolKind` Enum class. It represents a type of symbol that is callable, such as functions or methods, within the context of symbol parsing and analysis.
- **Use**: This variable is used to categorize and identify callable symbols when parsing and analyzing code structures.


---
### CALLABLE_DECLARATION 
- **Type**: `Enum`
- **Description**: `CALLABLE_DECLARATION` is an enumeration member of the `SymbolKind` Enum class. It represents a specific kind of symbol that can be identified in code, specifically a callable declaration, which is a declaration of a function or method without its implementation.
- **Use**: This variable is used to categorize and identify callable declarations within the code analysis process.


---
### CHUNK_OVERLAP 
- **Type**: `int`
- **Description**: `CHUNK_OVERLAP` is an integer variable set to 1,000. It represents the number of overlapping characters between consecutive chunks of text when splitting a large text into smaller parts.
- **Use**: This variable is used to ensure that there is a consistent overlap between text chunks, which can be important for maintaining context across chunk boundaries when processing large texts.


---
### CHUNK_SIZE 
- **Type**: `int`
- **Description**: `CHUNK_SIZE` is a global integer variable set to 64,000. It represents the size of chunks used when splitting text or code into smaller parts for processing.
- **Use**: This variable is used to define the maximum size of each chunk when splitting text or code, ensuring that the chunks do not exceed this size.


---
### CLASS 
- **Type**: `Enum`
- **Description**: The `CLASS` variable is an enumeration member of the `SymbolKind` Enum class. It represents a specific kind of symbol, specifically a class, within the context of symbol parsing and analysis.
- **Use**: This variable is used to identify and categorize symbols that are classes when parsing code.


---
### CLASS_METHOD 
- **Type**: `str`
- **Description**: `CLASS_METHOD` is a string constant defined within the `ScopeRelation` enumeration class. It represents a specific type of relationship between a child symbol and its parent scope, specifically indicating that the child is a class method of the parent class.
- **Use**: This variable is used to categorize and identify class methods within a symbol's scope in the context of code analysis or parsing.


---
### CPP 
- **Type**: `IntEnum`
- **Description**: The `CPP` variable is an enumeration member of the `Lang` class, which is a subclass of `IntEnum`. It represents the C++ programming language and is assigned the integer value 1.
- **Use**: This variable is used to identify and differentiate C++ code files based on their extensions in the `Lang` enumeration.


---
### C_OR_CPP_HEADER 
- **Type**: `IntEnum`
- **Description**: `C_OR_CPP_HEADER` is an enumeration value within the `Lang` class, which is a subclass of `IntEnum`. It represents a specific language type used to categorize files that are C or C++ header files. This value is used to identify files with extensions like `.h`, `.hpp`, `.hh`, `.hxx`, and `.h++` as either C or C++ header files.
- **Use**: This variable is used to classify and handle files that are C or C++ headers within the `Lang` enumeration.


---
### C_SHARP 
- **Type**: `IntEnum`
- **Description**: `C_SHARP` is an enumeration member of the `Lang` class, which is a subclass of `IntEnum`. It represents the C# programming language within this enumeration and is assigned the integer value 9.
- **Use**: This variable is used to identify and differentiate the C# programming language in the `Lang` enumeration, particularly when determining the language type based on file extensions.


---
### DATA_STRUCTURE 
- **Type**: `Enum`
- **Description**: The `DATA_STRUCTURE` variable is an enumeration member of the `SymbolKind` Enum class. It represents a specific kind of symbol that can be identified in code, specifically a data structure.
- **Use**: This variable is used to categorize and identify symbols in code as data structures within the `SymbolKind` enumeration.


---
### DATA_STRUCTURE_INSTANCE 
- **Type**: `Enum`
- **Description**: `DATA_STRUCTURE_INSTANCE` is an enumeration member of the `SymbolKind` Enum class. It represents a specific kind of symbol that can be identified in code, specifically an instance of a data structure.
- **Use**: This variable is used to categorize symbols as instances of data structures within the code analysis process.


---
### DEFAULT 
- **Type**: `Lang`
- **Description**: The `DEFAULT` variable is an enumeration member of the `Lang` class, which is a subclass of `IntEnum`. It represents a default language type with an integer value of 10. This enumeration is used to categorize different programming languages based on file extensions and source code characteristics.
- **Use**: The `DEFAULT` variable is used as a fallback language type when a file extension does not match any predefined language categories in the `Lang` enumeration.


---
### ENUMERATOR 
- **Type**: `StrEnum`
- **Description**: `ENUMERATOR` is a member of the `ScopeRelation` enumeration class, which is a subclass of `StrEnum`. It represents a specific type of relationship between a child symbol and its parent scope, specifically indicating that the child is an enumerator within the parent scope.
- **Use**: This variable is used to categorize and identify enumerator relationships in symbol parsing and analysis.


---
### FIELD 
- **Type**: `pydantic.fields.ModelField`
- **Description**: The `FIELD` variable is a global variable imported from the `pydantic` library. It is used to define fields in Pydantic models, allowing for the specification of default values, validation, and metadata for model attributes.
- **Use**: This variable is used to define and configure fields within Pydantic data models.


---
### IMPORT 
- **Type**: `Enum`
- **Description**: `IMPORT` is an enumeration member of the `SymbolKind` Enum class. It represents a specific kind of symbol that can be identified in code, specifically an import statement or directive.
- **Use**: This variable is used to categorize and identify import symbols within a codebase when analyzing or parsing code.


---
### INSTANCE_METHOD 
- **Type**: `StrEnum`
- **Description**: `INSTANCE_METHOD` is a member of the `ScopeRelation` enumeration, which is a subclass of `StrEnum`. It represents a specific type of relationship between a child symbol and its parent scope, specifically indicating that the child is an instance method of the parent class.
- **Use**: This variable is used to categorize and identify instance methods within a symbol's scope relation in the code analysis process.


---
### INTERFACE 
- **Type**: `Enum`
- **Description**: The `INTERFACE` is a member of the `SymbolKind` enumeration, which is used to categorize different types of symbols in a codebase. This enumeration includes various symbol types such as VARIABLE, CALLABLE, CLASS, INTERFACE, and others, each representing a distinct kind of code element.
- **Use**: This variable is used to identify and categorize symbols that represent interfaces within a codebase.


---
### JAVA 
- **Type**: `IntEnum`
- **Description**: The `JAVA` variable is an enumeration member of the `Lang` class, which is a subclass of `IntEnum`. It represents the Java programming language with an associated integer value of 7.
- **Use**: This variable is used to identify and differentiate Java code files based on their file extension within the `Lang` enumeration.


---
### LLM 
- **Type**: `ParserKind`
- **Description**: The `LLM` variable is an enumeration member of the `ParserKind` Enum class. It represents a specific type of parser that is likely related to language model processing, as suggested by the name 'LLM' (Large Language Model).
- **Use**: This variable is used to specify the type of parser being utilized, particularly when the parser is based on a language model.


---
### METHOD 
- **Type**: `StrEnum`
- **Description**: `METHOD` is a member of the `ScopeRelation` enumeration, which is a subclass of `StrEnum`. It represents the relationship of a child symbol to its parent scope, specifically indicating that the child is a method of the parent class.
- **Use**: This variable is used to categorize and identify methods within a class in the context of symbol parsing and analysis.


---
### MODULE 
- **Type**: `SymbolKind`
- **Description**: The `MODULE` variable is an enumeration member of the `SymbolKind` Enum class. It represents a specific kind of symbol, in this case, a module, which is a logical grouping of code elements in programming.
- **Use**: This variable is used to categorize or identify symbols that are modules within the codebase.


---
### MODULE_METHOD 
- **Type**: `str`
- **Description**: `MODULE_METHOD` is a string constant defined in the `ScopeRelation` enumeration class. It represents a specific type of relationship between a child symbol and its parent scope, specifically indicating that the child is a method belonging to a module.
- **Use**: This variable is used to categorize and identify module methods within a symbol's scope relation in the codebase.


---
### NESTED_CLASS 
- **Type**: `StrEnum`
- **Description**: `NESTED_CLASS` is a member of the `ScopeRelation` enumeration, which is a subclass of `StrEnum`. It represents a specific type of relationship between a child symbol and its parent scope, specifically indicating that the child is a nested class within the parent.
- **Use**: This variable is used to categorize and identify nested classes within a parent scope in the context of symbol parsing and analysis.


---
### NESTED_DATA_STRUCTURE 
- **Type**: `StrEnum`
- **Description**: `NESTED_DATA_STRUCTURE` is a member of the `ScopeRelation` enumeration, which is a subclass of `StrEnum`. It represents a specific type of relationship between a child symbol and its parent scope, specifically indicating that the child is a nested data structure within the parent.
- **Use**: This variable is used to categorize and identify nested data structures in the context of symbol parsing and scope relations.


---
### NESTED_INTERFACE 
- **Type**: `StrEnum`
- **Description**: `NESTED_INTERFACE` is a member of the `ScopeRelation` enumeration, which is a subclass of `StrEnum`. It represents a specific type of relationship between a child symbol and its parent scope, specifically indicating that the child is a nested interface within the parent scope.
- **Use**: This variable is used to categorize and identify nested interfaces within a parent scope in symbol analysis.


---
### PYTHON 
- **Type**: `IntEnum`
- **Description**: The `PYTHON` variable is an enumeration member of the `Lang` class, which is a subclass of `IntEnum`. It represents the integer value `3`, corresponding to the Python programming language within the `Lang` enumeration.
- **Use**: This variable is used to identify and differentiate the Python language in a set of supported programming languages.


---
### RUBY 
- **Type**: `IntEnum`
- **Description**: The `RUBY` variable is an enumeration member of the `Lang` class, which is a subclass of `IntEnum`. It represents the Ruby programming language within a set of predefined programming languages, each associated with a unique integer value.
- **Use**: This variable is used to identify and differentiate Ruby source files based on their file extensions, such as '.rb' or '.rbi', within the `Lang` enumeration.


---
### RUST 
- **Type**: `IntEnum`
- **Description**: The `RUST` variable is an enumeration member of the `Lang` class, which is a subclass of `IntEnum`. It represents the programming language Rust with an associated integer value of 5. This enumeration is used to categorize and identify different programming languages by their file extensions.
- **Use**: This variable is used to identify Rust source files based on their file extension, specifically ".rs", within the `Lang` enumeration.


---
### TREE_SITTER 
- **Type**: `Enum`
- **Description**: `TREE_SITTER` is an enumeration member of the `ParserKind` Enum class. It represents one of the possible types of parsers that can be used, specifically indicating the use of the Tree-sitter parser.
- **Use**: This variable is used to specify the type of parser being utilized in the context of symbol parsing and analysis.


---
### UCTAGS 
- **Type**: `Enum`
- **Description**: `UCTAGS` is an enumeration member of the `ParserKind` Enum class. It represents a specific type of parser used in the code, specifically the Universal Ctags parser.
- **Use**: This variable is used to specify the parser kind when creating or handling raw symbol data.


---
### VARIABLE 
- **Type**: `Enum`
- **Description**: The `VARIABLE` is an enumeration member of the `SymbolKind` Enum class. It represents a specific kind of symbol that can be identified in code, specifically a variable.
- **Use**: This variable is used to categorize and identify symbols of type 'variable' within the code analysis process.


---
### VERILOG 
- **Type**: `IntEnum`
- **Description**: The `VERILOG` variable is an enumeration member of the `Lang` class, which is a subclass of `IntEnum`. It represents the Verilog programming language and is assigned the integer value 4. This enumeration is used to categorize and identify different programming languages by their file extensions.
- **Use**: This variable is used to identify and handle Verilog files based on their extensions, such as '.v' and '.sv', within the `Lang` class.


---
### calls 
- **Type**: `list[Self]`
- **Description**: The `calls` variable is a list of `ReifiedSymbol` instances, which are used to represent symbols in a codebase that have been extended with additional information, such as a list of usages. This list specifically holds instances of symbols that are calls, meaning they represent function or method invocations within the code.
- **Use**: This variable is used to store and manage a collection of call symbols associated with a particular `ReifiedSymbol` instance.


---
### declarations 
- **Type**: `list[Self]`
- **Description**: The `declarations` variable is a list of `ReifiedSymbol` instances, which are used to represent symbol declarations in the code. Each `ReifiedSymbol` contains information about a symbol's raw data, whether it is a definition or declaration, and its associated usages and calls. The list is initialized with a default factory, indicating it starts as an empty list.
- **Use**: This variable is used to store and manage a collection of symbol declarations within a `ReifiedSymbol` instance.


---
### definition 
- **Type**: `ReifiedSymbol`
- **Description**: The `definition` variable is an instance of the `ReifiedSymbol` class, which is a data structure that extends `LinkedSymbol` with additional information about symbol usages, specifically if it is a definition. It contains attributes such as `raw`, `is_definition`, `is_declaration`, and lists for `usages`, `calls`, and `declarations`. The `definition` attribute itself is a reference to another `ReifiedSymbol` instance or `None`, indicating the symbol's definition if it exists.
- **Use**: This variable is used to store and manage detailed information about a symbol's definition and its relationships within the code.


---
### frozen 
- **Type**: `bool`
- **Description**: The `frozen` variable is a configuration setting within the `Config` class of the `RawTreeSitterSymbolData` model, which is a subclass of `BaseModel` from the Pydantic library. It is set to `True`, indicating that instances of this model are immutable after creation.
- **Use**: This variable is used to ensure that instances of `RawTreeSitterSymbolData` cannot be modified after they are created, providing a level of data integrity and consistency.


---
### is_large_file 
- **Type**: `bool`
- **Description**: The `is_large_file` variable is a boolean field within the `RawSymbolData` class, which is part of a data model for representing symbols in code. It indicates whether the file associated with the symbol is considered large.
- **Use**: This variable is used to determine if special handling, such as chunking, is needed for processing large files.


---
### is_overloaded 
- **Type**: `bool`
- **Description**: The `is_overloaded` variable is a boolean field within the `RawSymbolData` class, which is part of a data model for representing symbols in code. It indicates whether a particular symbol is considered overloaded, which typically means that the symbol has multiple definitions or uses in different contexts.
- **Use**: This variable is used to determine if a symbol should be treated as overloaded, affecting how its code is processed and stored.


---
### reified_symbol 
- **Type**: `ReifiedSymbol | None`
- **Description**: The `reified_symbol` is an optional attribute of the `RawSymbolData` class, which can hold an instance of the `ReifiedSymbol` class. The `ReifiedSymbol` class extends `LinkedSymbol` with additional information such as a list of usages, calls, and declarations if the symbol is a definition. This attribute is used to provide a more detailed representation of a symbol, including its relationships and usages in the code.
- **Use**: This variable is used to store an optional detailed representation of a symbol, including its usages and relationships, within the `RawSymbolData` class.


---
### usages 
- **Type**: `list[Self]`
- **Description**: The `usages` variable is a list of `ReifiedSymbol` instances, which represents the usages of a particular symbol if it is a definition. It is part of the `ReifiedSymbol` dataclass, which extends `LinkedSymbol` to include additional information about symbol usage, calls, and declarations.
- **Use**: This variable is used to store and manage the list of usages for a symbol definition within the `ReifiedSymbol` dataclass.


# Classes

---
### Config 
- **Type**: `class`
- **Members**:
    - `frozen`: A class variable indicating that the class is immutable.
- **Description**: The `Config` class is a simple class that provides a configuration setting for immutability by setting the `frozen` attribute to `True`. This implies that instances of this class, or classes that use this as a configuration, are intended to be immutable, meaning their state cannot be modified after creation. The class also includes a docstring that suggests it provides a `__hash__` method, which is typically associated with immutability, allowing instances to be used as keys in dictionaries or stored in sets.


---
### Lang 
- **Type**: `class`
- **Members**:
    - `C`: Represents the C programming language with an integer value of 0.
    - `CPP`: Represents the C++ programming language with an integer value of 1.
    - `C_OR_CPP_HEADER`: Represents C or C++ header files with an integer value of 2.
    - `PYTHON`: Represents the Python programming language with an integer value of 3.
    - `VERILOG`: Represents the Verilog hardware description language with an integer value of 4.
    - `RUST`: Represents the Rust programming language with an integer value of 5.
    - `ASSEMBLY`: Represents assembly language with an integer value of 6.
    - `JAVA`: Represents the Java programming language with an integer value of 7.
    - `RUBY`: Represents the Ruby programming language with an integer value of 8.
    - `C_SHARP`: Represents the C# programming language with an integer value of 9.
    - `DEFAULT`: Represents a default language with an integer value of 10.
- **Description**: The `Lang` class is an enumeration that extends `IntEnum` to represent various programming languages and file types with integer values. It provides a method `from_ext_and_source` to determine the language based on file extension and source content, returning the appropriate language enum value. The class also includes a `__str__` method to return the name of the language as a string.
- **Inherits From**:
    - IntEnum

**Methods**

---
#### Lang.__str__
The `__str__` function returns the name of the enumeration member as a string.
- **Inputs**:
    - `self`: An instance of the enumeration class `Lang`.
- **Control Flow**:
    - The function directly returns the `name` attribute of the enumeration instance.
- **Output**:
    - A string representing the name of the enumeration member.


---
#### Lang.from_ext_and_source
The `from_ext_and_source` function determines the programming language type based on a file extension and source code.
- **Inputs**:
    - `ext`: A string representing the file extension, such as '.c', '.cpp', '.py', etc.
    - `source`: A string representing the source code of the file, although it is not used in the current implementation of the function.
- **Control Flow**:
    - The function uses a match-case statement to compare the provided file extension against a set of predefined cases.
    - For each case, it returns a corresponding class attribute from the `Lang` enumeration, which represents a specific programming language.
    - If the file extension does not match any of the predefined cases, the function returns `cls.DEFAULT`.
- **Output**:
    - The function returns a member of the `Lang` enumeration, which represents the programming language associated with the given file extension.



---
### ParserKind 
- **Type**: `class`
- **Members**:
    - `UCTAGS`: Represents a parser kind using Universal Ctags.
    - `TREE_SITTER`: Represents a parser kind using Tree-sitter.
    - `LLM`: Represents a parser kind using a Language Model.
- **Description**: The `ParserKind` class is an enumeration that defines different types of parsers that can be used in the system. It includes three members: `UCTAGS`, `TREE_SITTER`, and `LLM`, each representing a specific parser type. This class is used to categorize and manage different parsing strategies within the application.
- **Inherits From**:
    - Enum


---
### RawSymbolCollection 
- **Type**: `class`
- **Members**:
    - `data`: A dictionary mapping string keys to RawSymbolData objects.
- **Description**: The `RawSymbolCollection` class is an abstract base class that extends `BaseModel` and is designed to manage a collection of raw symbol data. It contains a dictionary `data` that maps string keys to `RawSymbolData` objects, representing various symbols extracted from code. The class provides abstract methods `from_llm` and `to_dict`, which must be implemented by subclasses to create a collection from a language model and to convert the collection to a dictionary, respectively.
- **Inherits From**:
    - BaseModel
    - abc.ABC

**Methods**

---
#### RawSymbolCollection.from_llm
The `from_llm` function is an abstract class method intended to create an instance of a class from code and a root relative path using a language model.
- **Inputs**:
    - `code`: A string representing the source code from which the class instance should be created.
    - `root_rel_path`: A `Path` object representing the root relative path associated with the source code.
- **Control Flow**:
    - The function is defined as an abstract class method, indicating that it must be implemented by subclasses of `RawSymbolCollection`.
    - The function takes two parameters: `code` and `root_rel_path`, but the body of the function is not implemented (indicated by `pass`).
    - The function is expected to return an instance of the class (`Self`) or `None`, but the actual logic for this is not provided in the code snippet.
- **Output**:
    - The function is expected to return an instance of the class (`Self`) or `None`, but the actual return value is not defined in the provided code.


---
#### RawSymbolCollection.to_dict
The `to_dict` function is an abstract method intended to convert a `RawSymbolCollection` instance into a dictionary mapping string keys to `RawSymbolData` objects.
- **Inputs**:
    - None
- **Control Flow**:
    - The function is defined as an abstract method within the `RawSymbolCollection` class, indicating that any subclass must implement this method.
    - The function signature suggests it returns a dictionary with string keys and `RawSymbolData` values, but the actual implementation is not provided in the code snippet.
- **Output**:
    - A dictionary where keys are strings and values are `RawSymbolData` objects.



---
### RawSymbolData 
- **Type**: `class`
- **Members**:
    - `parser_kind`: Specifies the kind of parser used to generate the symbol data.
    - `symbol_kind`: Indicates the type of symbol, such as variable, callable, or class.
    - `name`: The name of the symbol.
    - `path`: The file path where the symbol is located.
    - `scope`: The scope in which the symbol is defined, if applicable.
    - `scope_relation`: Describes the relationship of the symbol to its scope, such as method or field.
    - `children`: A list of child symbols contained within this symbol.
    - `start_line`: The starting line number of the symbol in the source code.
    - `end_line`: The ending line number of the symbol in the source code.
    - `symbol_code`: The code snippet representing the symbol.
    - `file_code`: The full code of the file containing the symbol.
    - `reference_code`: Code that references this symbol, if any.
    - `delimiter`: A delimiter used in parsing the symbol, if applicable.
    - `is_large_file`: Indicates if the symbol is part of a large file.
    - `is_overloaded`: Indicates if the symbol is overloaded.
    - `reified_symbol`: An optional reified symbol associated with this raw symbol data.
- **Description**: The `RawSymbolData` class is a data model that represents detailed information about a symbol extracted from source code. It includes attributes to describe the symbol's parser type, kind, name, location, scope, and code representation. The class also provides a class method `from_tree_sitter_raw_symbol` to construct an instance from raw symbol data obtained via the Tree-sitter parser, handling large files and overloaded symbols by splitting code into chunks if necessary. This class is part of a system for analyzing and managing code symbols, supporting various parsing strategies and symbol kinds.
- **Inherits From**:
    - BaseModel

**Methods**

---
#### RawSymbolData.from_tree_sitter_raw_symbol
The `from_tree_sitter_raw_symbol` function constructs a `RawSymbolData` object from a `RawTreeSitterSymbolData` instance and additional parameters, handling code extraction and chunking for large or overloaded files.
- **Inputs**:
    - `ts_symbol`: An instance of `RawTreeSitterSymbolData` containing the raw symbol data extracted by Tree Sitter.
    - `path`: A `Path` object representing the file path where the symbol is located.
    - `scope`: An optional string representing the scope of the symbol.
    - `scope_relation`: An optional `ScopeRelation` enum value indicating the relationship of the symbol to its parent scope.
    - `children`: A list of `RawSymbolData` instances representing the child symbols of the current symbol.
    - `reference_code`: An optional string containing reference code related to the symbol.
    - `delimiter`: An optional string used to delimit parts of the symbol's scope.
    - `is_large_file`: A boolean indicating if the file is considered large.
    - `is_overloaded`: A boolean indicating if the symbol is overloaded.
    - `use_padding`: A boolean indicating if padding should be used when extracting code lines.
    - `code`: A string containing the full source code from which the symbol is extracted.
    - `reified_symbol`: An optional `ReifiedSymbol` instance associated with the symbol, used as a hack.
- **Control Flow**:
    - Initialize `file_code` to `None`.
    - Determine `start_line` and `end_line` based on `use_padding` and constants `BLIND_PADDING_TOP` and `BLIND_PADDING_BOTTOM`.
    - Extract the symbol's code (`s_code`) from the provided `code` string using the calculated line range.
    - If `is_large_file` or `is_overloaded` is true, split `s_code` into chunks using `split_text` and assign the first chunk's text to `symbol_code`; otherwise, assign `s_code` to `symbol_code` and `code` to `file_code`.
    - Create a `RawSymbolData` instance with the extracted and processed data.
    - Return the created `RawSymbolData` instance.
- **Output**:
    - Returns a `RawSymbolData` instance representing the symbol with its associated metadata and code.



---
### RawTreeSitterSymbolData 
- **Type**: `class`
- **Members**:
    - `name`: The name of the symbol, which can be None.
    - `start_line`: The starting line number of the symbol in the source file.
    - `end_line`: The ending line number of the symbol in the source file.
    - `start_byte`: The starting byte position of the symbol in the source file.
    - `end_byte`: The ending byte position of the symbol in the source file.
    - `file_path`: The file path where the symbol is located.
    - `symbol_kind`: The kind of symbol, represented by the SymbolKind enum.
    - `symbol_code`: The code associated with the symbol, which can be None.
- **Description**: The RawTreeSitterSymbolData class is a Pydantic model that represents raw symbol data extracted using Tree-sitter. It includes information about the symbol's name, location in terms of line and byte positions, the file path, the kind of symbol, and optionally the code associated with the symbol. The class is configured to be immutable, allowing it to be used as a hashable object.
- **Inherits From**:
    - BaseModel

**Nested Classes**
    - Config


---
### ReifiedSymbol 
- **Type**: `dataclass`
- **Members**:
    - `raw`: Holds raw symbol data from Tree-sitter.
    - `is_definition`: Indicates if the symbol is a definition.
    - `is_declaration`: Indicates if the symbol is a declaration.
    - `definition`: References the definition of the symbol, if any.
    - `usages`: Lists all usages of the symbol.
    - `calls`: Lists all calls made by the symbol.
    - `declarations`: Lists all declarations related to the symbol.
- **Description**: The `ReifiedSymbol` class is a data structure that extends the concept of a linked symbol by incorporating additional information about its usages, calls, and declarations. It is designed to work with raw symbol data obtained from Tree-sitter, and it provides a comprehensive view of a symbol's role within a codebase, including whether it is a definition or declaration, and its relationships with other symbols. This class is particularly useful for analyzing and understanding the structure and dependencies of code.


---
### ScopeRelation 
- **Type**: `class`
- **Members**:
    - `METHOD`: Represents a method relationship in the scope.
    - `NESTED_CLASS`: Represents a nested class relationship in the scope.
    - `NESTED_INTERFACE`: Represents a nested interface relationship in the scope.
    - `NESTED_DATA_STRUCTURE`: Represents a nested data structure relationship in the scope.
    - `FIELD`: Represents a field relationship in the scope.
    - `CLASS_METHOD`: Represents a class method relationship in the scope.
    - `INSTANCE_METHOD`: Represents an instance method relationship in the scope.
    - `MODULE_METHOD`: Represents a module method relationship in the scope.
    - `ATTRIBUTE`: Represents an attribute relationship in the scope.
    - `ENUMERATOR`: Represents an enumerator relationship in the scope.
- **Description**: The `ScopeRelation` class is an enumeration that defines various types of relationships between a child symbol and its parent scope, such as methods, nested classes, fields, and attributes. It is used to categorize and identify the role or type of a symbol within its parent context, providing a structured way to understand the hierarchy and organization of symbols in a codebase.
- **Inherits From**:
    - StrEnum


---
### SymbolKind 
- **Type**: `class`
- **Members**:
    - `VARIABLE`: Represents a variable symbol kind.
    - `CALLABLE`: Represents a callable symbol kind.
    - `CALLABLE_DECLARATION`: Represents a callable declaration symbol kind.
    - `CALL`: Represents a call symbol kind.
    - `DATA_STRUCTURE`: Represents a data structure symbol kind.
    - `DATA_STRUCTURE_INSTANCE`: Represents a data structure instance symbol kind.
    - `CLASS`: Represents a class symbol kind.
    - `INTERFACE`: Represents an interface symbol kind.
    - `MODULE`: Represents a module symbol kind.
    - `IMPORT`: Represents an import symbol kind.
- **Description**: The `SymbolKind` class is an enumeration that defines various types of symbols that can be identified in a codebase, such as variables, callables, classes, interfaces, modules, and imports. Each member of the enumeration represents a distinct kind of symbol, which can be used to categorize and manage different elements within a programming environment.
- **Inherits From**:
    - Enum


# Functions

---
### code_requires_multi_prompt 
The function `code_requires_multi_prompt` determines if a given code string needs to be split into multiple chunks based on predefined chunk size and overlap.
- **Inputs**:
    - `code`: A string representing the code that needs to be checked for chunking.
- **Control Flow**:
    - The function imports the `split_text` function from `shared.chunking.text_splitter`.
    - It calls `split_text` with the provided `code`, using constants `CHUNK_SIZE` and `CHUNK_OVERLAP` to determine how the code should be split into chunks.
    - The function checks the length of the resulting `code_chunks` list.
    - It returns `True` if the length of `code_chunks` is greater than 1, indicating that the code requires multiple prompts; otherwise, it returns `False`.
- **Output**:
    - A boolean value indicating whether the code needs to be split into multiple chunks (True) or not (False).


---
### create_raw_symbol_via_ctags 
The function `create_raw_symbol_via_ctags` generates a `RawSymbolData` object from a ctags symbol and associated metadata.
- **Inputs**:
    - `ctags_symbol`: A dictionary containing information about the symbol extracted by ctags, including its name, line number, and optionally its scope and end line.
    - `root_rel_path`: A `Path` object representing the root-relative path to the file containing the symbol.
    - `code`: A string containing the source code of the file where the symbol is located.
    - `symbol_kind`: An instance of `SymbolKind` enum indicating the type of symbol (e.g., VARIABLE, CALLABLE).
    - `scope_relation`: A string or `None` indicating the relationship of the symbol to its parent scope, such as 'methods'.
    - `delimiter`: A string or `None` used to split the scope information in the ctags symbol.
    - `is_multi_prompt`: A boolean indicating whether the file is large enough to require multiple prompts for processing.
    - `is_overloaded`: A boolean indicating whether the symbol is overloaded, defaulting to `False`.
    - `use_padding`: A boolean indicating whether to apply padding to the start and end lines of the symbol, defaulting to `False`.
- **Control Flow**:
    - Check if the ctags symbol has a 'scope' and split it using the delimiter to get the last part as the scope, otherwise set scope to None.
    - Create a `RawSymbolData` object with the provided and derived information, including setting the parser kind to `UCTAGS`.
    - Determine the start and end lines for the symbol code, applying padding if `use_padding` is True.
    - Extract the symbol code from the provided code string using the calculated start and end lines.
    - If `is_multi_prompt` or `is_overloaded` is True, split the symbol code into chunks and assign the first chunk to `symbol_code`, otherwise assign the entire symbol code.
    - Set the `file_code` to the entire code if neither `is_multi_prompt` nor `is_overloaded` is True.
    - Return the constructed `RawSymbolData` object.
- **Output**:
    - A `RawSymbolData` object containing detailed information about the symbol, including its name, kind, scope, code, and file path.


---
### create_raw_symbol_via_llm 
The function `create_raw_symbol_via_llm` creates a `RawSymbolData` object using the LLM parser kind with provided symbol details.
- **Inputs**:
    - `name`: A string representing the name of the symbol.
    - `path`: A `Path` object indicating the file path where the symbol is located.
    - `code`: A string containing the code associated with the symbol.
    - `symbol_kind`: An instance of `SymbolKind` enum representing the type of the symbol.
- **Control Flow**:
    - The function directly returns a `RawSymbolData` object initialized with the provided inputs and some default values.
    - The `parser_kind` is set to `ParserKind.LLM`.
    - The `scope`, `scope_relation`, `children`, `start_line`, `end_line`, `reference_code`, and `delimiter` are set to `None`.
    - The `symbol_code` and `file_code` are both set to the provided `code`.
- **Output**:
    - The function returns a `RawSymbolData` object initialized with the given parameters and default values for unspecified fields.


---
### default_ctags_analysis 
The `default_ctags_analysis` function analyzes code using ctags to extract symbols and returns a collection of these symbols if any are found.
- **Inputs**:
    - `collection_cls`: A class type that inherits from `RawSymbolCollection`, used to instantiate the output collection of symbols.
    - `code`: A string containing the source code to be analyzed.
    - `root_rel_path`: A `Path` object representing the root-relative path of the file being analyzed.
    - `symbol_kind`: An instance of `SymbolKind` indicating the type of symbols to be extracted.
    - `ctags_kinds`: A set of strings representing the kinds of symbols to be extracted by ctags.
    - `delimiter`: An optional string used to delimit scopes in the symbol extraction process.
    - `add_symbol_padding`: A boolean flag indicating whether to add padding around symbols when extracting code snippets.
- **Control Flow**:
    - Determine if the code requires multi-prompt processing by calling `code_requires_multi_prompt` with the `code` argument.
    - Extract symbols from the code using `extract_symbols_w_ctags`, passing `root_rel_path` and `code` as arguments.
    - Initialize an empty dictionary `raw_symbol_data` to store extracted symbols.
    - Iterate over each symbol in the extracted symbols list.
    - For each symbol, check if its kind is in the `ctags_kinds` set.
    - If the symbol's kind is valid, create a `RawSymbolData` object using `create_raw_symbol_via_ctags` and store it in `raw_symbol_data` with the symbol's name as the key.
    - If `raw_symbol_data` is empty, return `None`; otherwise, instantiate and return a `collection_cls` object with `raw_symbol_data` as its data.
- **Output**:
    - Returns an instance of `RawSymbolCollection` containing the extracted symbols, or `None` if no symbols are found.


---
### disambiguate_header 
The `disambiguate_header` function determines whether a given header file is written in C or C++ using a language model, with a fallback option in case of errors.
- **Inputs**:
    - `code`: A string containing the source code of the header file to be analyzed.
    - `fallback`: An instance of the `Lang` enum that specifies the default language to return if the language model fails to provide a valid response.
- **Control Flow**:
    - Initialize a ChatOpenAI instance with specific parameters for model, temperature, and timeout.
    - Define a system prompt that instructs the language model to determine if the header file is C or C++ based on the provided code.
    - Create a user prompt by embedding the header file's code into a predefined format.
    - Attempt to generate a response from the language model using the system and user prompts.
    - Convert the response to an integer and match it to return either `Lang.C` or `Lang.CPP`.
    - If the response is not 0 or 1, or if an error occurs during the process, return the fallback language.
- **Output**:
    - Returns a `Lang` enum value indicating whether the header file is C or C++, or the fallback language if an error occurs.


