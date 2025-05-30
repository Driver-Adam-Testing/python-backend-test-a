# Purpose
This Python file is designed to facilitate the extraction of various code symbols from C source files using the Tree-sitter parsing library. It defines a framework for creating abstract syntax trees (ASTs) and extracting specific code elements such as imports, function definitions, data structures, variables, and function calls. The core component is the `DriverTree` abstract base class, which outlines the structure for language-specific subclasses to implement methods for extracting these elements. The `CDriverTree` class is a concrete implementation for the C programming language, utilizing Tree-sitter's C language support to parse and analyze C code.

The file is structured as a library intended for use in other Python scripts or applications. It provides a public API through the `DriverTree` and `CDriverTree` classes, allowing users to parse C code and retrieve detailed information about its structure and components. The code leverages Python's `dataclass` for organizing symbol data and uses decorators to mark methods as symbol extractors. The file also includes utility functions for handling Tree-sitter nodes and extracting specific information, such as function names and parameters. Overall, this code provides a robust framework for analyzing C code, making it useful for tasks such as code analysis, refactoring, or documentation generation.
# Imports and Dependencies

---
- `abc`
- `collections.abc`
- `dataclasses`
- `inspect`
- `pathlib`
- `typing`
- `tree_sitter`
- `tree_sitter_c`
- `utils.lang_specialization.symbol_common`


# Global Variables

---
### LANGUAGES 
- **Type**: `dict`
- **Description**: The `LANGUAGES` variable is a dictionary that maps programming language identifiers to their corresponding Tree-sitter language objects. In this case, it contains a single entry for the C programming language, using the Tree-sitter C language module.
- **Use**: This variable is used to retrieve the Tree-sitter language object for a specified programming language, facilitating the parsing of source code in that language.


---
### code 
- **Type**: `str`
- **Description**: The `code` variable is a string that contains a C code snippet defining a typedef for a struct named `Point2` and a pointer to it named `Point2Ptr`. This struct has two integer fields, `x` and `y`. The code is used to test the functionality of the `CDriverTree` class in parsing and extracting data structure definitions from C code.
- **Use**: This variable is used as input to the `CDriverTree.from_code` method to create a syntax tree and extract data structure definitions.


---
### data_structures 
- **Type**: `list[RawTreeSitterSymbolData]`
- **Description**: The `data_structures` variable is a list that contains instances of `RawTreeSitterSymbolData`, which represent data structure definitions extracted from C code. These data structures can include structs, unions, and enums, along with their typedefs, if applicable.
- **Use**: This variable is used to store and print the extracted data structure definitions from the provided C code.


---
### driver_tree 
- **Type**: `CDriverTree`
- **Description**: The `driver_tree` variable is an instance of the `CDriverTree` class, which is a subclass of `DriverTree` specifically designed for parsing C code using the tree-sitter library. It is initialized with a C code snippet and a file path, and it constructs an abstract syntax tree (AST) from the provided code.
- **Use**: This variable is used to extract data structure definitions and other symbols from the C code by invoking methods on the `CDriverTree` instance.


---
### language 
- **Type**: `str`
- **Description**: The `language` variable is a class attribute of the `DriverTree` class and its subclasses, such as `CDriverTree`. It is intended to specify the programming language that the `DriverTree` instance is designed to parse and analyze using the tree-sitter library.
- **Use**: This variable is used to determine which language-specific tree-sitter parser to use when creating an abstract syntax tree (AST) from source code.


# Classes

---
### CDriverTree 
- **Type**: `class`
- **Members**:
    - `language`: Specifies the programming language as 'c'.
- **Description**: The `CDriverTree` class is a specialized subclass of `DriverTree` designed to parse and extract various elements from C source code using the Tree-sitter library. It provides methods to extract imports, function definitions, data structure definitions, variables, function calls, and function declarations from C code. Each extraction method is decorated with `symbol_extractor`, indicating its role in symbol extraction. The class uses Tree-sitter queries to identify and process specific code patterns, returning structured data about the code elements found.
- **Inherits From**:
    - DriverTree

**Methods**

---
#### CDriverTree.extract_data_structure_definitions
The function `extract_data_structure_definitions` extracts and returns a list of data structure definitions (structs, unions, enums) and their typedefs from a parsed syntax tree, excluding forward declarations.
- **Inputs**:
    - None
- **Control Flow**:
    - Define a query string to match struct, union, and enum definitions and typedefs using Tree-sitter syntax.
    - Execute the query on the root node of the syntax tree to find matches.
    - Iterate over each match and use pattern matching to identify the type of data structure (struct, union, enum) and whether it is a typedef or a direct declaration.
    - For each match, check if the data structure is a bare definition inside a type_definition or declaration using the `has_ancestor` helper function, and skip it if true.
    - Extract the name of the data structure from the captured nodes, if available.
    - Determine the line range and byte range of the data structure node.
    - Create a `RawTreeSitterSymbolData` object for each valid data structure, capturing its name, line range, byte range, and source code.
    - Append each `RawTreeSitterSymbolData` object to the results list.
    - Sort the results list by the start byte of each data structure.
    - Return the sorted list of `RawTreeSitterSymbolData` objects.
- **Output**:
    - A sorted list of `RawTreeSitterSymbolData` objects representing the extracted data structure definitions and typedefs.


---
#### CDriverTree.extract_function_calls
The `extract_function_calls` function identifies and extracts all function call expressions from a syntax tree, returning them as a sorted list of `RawTreeSitterSymbolData` objects.
- **Inputs**:
    - None
- **Control Flow**:
    - A query is created to find all call expressions in the syntax tree using Tree-sitter.
    - The query is executed against the root node of the tree to find matches.
    - For each match, the function checks if the call expression has a valid function name by looking for an identifier node.
    - If a valid function name is found, the function name is extracted and decoded from bytes to a string.
    - The line range and byte range of the call expression node are determined using the `get_node_line_range` method and node properties.
    - A `RawTreeSitterSymbolData` object is created for each valid function call, containing details such as the function name, line range, byte range, file path, and symbol code.
    - The function call data is appended to a list of function calls.
    - The list of function calls is sorted by the start byte of each call expression.
    - The sorted list of function calls is returned.
- **Output**:
    - A sorted list of `RawTreeSitterSymbolData` objects representing function calls, sorted by their start byte.


---
#### CDriverTree.extract_function_declarations
The `extract_function_declarations` function extracts all function declarations (excluding definitions) from C code using Tree-sitter.
- **Inputs**:
    - `self`: An instance of the `CDriverTree` class, which contains the Tree-sitter language and tree, source bytes, and file path.
- **Control Flow**:
    - A Tree-sitter query is created to match all declaration nodes in the syntax tree.
    - The query is executed against the root node of the syntax tree to find all matches.
    - For each match, the declaration node is extracted from the captures.
    - The function checks if the declaration node has a child node named 'declarator'. If not, it continues to the next match.
    - The function name and parameters are extracted using `get_function_name_and_params`. If no function name is found, it continues to the next match.
    - The function checks if the declaration node has a body by looking for a 'compound_statement' child. If a body is found, it continues to the next match.
    - The line range and byte range of the declaration node are determined using `get_node_line_range`.
    - A `RawTreeSitterSymbolData` object is created for each valid function declaration and added to the `declarations` list.
    - The list of declarations is sorted by the start byte of each declaration.
    - The sorted list of function declarations is returned.
- **Output**:
    - A sorted list of `RawTreeSitterSymbolData` objects representing function declarations in the C code.


---
#### CDriverTree.extract_function_definitions
The `extract_function_definitions` function extracts and returns a sorted list of function definitions from a syntax tree using Tree-sitter.
- **Inputs**:
    - `self`: An instance of a class that inherits from `DriverTree`, containing attributes like `tree_sitter_lang`, `tree`, `source_bytes`, and `file_path`.
- **Control Flow**:
    - A Tree-sitter query is created to find function definitions in the syntax tree.
    - The query is executed against the root node of the syntax tree to find matches.
    - For each match, the function definition node is captured and processed to extract the function name and parameters using `get_function_name_and_params`.
    - If the function name cannot be parsed, a message is printed, and the function name is set to `None`.
    - The line range and byte range of the function definition node are determined using `get_node_line_range` and the node's attributes.
    - A `RawTreeSitterSymbolData` object is created for each function definition, capturing its name, line range, byte range, file path, and code text.
    - The function data is appended to a list of functions.
    - The list of functions is sorted by their starting byte position.
    - The sorted list of function definitions is returned.
- **Output**:
    - A sorted list of `RawTreeSitterSymbolData` objects, each representing a function definition with details like name, line range, byte range, file path, and code text.


---
#### CDriverTree.extract_imports
The `extract_imports` function extracts and returns all `#include` directives from C code, capturing their paths and metadata.
- **Inputs**:
    - None
- **Control Flow**:
    - A query is defined to match `#include` directives with either `string_literal` or `system_lib_string` paths.
    - The query is executed against the root node of the syntax tree to find all matches.
    - For each match, the include directive and path nodes are extracted.
    - The path text is decoded from bytes and cleaned of surrounding characters (angle brackets or quotes) based on its type.
    - The line range of the include directive is determined using the `get_node_line_range` method.
    - A `RawTreeSitterSymbolData` object is created for each include, capturing its name, line range, byte range, file path, and code.
    - The list of includes is sorted by their starting byte position.
    - The sorted list of includes is returned.
- **Output**:
    - A sorted list of `RawTreeSitterSymbolData` objects representing the `#include` directives found in the C code.


---
#### CDriverTree.extract_variables
The `extract_variables` function identifies and returns a list of global variable declarations from a parsed syntax tree, filtering out non-global and function/type-related declarations.
- **Inputs**:
    - `self`: An instance of a class that contains the syntax tree and related metadata for parsing and extracting symbols from source code.
- **Control Flow**:
    - A query is executed on the syntax tree to find all nodes representing declarations, tagged as `global_var`.
    - The function `is_top_level_or_preprocessor_wrapped` checks if a node is at the top level or only wrapped by preprocessor directives, ensuring it is a global variable.
    - For each matched declaration node, the function checks if it is not a function or type definition by examining its children nodes.
    - If the declaration is valid, it searches for identifier nodes within the declaration to extract variable names.
    - For each valid identifier, a `RawTreeSitterSymbolData` object is created with details about the variable, including its name, line range, byte range, and source code snippet.
    - The list of variable data objects is sorted by their starting byte position before being returned.
- **Output**:
    - A sorted list of `RawTreeSitterSymbolData` objects, each representing a global variable declaration found in the syntax tree.



---
### DriverTree 
- **Type**: `dataclass`
- **Members**:
    - `tree_sitter_lang`: The language used by tree-sitter for parsing.
    - `tree`: The abstract syntax tree (AST) generated by tree-sitter.
    - `source_bytes`: The source code in bytes format.
    - `file_path`: The file path of the source code.
    - `language`: The programming language of the source code, default is an empty string.
- **Description**: The `DriverTree` class is an abstract base class designed to facilitate the creation and manipulation of abstract syntax trees (ASTs) using the tree-sitter library. It is intended for use with single methods, code files, or entire repositories, and requires subclasses to implement language-specific behaviors such as extracting imports, function definitions, data structures, function calls, and variables. The class provides a method to instantiate itself from a code string and file path, and includes utility methods for extracting line ranges of nodes and collecting all symbols extracted by subclass methods.
- **Inherits From**:
    - ABC

**Methods**

---
#### DriverTree.extract_all_symbols
The `extract_all_symbols` function collects and returns all symbols extracted by methods marked as symbol extractors within a class, sorted by their starting line number.
- **Inputs**:
    - None
- **Control Flow**:
    - Initialize an empty list `all_symbols` to store the collected symbols.
    - Iterate over all methods of the class instance using `getmembers` with `ismethod` predicate to filter methods.
    - For each method, check if it has the attribute `_is_symbol_extractor` set to `True`.
    - If the method is a symbol extractor, attempt to call it and extend `all_symbols` with its result.
    - Handle `NotImplementedError` exceptions by continuing to the next method without adding any symbols.
    - Sort the `all_symbols` list by the `start_line` attribute of each symbol.
    - Return the sorted list of symbols.
- **Output**:
    - A list of `RawTreeSitterSymbolData` objects, sorted by their `start_line` attribute.


---
#### DriverTree.extract_data_structure_definitions
The `extract_data_structure_definitions` function extracts and returns a list of data structure definitions such as structs, unions, and enums from a parsed C code tree, excluding forward declarations.
- **Inputs**:
    - None
- **Control Flow**:
    - The function defines a query string to match various data structure definitions and typedefs in C code, including structs, unions, and enums.
    - It executes the query against the root node of the parsed tree to find matches.
    - For each match, it checks if the data structure is a bare definition inside a type_definition or declaration and skips it if so.
    - It extracts the name and line range of each valid data structure definition.
    - It creates a `RawTreeSitterSymbolData` object for each data structure, capturing its name, line range, byte range, file path, and code snippet.
    - The results are sorted by their start byte and returned as a list.
- **Output**:
    - A list of `RawTreeSitterSymbolData` objects representing the data structure definitions found in the C code.


---
#### DriverTree.extract_function_calls
The `extract_function_calls` function identifies and returns a list of function call symbols from a parsed abstract syntax tree (AST) using Tree-sitter.
- **Inputs**:
    - None
- **Control Flow**:
    - The function uses a Tree-sitter query to find all nodes in the AST that represent function call expressions.
    - For each matched call expression node, it attempts to extract the function name by looking for an identifier node within the call expression.
    - If a valid function name is found, it creates a `RawTreeSitterSymbolData` object containing details about the function call, such as its name, line range, byte range, and file path.
    - The function collects all valid function call symbols into a list.
    - Finally, it sorts the list of function call symbols by their starting byte position and returns the sorted list.
- **Output**:
    - A sorted list of `RawTreeSitterSymbolData` objects representing function call symbols found in the AST.


---
#### DriverTree.extract_function_definitions
The `extract_function_definitions` function extracts and returns a list of function definitions from a parsed syntax tree using Tree-sitter.
- **Inputs**:
    - None
- **Control Flow**:
    - The function uses a Tree-sitter query to find all nodes in the syntax tree that match the pattern for function definitions.
    - It iterates over each match, extracting the function name and parameters using the `get_function_name_and_params` helper function.
    - For each function definition, it calculates the line range and byte range in the source code.
    - It creates a `RawTreeSitterSymbolData` object for each function, storing metadata such as the function name, line range, byte range, and source code snippet.
    - The function appends each `RawTreeSitterSymbolData` object to a list.
    - Finally, it sorts the list of function definitions by their starting byte position and returns it.
- **Output**:
    - A sorted list of `RawTreeSitterSymbolData` objects, each representing a function definition with metadata such as name, line range, byte range, and source code snippet.


---
#### DriverTree.extract_imports
The `extract_imports` function extracts all #include directives from C code using tree-sitter and returns them as a list of `RawTreeSitterSymbolData` objects.
- **Inputs**:
    - `self`: An instance of the `CDriverTree` class, which contains the tree-sitter language, tree, source bytes, file path, and language information.
- **Control Flow**:
    - The function defines a query to match preprocessor include directives in the C code, capturing both string literals and system library strings.
    - It executes the query against the root node of the tree-sitter parse tree to find all matches.
    - For each match, it extracts the include directive node and the include path node.
    - The include path text is extracted and cleaned by removing angle brackets or quotes, depending on the type of include path node.
    - The line range of the include directive node is determined using the `get_node_line_range` method.
    - A `RawTreeSitterSymbolData` object is created for each include directive, containing the include path, line range, byte range, file path, and symbol code.
    - The list of `RawTreeSitterSymbolData` objects is sorted by the start byte of each include directive.
    - The sorted list of include directives is returned.
- **Output**:
    - A sorted list of `RawTreeSitterSymbolData` objects, each representing an include directive found in the C code.


---
#### DriverTree.extract_variables
The `extract_variables` function extracts global variable declarations from a parsed C code tree using Tree-sitter.
- **Inputs**:
    - None
- **Control Flow**:
    - The function uses a Tree-sitter query to find all nodes in the syntax tree that match the pattern for global variable declarations.
    - It iterates over each match to determine if the node is a top-level declaration or wrapped by preprocessor directives, ensuring it is a global variable.
    - For each valid global variable declaration, it checks if the declaration is not a function or type definition.
    - It identifies the variable's name by finding the identifier node within the declaration node.
    - It creates a `RawTreeSitterSymbolData` object for each variable, capturing its name, line range, byte range, and other metadata.
    - The function returns a sorted list of `RawTreeSitterSymbolData` objects representing the global variables.
- **Output**:
    - A sorted list of `RawTreeSitterSymbolData` objects, each representing a global variable found in the C code.


---
#### DriverTree.from_code
The `from_code` function initializes a `DriverTree` subclass instance by parsing a given code string into an abstract syntax tree (AST) using the Tree-sitter library.
- **Inputs**:
    - `code_str`: A string containing the source code to be parsed into an abstract syntax tree.
    - `file_path`: A `Path` object or string representing the file path associated with the source code.
- **Control Flow**:
    - Check if the `language` attribute of the class is set; if not, raise a `DriverTreeError`.
    - Retrieve the Tree-sitter language object from the `LANGUAGES` dictionary using the class's `language` attribute.
    - Create a Tree-sitter parser for the specified language.
    - Convert the `code_str` to a UTF-8 encoded byte string.
    - Parse the byte string to generate a Tree-sitter syntax tree.
    - Return an instance of the class, initialized with the syntax tree, language object, source bytes, and file path.
- **Output**:
    - Returns an instance of the class (a subclass of `DriverTree`) initialized with the parsed syntax tree, Tree-sitter language, source bytes, and file path.


---
#### DriverTree.get_node_line_range
The `get_node_line_range` function calculates and returns the 1-based line range of a Tree-sitter node, adjusting for trailing newlines.
- **Inputs**:
    - `node`: A Tree-sitter Node object representing a syntax node in the source code.
- **Control Flow**:
    - Retrieve the starting line of the node by accessing `node.start_point.row` and convert it from 0-based to 1-based by adding 1.
    - Retrieve the ending line of the node by accessing `node.end_point.row` and convert it from 0-based to 1-based by adding 1.
    - Check if the last byte of the node's span in `self.source_bytes` is a newline character.
    - If the last byte is a newline, decrement the ending line by 1 to adjust for the newline.
    - Return a tuple containing the starting and ending lines.
- **Output**:
    - A tuple of two integers representing the 1-based starting and ending lines of the node in the source code.



---
### DriverTreeError 
- **Type**: `class`
- **Description**: The `DriverTreeError` class is a custom exception that inherits from the built-in `Exception` class. It is used to signal errors specific to the `DriverTree` operations, such as when a language is not specified for a `DriverTree` subclass. This class does not add any additional functionality or attributes beyond what is provided by the base `Exception` class.
- **Inherits From**:
    - Exception


# Functions

---
### find_identifier_node 
The `find_identifier_node` function recursively searches for and returns the first identifier node within a given tree-sitter node.
- **Inputs**:
    - `node`: A `tree_sitter.Node` object representing the root node from which the search for an identifier node begins.
- **Control Flow**:
    - Check if the current node's type is 'identifier'; if so, return the node.
    - Iterate over each child of the current node.
    - For each child, check if its type is 'identifier'; if so, return the child node.
    - If the child is not an identifier, recursively call `find_identifier_node` on the child.
    - If a recursive call returns a non-None result, return that result.
    - If no identifier node is found, return None.
- **Output**:
    - Returns a `tree_sitter.Node` object representing the first identifier node found, or `None` if no identifier node is present.


---
### get_function_name_and_params 
The function `get_function_name_and_params` extracts the function name and parameter node from a given function declarator node, handling various types of nested declarators.
- **Inputs**:
    - `declarator_node`: A `tree_sitter.Node` representing a function declarator from which the function name and parameters are to be extracted.
- **Control Flow**:
    - Check if the `declarator_node` is of type 'function_declarator'.
    - If it is, retrieve the child nodes for 'declarator' and 'parameters'.
    - If the 'declarator' node is an identifier, return its text as the function name and the parameters node.
    - If the 'declarator' node is not an identifier, recursively call `get_function_name_and_params` on the 'declarator' node to handle nested declarators.
    - If the `declarator_node` is of type 'pointer_declarator', 'parenthesized_declarator', or 'attributed_declarator', recursively call `get_function_name_and_params` on its 'declarator' child node.
    - Return `None, None` if the node type is unsupported or unhandled.
- **Output**:
    - A tuple containing the function name as a string (or `None` if not found) and the parameters node as a `tree_sitter.Node` (or `None` if not found).


---
### has_ancestor 
The `has_ancestor` function checks if a given node in a tree-sitter syntax tree has any ancestor node of specified types.
- **Inputs**:
    - `node`: A `tree_sitter.Node` object representing the node in the syntax tree for which the ancestor check is to be performed.
    - `types`: A set of strings representing the types of ancestor nodes to check for.
- **Control Flow**:
    - Initialize the `parent` variable with the parent of the given `node`.
    - Enter a while loop that continues as long as `parent` is not `None`.
    - Inside the loop, check if the type of the `parent` node is in the `types` set.
    - If a match is found, return `True`.
    - If no match is found, update `parent` to its own parent and continue the loop.
    - If the loop exits without finding a match, return `False`.
- **Output**:
    - A boolean value indicating whether the node has an ancestor of any of the specified types.


---
### is_top_level_or_preprocessor_wrapped 
The function checks if a given node is at the top level of a syntax tree or only has preprocessor nodes as ancestors before reaching the top level.
- **Inputs**:
    - `node`: A `tree_sitter.Node` object representing a node in a syntax tree.
- **Control Flow**:
    - Initialize `parent` as the parent of the input `node`.
    - Enter a loop that continues as long as `parent` is not `None`.
    - Check if `parent` is of type `translation_unit`; if so, return `True`.
    - If `parent` is not a preprocessor node (i.e., its type does not start with 'preproc_'), return `False`.
    - Update `parent` to its own parent and continue the loop.
    - If the loop exits without returning, return `False`.
- **Output**:
    - A boolean value indicating whether the node is at the top level or only has preprocessor nodes as ancestors before reaching the top level.


---
### node_to_text 
The `node_to_text` function decodes the text content of a tree-sitter node from bytes to a UTF-8 string.
- **Inputs**:
    - `node`: A `tree_sitter.Node` object representing a node in a syntax tree, whose text content is to be decoded.
- **Control Flow**:
    - The function accesses the `text` attribute of the `node`, which is in bytes.
    - It then decodes this byte string using UTF-8 encoding to convert it into a regular Python string.
- **Output**:
    - A string representing the decoded text content of the given tree-sitter node.


---
### symbol_extractor 
The `symbol_extractor` function is a decorator that marks a method as a symbol extractor by setting an attribute on it.
- **Inputs**:
    - `method`: A callable object (typically a method) that returns a list of `RawTreeSitterSymbolData`.
- **Control Flow**:
    - The function takes a single argument, `method`, which is expected to be a callable.
    - It sets an attribute `_is_symbol_extractor` to `True` on the `method` to mark it as a symbol extractor.
    - The function returns the `method` unchanged.
- **Output**:
    - The function returns the input `method` with an additional attribute `_is_symbol_extractor` set to `True`.


