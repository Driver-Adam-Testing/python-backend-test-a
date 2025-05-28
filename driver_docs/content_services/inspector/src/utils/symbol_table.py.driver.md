# Purpose
This Python script is designed to analyze C projects by parsing C source and header files to build a comprehensive index of symbols, including their definitions, declarations, and usages. The script is structured to perform several key tasks: it first discovers all C and header files within a specified project directory, then parses these files to extract symbol data using a Tree-sitter-based driver. The script constructs a containment map to understand the hierarchical relationships between symbols and identifies which symbols are definitions, declarations, or usages. It also resolves include paths to determine the visibility of symbols across different files, allowing it to link symbol usages to their definitions.

The script is organized into several classes and functions that encapsulate different stages of the analysis process. The `ParsedProject` class handles the initial parsing and symbol extraction, while `ParsedProjectWithVisibility` extends this by mapping file visibility based on include directives. The `LinkedProject` class links symbol usages to their definitions, and the `ReifiedProjectIndex` class finalizes the symbol graph by linking definitions to their usages and declarations. The `build_c_project_index` function orchestrates these steps, and the `main` function serves as the entry point, setting up the project path and initiating the indexing process. The script is designed to be run as a standalone tool, providing a detailed summary of the symbol relationships within a C project.
# Imports and Dependencies

---
- `collections`
- `concurrent.futures`
- `dataclasses`
- `pathlib`
- `typing`
- `utils.lang_specialization.symbol_common`
- `utils.treesitter_driver`


# Global Variables

---
### definition
- **Type**: ``function``
- **Description**: The `definition` function is a utility function used to determine if a given symbol is a definition. It checks the symbol kind against a set of predefined kinds that are considered definitions, such as `SymbolKind.CALLABLE` and `SymbolKind.DATA_STRUCTURE`. This function is part of a larger system for parsing and analyzing C project files.
- **Use**: This function is used to identify whether a symbol is a definition within the context of parsing and linking symbols in a C project.


# Classes

---
### LinkedProject
- **Type**: `dataclass`
- **Members**:
    - `linked_symbols`: A dictionary mapping file paths to lists of LinkedSymbol objects.
    - `visibility_map`: A dictionary mapping file paths to sets of file paths that are transitively visible from each file.
- **Description**: The `LinkedProject` class is a data structure that represents a collection of linked symbols across multiple files in a project, along with their visibility relationships. It provides a method to construct an instance from a `ParsedProjectWithVisibility`, linking symbol usages to their definitions across files that are transitively visible. This class is useful for understanding symbol dependencies and visibility in a codebase, particularly in projects with complex include and visibility relationships.

**Methods**

---
#### LinkedProject.from_parsed_project_with_visibility
The function `from_parsed_project_with_visibility` links symbol usages to their definitions across all files that are transitively visible in a project.
- **Inputs**:
    - `cls`: The class `LinkedProject` to which this method belongs, used to create an instance of the class.
    - `project_vis`: An instance of `ParsedProjectWithVisibility` containing symbol data and visibility information for a project.
- **Control Flow**:
    - Initialize dictionaries to collect definitions and declarations by symbol name.
    - Iterate over each file and its symbols in `project_vis` to populate the definitions and declarations dictionaries.
    - For each symbol name with exactly one definition, map all its declarations to this definition.
    - Iterate over each file and its symbols again to link each symbol to its definition if it is visible, using the visibility map.
    - For each symbol, determine if it is a definition, declaration, or usage, and attempt to link it to a definition if possible.
    - Store the linked symbols in a dictionary keyed by file path.
    - Return a new instance of `LinkedProject` with the linked symbols and visibility map.
- **Output**:
    - Returns an instance of `LinkedProject` containing a mapping of file paths to lists of `LinkedSymbol` objects, each representing a symbol with potential links to its definition.



---
### LinkedSymbol
- **Type**: `dataclass`
- **Members**:
    - `raw`: Holds the raw symbol data from RawTreeSitterSymbolData.
    - `is_definition`: Indicates if the symbol is a definition.
    - `is_declaration`: Indicates if the symbol is a declaration.
    - `definition`: Points to the definition of the symbol if it is a usage, otherwise None.
- **Description**: The LinkedSymbol class is a data structure that extends the RawTreeSitterSymbolData by adding metadata about whether the symbol is a definition or a declaration, and a reference to its definition if it is a usage. This class is used to facilitate the linking of symbols within a project, allowing for the identification of symbol definitions and their usages or declarations.


---
### ParsedProject
- **Type**: `dataclass`
- **Members**:
    - `file_to_symbols`: A dictionary mapping file paths to lists of raw TreeSitter symbol data.
    - `includes_map`: A dictionary mapping file paths to lists of include strings.
    - `file_to_containment_map`: A dictionary mapping file paths to containment maps of symbols.
- **Description**: The `ParsedProject` class is a data structure that holds parsed information about a C project, including symbols, includes, and containment relationships for each file. It provides a class method `from_files` to parse multiple files, either serially or in parallel, and populate the class attributes with the parsed data. This class is used as a foundational step in building a comprehensive index of a C project, facilitating further analysis and processing of the project's code structure.

**Methods**

---
#### ParsedProject.from_files
The `from_files` function parses a list of C files to extract symbols, includes, and containment maps, and returns a `ParsedProject` instance containing this data.
- **Inputs**:
    - `file_paths`: A list of `Path` objects representing the absolute paths to the C files to be parsed.
    - `project_root`: A `Path` object representing the root directory of the project, used to convert file paths to relative paths.
    - `num_workers`: An optional integer specifying the number of worker threads to use for parallel processing; if `None` or `1`, processing is done serially.
- **Control Flow**:
    - Define a nested function `parse_and_handle` to parse a single file and handle exceptions, returning the relative file path, symbols, includes, and containment map.
    - Initialize dictionaries `file_to_syms`, `raw_includes`, and `file_to_containment_map` to store parsed data.
    - Check if `num_workers` is `None` or `1` to decide between serial and parallel processing.
    - For serial processing, iterate over `file_paths`, parse each file using `parse_and_handle`, and store results in the dictionaries.
    - For parallel processing, use `ThreadPoolExecutor` to submit parsing tasks for each file, collect results as they complete, and store them in the dictionaries.
    - Return an instance of `ParsedProject` initialized with the collected data.
- **Output**:
    - Returns an instance of `ParsedProject` containing mappings of file paths to symbols, includes, and containment maps.



---
### ParsedProjectWithVisibility
- **Type**: `dataclass`
- **Members**:
    - `file_to_symbols`: A dictionary mapping file paths to lists of raw TreeSitter symbol data.
    - `includes_map`: A dictionary mapping file paths to lists of include strings.
    - `visibility_map`: A dictionary mapping file paths to sets of file paths that are transitively visible from each file.
- **Description**: The `ParsedProjectWithVisibility` class extends the `ParsedProject` class by adding a `visibility_map` that indicates which files are transitively visible from each file. This class is designed to handle the visibility of files in a project by constructing a map that shows all files a given file can 'see' through its includes. It provides a class method `from_parsed_project` to create an instance from a `ParsedProject`, utilizing either serial or parallel processing to compute the visibility map.

**Methods**

---
#### ParsedProjectWithVisibility.from_parsed_project
The `from_parsed_project` function constructs a visibility map for a project, indicating which files can be transitively 'seen' by each file, and returns an instance of `ParsedProjectWithVisibility`.
- **Inputs**:
    - `cls`: The class `ParsedProjectWithVisibility` to which the method belongs.
    - `parsed`: An instance of `ParsedProject` containing the project's file-to-symbols map and includes map.
    - `num_workers`: An optional integer specifying the number of worker threads for parallel processing; if `None` or `1`, processing is done serially.
- **Control Flow**:
    - Initialize `file_to_symbols`, `includes_map`, and `project_files` from the `parsed` object.
    - Define a `dfs` function to perform a depth-first search to find all files transitively visible from a given file.
    - Define a `compute_visited` function to initiate the DFS for a given file and return the set of visited files.
    - Check if `num_workers` is `None` or `1` to decide between serial and parallel processing.
    - In serial processing, iterate over each file path, compute its visibility using `compute_visited`, and update the `visibility_map`.
    - In parallel processing, use a `ThreadPoolExecutor` to compute visibility for each file concurrently, updating the `visibility_map` as futures complete.
    - Return an instance of `ParsedProjectWithVisibility` initialized with `file_to_symbols`, `includes_map`, and `visibility_map`.
- **Output**:
    - An instance of `ParsedProjectWithVisibility` containing the file-to-symbols map, includes map, and the computed visibility map.



---
### ReifiedProjectIndex
- **Type**: `dataclass`
- **Members**:
    - `file_to_symbols`: A dictionary mapping file paths to lists of reified symbols.
- **Description**: The `ReifiedProjectIndex` class represents a comprehensive mapping of files to their corresponding reified symbols, where each symbol is fully linked in both directions (definition to usage and vice versa). It provides methods to construct this mapping from a linked project and to retrieve definitions and usages of symbols. Additionally, it includes a method to print a summary of the symbols in specified files, highlighting definitions, declarations, usages, and function calls.

**Methods**

---
#### ReifiedProjectIndex.from_linked_project
The `from_linked_project` function constructs a `ReifiedProjectIndex` by transforming linked symbols into reified symbols with complete linkage information, including definitions, usages, declarations, and function calls.
- **Inputs**:
    - `cls`: The class type to instantiate, expected to be `ReifiedProjectIndex`.
    - `linked_proj`: An instance of `LinkedProject` containing linked symbols and their visibility map.
    - `file_to_containment_map`: A dictionary mapping file paths to containment maps, which map raw symbols to their child symbols.
- **Control Flow**:
    - Initialize a provisional map to store `ReifiedSymbol` instances for each `LinkedSymbol` in `linked_proj`.
    - Iterate over each `LinkedSymbol` to populate the provisional map with `ReifiedSymbol` instances, copying raw data and definition/declaration flags.
    - Build adjacency lists for definitions to their usages and declarations using the provisional map.
    - Create a final map of `ReifiedSymbol` instances, setting their definitions, usages, and declarations based on the adjacency lists.
    - For each function definition, gather calls from the containment map and update the final map with these calls.
    - Group the reified symbols by file path into a `file_map`.
    - Return a new instance of `ReifiedProjectIndex` initialized with the `file_map`.
- **Output**:
    - Returns an instance of `ReifiedProjectIndex` containing a mapping from file paths to lists of `ReifiedSymbol` instances, each fully linked with definitions, usages, declarations, and calls.


---
#### ReifiedProjectIndex.get_definition_of
The `get_definition_of` function retrieves the definition of a given `ReifiedSymbol` if it exists.
- **Inputs**:
    - `symbol`: A `ReifiedSymbol` object for which the definition is to be retrieved.
- **Control Flow**:
    - The function directly accesses the `definition` attribute of the `symbol` argument and returns it.
- **Output**:
    - The function returns a `ReifiedSymbol` object representing the definition of the input symbol, or `None` if no definition exists.


---
#### ReifiedProjectIndex.get_usages_of
The `get_usages_of` function retrieves a list of usage symbols for a given symbol if it is a definition.
- **Inputs**:
    - `symbol`: A `ReifiedSymbol` object representing a symbol in the code, which may be a definition or a usage.
- **Control Flow**:
    - Check if the provided symbol is a definition using the `is_definition` attribute.
    - If the symbol is not a definition, return an empty list.
    - If the symbol is a definition, return its `usages` attribute, which is a list of `ReifiedSymbol` objects representing the usages of this symbol.
- **Output**:
    - A list of `ReifiedSymbol` objects representing the usages of the given symbol if it is a definition, otherwise an empty list.


---
#### ReifiedProjectIndex.print_summary
The `print_summary` function prints a detailed summary of symbols found in specified files, including their definitions, declarations, usages, and calls.
- **Inputs**:
    - `files`: A list of `Path` objects representing file paths to summarize, or `None` to summarize all files in `self.file_to_symbols`.
- **Control Flow**:
    - Initialize ANSI color codes for terminal output.
    - Determine the target files to summarize based on the `files` argument or default to all files in `self.file_to_symbols`.
    - Iterate over each file path in the target list.
    - For each file, retrieve the list of reified symbols associated with it.
    - If no symbols are found for a file, print a warning message and continue to the next file.
    - For each symbol, print its name, line range, and file path.
    - If the symbol is a definition, print the number of usages and declarations, and list each declaration and usage with details.
    - If the symbol is a callable definition, list the functions it calls.
    - If the symbol is a declaration, print its associated definition if available.
    - If the symbol is a usage, print its associated definition if available.
- **Output**:
    - The function does not return any value; it outputs the summary directly to the console.



# Functions

---
### build_c_project_index
The `build_c_project_index` function orchestrates the process of parsing C project files, determining their visibility, linking symbols, and reifying the symbol graph to build a comprehensive project index.
- **Inputs**:
    - `file_paths`: A list of `Path` objects representing the file paths of the C project files to be indexed.
    - `project_root`: A `Path` object representing the root directory of the C project.
- **Control Flow**:
    - Prints a message indicating the start of parsing files.
    - Calls `ParsedProject.from_files` to parse the files and create a `ParsedProject` object.
    - Prints a message indicating the start of resolving includes and visibility.
    - Calls `ParsedProjectWithVisibility.from_parsed_project` to determine transitive visibility among the parsed files.
    - Prints a message indicating the start of linking symbols.
    - Calls `LinkedProject.from_parsed_project_with_visibility` to link symbol usages to their definitions.
    - Prints a message indicating the start of reifying the symbol graph.
    - Calls `ReifiedProjectIndex.from_linked_project` to create a reified project index from the linked project.
    - Prints a message indicating the completion of the index building process.
    - Returns the `ReifiedProjectIndex` object.
- **Output**:
    - Returns a `ReifiedProjectIndex` object that contains a fully linked and reified symbol graph of the C project.


---
### build_containment_map
The `build_containment_map` function creates a mapping of parent symbols to their child symbols based on byte range containment.
- **Inputs**:
    - `symbols`: A list of `RawTreeSitterSymbolData` objects representing symbols with byte range information.
- **Control Flow**:
    - Initialize an empty dictionary `child_map` using `defaultdict` to store lists of child symbols for each parent symbol.
    - Iterate over each symbol in the `symbols` list as a potential parent symbol.
    - For each parent symbol, iterate over each symbol in the `symbols` list as a potential child symbol.
    - Skip the iteration if the parent and child symbols are the same.
    - Check if the child symbol's byte range is fully contained within the parent symbol's byte range.
    - If the containment condition is met, append the child symbol to the list of children for the parent symbol in `child_map`.
    - Convert `child_map` to a regular dictionary and return it.
- **Output**:
    - A dictionary mapping each parent `RawTreeSitterSymbolData` to a list of child `RawTreeSitterSymbolData` that are fully contained within the parent's byte range.


---
### compute_visited
The `compute_visited` function performs a depth-first search (DFS) to determine all files that are transitively visible from a given file path.
- **Inputs**:
    - `fpath`: A `Path` object representing the file path from which to start the DFS and compute visibility.
- **Control Flow**:
    - Initialize a set `visited` with the input `fpath` to keep track of visited file paths.
    - Call the `dfs` function with `fpath` and `visited` to perform a depth-first search, adding all transitively visible files to `visited`.
    - Return the `visited` set containing all file paths that are transitively visible from the input `fpath`.
- **Output**:
    - A set of `Path` objects representing all files that are transitively visible from the input file path.


---
### dfs
The `dfs` function performs a depth-first search to explore and mark all files transitively included from a given file in a project.
- **Inputs**:
    - `current`: The current file path being explored in the depth-first search.
    - `visited`: A set of file paths that have already been visited during the search to avoid cycles and redundant processing.
- **Control Flow**:
    - Iterate over each include string associated with the current file from the `includes_map`.
    - For each include string, resolve it to a file path using `resolve_include_path`.
    - Check if the resolved include path is valid and not already visited.
    - If valid and not visited, add the include path to the visited set and recursively call `dfs` on it.
- **Output**:
    - The function does not return any value; it modifies the `visited` set in place to include all transitively included files from the starting file.


---
### discover_c_and_h_files
The function `discover_c_and_h_files` identifies and returns a list of all C and header files within a given project directory.
- **Inputs**:
    - `project_root`: A `Path` object representing the root directory of the project where the search for C and header files will be conducted.
- **Control Flow**:
    - The function uses the `rglob` method of the `Path` object to recursively search for all files in the `project_root` directory.
    - It filters the files to include only those with a `.c` or `.h` file extension, using a case-insensitive comparison of the file suffix.
    - Each matching file path is resolved to its absolute path using the `resolve` method.
- **Output**:
    - A list of `Path` objects, each representing the absolute path to a C or header file found within the specified project directory.


---
### is_declaration
The function `is_declaration` checks if a given symbol is a callable declaration.
- **Inputs**:
    - `sym`: An instance of `RawTreeSitterSymbolData` representing a symbol to be checked.
- **Control Flow**:
    - The function evaluates whether the `symbol_kind` attribute of the input `sym` is equal to `SymbolKind.CALLABLE_DECLARATION`.
- **Output**:
    - A boolean value indicating whether the symbol is a callable declaration.


---
### is_definition
The `is_definition` function determines if a given symbol is considered a 'definition' based on its kind.
- **Inputs**:
    - `sym`: An instance of `RawTreeSitterSymbolData` representing a symbol whose kind is to be checked.
- **Control Flow**:
    - The function checks if the `symbol_kind` attribute of the input `sym` is in a predefined set of kinds that are considered definitions.
    - The set includes `SymbolKind.CALLABLE` and `SymbolKind.DATA_STRUCTURE`.
- **Output**:
    - A boolean value indicating whether the symbol is considered a definition.


---
### main
The `main` function orchestrates the discovery and indexing of C and header files in a specified project directory, and then prints a summary of the indexed symbols.
- **Inputs**:
    - None
- **Control Flow**:
    - Set the `project_root` to a specific directory path where the C project is located.
    - Call `discover_c_and_h_files` with `project_root` to get a list of all C and header files in the project.
    - Call `build_c_project_index` with the discovered file paths and `project_root` to create an index of the project symbols.
    - Call `index.print_summary()` to print a summary of the indexed symbols.
- **Output**:
    - The function does not return any value; it performs its operations and outputs a summary of the indexed symbols to the console.


---
### parse_and_handle
The `parse_and_handle` function parses a C file to extract symbols, includes, and a containment map, handling any exceptions that occur during parsing.
- **Inputs**:
    - `abs_fpath`: A `Path` object representing the absolute file path of the C file to be parsed.
- **Control Flow**:
    - Convert the absolute file path to a root-relative path using `to_root_relative`.
    - Attempt to parse the C file using `parse_c_file`, which returns symbols, includes, and a containment map.
    - If parsing is successful, print a success message with the relative file path.
    - If an exception occurs during parsing, print a failure message with the exception details and set symbols, includes, and containment map to empty values.
    - Return a tuple containing the relative file path, symbols, includes, and containment map.
- **Output**:
    - A tuple containing the root-relative file path, a list of symbols, a list of includes, and a containment map (dictionary).


---
### parse_c_file
The `parse_c_file` function parses a C file to extract non-import symbols, include directives, and a containment map of symbols.
- **Inputs**:
    - `fpath`: A `Path` object representing the file path of the C file to be parsed.
    - `project_root`: A `Path` object representing the root directory of the project, used to determine the relative path of the file.
- **Control Flow**:
    - Read the content of the file specified by `fpath` using UTF-8 encoding.
    - Convert the file path to a project-root-relative path using the `to_root_relative` function.
    - Initialize a `CDriverTree` object using the file content and relative path.
    - Extract all symbols from the file using the `extract_all_symbols` method of the `CDriverTree` object.
    - Build a containment map of symbols using the `build_containment_map` function.
    - Iterate over all extracted symbols to separate them into include directives and non-import symbols based on their kind.
    - Return the non-import symbols, include directives, and the containment map as a tuple.
- **Output**:
    - A tuple containing three elements: a list of non-import `RawTreeSitterSymbolData` symbols, a list of include directive strings, and a dictionary mapping `RawTreeSitterSymbolData` symbols to lists of child symbols.


---
### resolve_include_path
The `resolve_include_path` function attempts to resolve the path of an include file relative to a given file within a set of project files.
- **Inputs**:
    - `current_file`: A `Path` object representing the current file from which the include path is being resolved.
    - `include_str`: A string representing the include path or filename to be resolved.
    - `project_files`: A set of `Path` objects representing all the files in the project.
- **Control Flow**:
    - The function first constructs a candidate path by appending `include_str` to the parent directory of `current_file` and resolves it to an absolute path.
    - It checks if this candidate path exists in `project_files`; if so, it returns this path.
    - If the candidate path is not found, the function searches for any paths in `project_files` that end with `include_str`.
    - If exactly one match is found, it returns that path.
    - If multiple matches are found, it returns the first match.
    - If no matches are found, it returns `None`.
- **Output**:
    - The function returns a `Path` object representing the resolved include path if found, or `None` if no suitable path is found.


---
### to_root_relative
The `to_root_relative` function converts an absolute file path to a path relative to a specified project root.
- **Inputs**:
    - `fpath`: A `Path` object representing the absolute file path to be converted.
    - `project_root`: A `Path` object representing the root directory of the project to which the file path should be made relative.
- **Control Flow**:
    - The function takes two `Path` objects as input: `fpath` and `project_root`.
    - It calculates the relative path of `fpath` with respect to `project_root` using the `relative_to` method.
    - It constructs a new `Path` object by joining the name of the `project_root` with the relative path calculated in the previous step.
    - The resulting `Path` object is returned.
- **Output**:
    - A `Path` object representing the file path relative to the project root, prefixed with the project root's name.


