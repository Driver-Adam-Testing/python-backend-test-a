# Purpose
This Python script is a comprehensive test suite using the `pytest` framework to validate the functionality of a C code parsing utility, specifically the `CDriverTree` class from the `utils.treesitter_driver` module. The script defines multiple test cases to ensure the correct extraction of various C language constructs such as imports, function definitions, enums, structs, unions, global variables, function calls, and function declarations from C source code. Each test case uses fixtures to load C code samples and employs assertions to compare the extracted data against expected results, ensuring the parser's accuracy. The script provides narrow functionality focused on testing the parsing capabilities of C code, and it includes parameterized tests to cover a wide range of scenarios, including handling conditional imports and known issues with typedefs.
# Imports and Dependencies

---
- `pathlib`
- `pytest`
- `utils.treesitter_driver.CDriverTree`


# Classes

---
### TestDelcarations 
- **Type**: `class`
- **Members**:
    - `test_extract_function_declarations`: Tests extraction of function declarations from code using parameterized inputs.
    - `test_declarations_not_definitions`: Ensures that function definitions are not mistakenly included as declarations.
    - `test_non_function_declarations_excluded`: Verifies that non-function declarations, such as variables and typedefs, are excluded from function declarations.
- **Description**: The `TestDelcarations` class is designed to test the functionality of extracting function declarations from C code using the `CDriverTree` utility. It includes methods to ensure that only function declarations are extracted, excluding function definitions and non-function declarations. The class uses parameterized tests to validate the extraction process against expected function names and line ranges.

**Methods**

---
#### TestDelcarations.test_declarations_not_definitions
The function `test_declarations_not_definitions` verifies that function definitions are not mistakenly included in the list of function declarations extracted from C code.
- **Inputs**:
    - `self`: Represents the instance of the class `TestDelcarations` to which this method belongs.
    - `function_declaration_test_code`: A string containing C code that is used to test the extraction of function declarations.
- **Control Flow**:
    - The function begins by creating a `CDriverTree` object using the provided C code string and a placeholder filename.
    - It then extracts function declarations from the `CDriverTree` object using the `extract_function_declarations` method.
    - The function collects the names of the extracted declarations into a list called `function_names`.
    - An assertion checks that the string 'some_function' is not present in the `function_names` list, ensuring that function definitions are not included in the declarations.
- **Output**:
    - The function does not return any value; it raises an assertion error if a function definition is found among the declarations.


---
#### TestDelcarations.test_extract_function_declarations
The `test_extract_function_declarations` function verifies that function declarations are correctly extracted from C code using the `CDriverTree` class.
- **Inputs**:
    - `self`: A reference to the instance of the class `TestDelcarations`.
    - `function_declaration_test_code`: A string containing C code to be tested for function declarations.
    - `expected_function_name`: The name of the function expected to be found in the declarations.
    - `expected_line_range`: A tuple representing the expected start and end line numbers of the function declaration.
- **Control Flow**:
    - Create a `CDriverTree` object from the provided C code using `CDriverTree.from_code` method.
    - Extract function declarations from the `CDriverTree` object using `extract_function_declarations` method.
    - Create a list of tuples containing function names and their line ranges from the extracted declarations.
    - Check for duplicate declarations in the extracted list and assert that there are none.
    - Assert that the expected function name and line range tuple is present in the extracted declarations.
- **Output**:
    - The function does not return any value; it uses assertions to validate the correctness of function declarations extracted from the C code.


---
#### TestDelcarations.test_non_function_declarations_excluded
The function `test_non_function_declarations_excluded` verifies that non-function declarations such as variables and typedefs are not mistakenly included in the list of function declarations extracted from C code.
- **Inputs**:
    - `self`: Represents the instance of the class `TestDelcarations` to which this method belongs.
    - `function_declaration_test_code`: A string containing C code that is used to test the extraction of function declarations.
- **Control Flow**:
    - The function begins by creating a `CDriverTree` object using the `from_code` method, passing in the `function_declaration_test_code` and a placeholder filename.
    - It then calls `extract_function_declarations` on the `driver_tree` object to retrieve a list of function declarations from the provided C code.
    - The function iterates over the extracted declarations to compile a list of function names.
    - It asserts that the name 'not_a_function' is not present in the list of function names, indicating that variable declarations are excluded.
    - It asserts that the name 'signal_handler_t' is not present in the list of function names, indicating that typedefs are excluded.
- **Output**:
    - The function does not return any value; it raises an assertion error if non-function declarations are found in the extracted function declarations.



# Functions

---
### enums_test_code 
The `enums_test_code` function reads and returns the content of a specific C test file for enums.
- **Inputs**:
    - None
- **Control Flow**:
    - Constructs the file path to the 'test_enums.c' file located in the 'treesitter_testcases/c' directory relative to the current file.
    - Opens the file at the constructed path with UTF-8 encoding.
    - Reads the entire content of the file and returns it.
- **Output**:
    - A string containing the content of the 'test_enums.c' file.


---
### function_call_test_code 
The `function_call_test_code` function reads and returns the content of a specific C test file for function calls.
- **Inputs**:
    - None
- **Control Flow**:
    - Constructs a file path to the 'test_func_calls.c' file located in the 'treesitter_testcases/c' directory relative to the current file.
    - Opens the file at the constructed path with UTF-8 encoding.
    - Reads the entire content of the file.
    - Returns the read content as a string.
- **Output**:
    - A string containing the content of the 'test_func_calls.c' file.


---
### function_declaration_test_code 
The `function_declaration_test_code` function reads and returns the content of a specific C test file for function declarations.
- **Inputs**:
    - None
- **Control Flow**:
    - Constructs the file path to the 'test_func_declarations.c' file located in the 'treesitter_testcases/c' directory relative to the current file.
    - Opens the file at the constructed path with UTF-8 encoding.
    - Reads the entire content of the file and returns it as a string.
- **Output**:
    - A string containing the content of the 'test_func_declarations.c' file.


---
### functions_test_code 
The `functions_test_code` function reads and returns the content of a specific C test file as a string.
- **Inputs**:
    - None
- **Control Flow**:
    - Constructs a file path by navigating to the 'treesitter_testcases/c/test_func_defs.c' file relative to the current file's directory.
    - Opens the file at the constructed path with UTF-8 encoding.
    - Reads the entire content of the file.
    - Returns the read content as a string.
- **Output**:
    - A string containing the entire content of the 'test_func_defs.c' file.


---
### globals_test_code 
The `globals_test_code` function reads and returns the content of a specific C test file for global variables.
- **Inputs**:
    - None
- **Control Flow**:
    - Constructs the file path to 'test_globals.c' located in the 'treesitter_testcases/c' directory relative to the current file.
    - Opens the file at the constructed path with UTF-8 encoding.
    - Reads the entire content of the file and returns it as a string.
- **Output**:
    - A string containing the content of the 'test_globals.c' file.


---
### imports_c_code 
The `imports_c_code` function returns a string containing C code with various include directives and a simple main function.
- **Inputs**:
    - None
- **Control Flow**:
    - The function is defined as a pytest fixture, which means it is used to provide a fixed baseline for tests.
    - It returns a multi-line string that includes several C include directives, both standard and custom headers.
    - The string also contains a conditional preprocessor directive to include either 'custom.h' or 'default.h' based on the 'USE_CUSTOM_HEADER' definition.
    - Finally, the string includes a simple 'main' function definition that returns 1.
- **Output**:
    - A string containing C code with include directives and a main function.


---
### structs_test_code 
The `structs_test_code` function reads and returns the content of a C test file for structs from a specific directory.
- **Inputs**:
    - None
- **Control Flow**:
    - Constructs the file path to 'test_structs.c' located in the 'treesitter_testcases/c' directory relative to the current file.
    - Opens the file at the constructed path with UTF-8 encoding.
    - Reads the entire content of the file and returns it as a string.
- **Output**:
    - A string containing the content of the 'test_structs.c' file.


---
### test_extract_enums 
The function `test_extract_enums` verifies that a specific enum definition is correctly extracted from C code using the `CDriverTree` class.
- **Inputs**:
    - `enums_test_code`: A string containing C code that includes enum definitions to be tested.
    - `expected_enum_name`: The name of the enum expected to be found in the C code, or None for anonymous enums.
    - `expected_line_range`: A tuple of two integers representing the expected start and end line numbers of the enum definition in the C code.
- **Control Flow**:
    - Create a `CDriverTree` object from the provided C code string using `CDriverTree.from_code` method.
    - Extract data structure definitions from the `CDriverTree` object using `extract_data_structure_definitions` method.
    - Create a list of tuples containing the name and line range of each extracted data structure.
    - Assert that the expected enum name and line range tuple is present in the list of extracted data structures.
    - If the assertion fails, raise an error with a message indicating the expected and actual extracted enums.
- **Output**:
    - The function does not return any value; it raises an assertion error if the expected enum is not found in the extracted data structures.


---
### test_extract_function_calls 
The function `test_extract_function_calls` verifies that a specific function call is correctly extracted from C code using the `CDriverTree` class.
- **Inputs**:
    - `function_call_test_code`: A string containing C code from which function calls are to be extracted.
    - `expected_function_call_name`: The name of the function call expected to be found in the extracted data.
    - `expected_line_range`: A tuple of two integers representing the expected start and end line numbers of the function call in the code.
- **Control Flow**:
    - Create a `CDriverTree` object from the provided C code string using `CDriverTree.from_code` method.
    - Extract function calls from the `CDriverTree` object using `extract_function_calls` method.
    - Create a list of tuples containing the name and line range of each extracted function call.
    - Check for duplicate function calls in the extracted list and assert that there are none.
    - Assert that the expected function call name and line range are present in the extracted list, raising an error if not.
- **Output**:
    - The function does not return any value; it raises an assertion error if the expected function call is not found or if duplicates are detected.


---
### test_extract_function_defs 
The function `test_extract_function_defs` verifies that a specific function definition is correctly extracted from C code using the `CDriverTree` class.
- **Inputs**:
    - `functions_test_code`: A string containing C code from which function definitions are to be extracted.
    - `expected_function_name`: The name of the function expected to be found in the extracted definitions.
    - `expected_line_range`: A tuple of two integers representing the expected start and end line numbers of the function definition in the code.
- **Control Flow**:
    - Create a `CDriverTree` object using the provided C code string and a placeholder filename.
    - Extract function definitions from the `CDriverTree` object using the `extract_function_definitions` method.
    - Create a list of tuples containing the name and line range of each extracted function.
    - Assert that the expected function name and line range tuple is present in the list of extracted functions, raising an error with a descriptive message if not.
- **Output**:
    - The function does not return any value; it raises an assertion error if the expected function definition is not found.


---
### test_extract_globals 
The function `test_extract_globals` verifies that global variables are correctly extracted from C code and checks for duplicates and expected globals.
- **Inputs**:
    - `globals_test_code`: A string containing C code from which global variables are to be extracted.
    - `expected_global_name`: The name of the global variable expected to be found in the extracted list.
    - `expected_line_range`: A tuple representing the expected start and end line numbers of the global variable in the code.
- **Control Flow**:
    - The function begins by creating a `CDriverTree` object from the provided C code string using `CDriverTree.from_code` method.
    - It then extracts global variables from the code using the `extract_variables` method of the `CDriverTree` object.
    - The extracted global variables are stored in a list of tuples, each containing the variable's name and its line range.
    - The function iterates over the extracted globals to assert that none of them are named 'localVar'.
    - It checks for duplicate global variable declarations by counting occurrences in the extracted list and asserts that there are no duplicates.
    - Finally, it asserts that the expected global variable (name and line range) is present in the extracted list, raising an error if not found.
- **Output**:
    - The function does not return any value; it raises assertions if the conditions are not met.


---
### test_extract_import_line_numbers 
The function `test_extract_import_line_numbers` verifies that the line numbers of import statements extracted from C code match expected values.
- **Inputs**:
    - `imports_c_code`: A string containing C code with import statements to be tested.
- **Control Flow**:
    - Create a `CDriverTree` object from the provided C code string using `CDriverTree.from_code`.
    - Extract import statements from the `CDriverTree` object using `extract_imports`.
    - Define a list of expected line numbers for the import statements.
    - Extract the start and end line numbers from the extracted import statements.
    - Assert that the extracted line numbers match the expected line numbers, raising an error if they do not.
- **Output**:
    - The function does not return any value; it raises an assertion error if the extracted line numbers do not match the expected line numbers.


---
### test_extract_import_texts 
The function `test_extract_import_texts` verifies that the `extract_imports` method of `CDriverTree` correctly identifies and extracts all import statements from a given C code string.
- **Inputs**:
    - `imports_c_code`: A string containing C code with various import statements, including conditional imports.
- **Control Flow**:
    - Create a `CDriverTree` object using the `from_code` method with the provided C code string and a placeholder filename.
    - Call the `extract_imports` method on the `CDriverTree` object to retrieve a list of import statements.
    - Define a list of expected import statements, including those from conditional branches.
    - Assert that the number of extracted imports matches the number of expected imports, raising an error if they do not match.
    - Extract the names of the imports from the `includes` list and assert that they match the expected import names, raising an error if they do not match.
- **Output**:
    - The function does not return any value; it raises an assertion error if the extracted imports do not match the expected imports.


---
### test_extract_structs 
The function `test_extract_structs` verifies that a specific struct definition is correctly extracted from C code using the `CDriverTree` class.
- **Inputs**:
    - `structs_test_code`: A string containing C code that includes struct definitions to be tested.
    - `expected_struct_name`: The name of the struct that is expected to be found in the extracted data structures.
    - `expected_line_range`: A tuple of two integers representing the expected start and end line numbers of the struct definition in the C code.
- **Control Flow**:
    - Create a `CDriverTree` object from the provided C code string `structs_test_code`.
    - Extract data structure definitions from the `CDriverTree` object using the `extract_data_structure_definitions` method.
    - Create a list of tuples `extracted`, each containing the name and line range of a data structure.
    - Check for duplicate entries in the `extracted` list and assert that there are none.
    - Assert that the tuple `(expected_struct_name, expected_line_range)` is present in the `extracted` list, raising an error if it is not.
- **Output**:
    - The function does not return any value; it raises an assertion error if the expected struct is not found or if there are duplicate struct definitions.


---
### test_extract_unions 
The function `test_extract_unions` verifies that a specific union definition is correctly extracted from C code and checks for duplicate declarations.
- **Inputs**:
    - `unions_test_code`: A string containing C code that includes union definitions to be tested.
    - `expected_union_name`: The name of the union expected to be found in the extracted data structures.
    - `expected_line_range`: A tuple of two integers representing the expected start and end line numbers of the union definition in the C code.
- **Control Flow**:
    - Create a `CDriverTree` object from the provided C code string using `CDriverTree.from_code` method.
    - Extract data structure definitions from the `CDriverTree` object using `extract_data_structure_definitions` method.
    - Create a list of tuples containing the name and line range of each extracted data structure.
    - Check for duplicate entries in the extracted list and assert that there are none.
    - Assert that the expected union name and line range tuple is present in the extracted list, raising an error if not.
- **Output**:
    - The function does not return any value; it raises an assertion error if the expected union is not found or if duplicates are detected.


---
### unions_test_code 
The `unions_test_code` function reads and returns the content of a C test file for unions from a specific directory.
- **Inputs**:
    - None
- **Control Flow**:
    - Constructs the file path to 'test_unions.c' located in the 'treesitter_testcases/c' directory relative to the current file's directory.
    - Opens the file at the constructed path with UTF-8 encoding.
    - Reads the entire content of the file.
    - Returns the read content as a string.
- **Output**:
    - A string containing the content of the 'test_unions.c' file.


