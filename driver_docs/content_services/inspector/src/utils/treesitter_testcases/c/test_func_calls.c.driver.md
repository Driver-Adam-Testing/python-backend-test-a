# Purpose
This C code snippet is a small function collection designed to demonstrate function calls as arguments and conditional compilation. The [`test_function_calls_as_args`](#test_function_calls_as_args) function showcases the use of function calls within other function arguments, specifically using `strlen` and `sizeof` within a call to `max`, and then printing a string's length using `printf`. The [`test_conditional_calls`](#test_conditional_calls) function, which is conditionally compiled only if the preprocessor directive `hi` is defined, illustrates a simple conditional logic flow where `is_valid` checks a condition, and based on the result, either `process` or `handle_error` is called. This code is likely part of a larger program intended for testing or educational purposes, demonstrating basic C programming concepts such as function calls, conditional compilation, and error handling.
# Functions

---
### test_function_calls_as_args <!-- {{#callable:test_function_calls_as_args}} -->
The function `test_function_calls_as_args` demonstrates the use of function calls as arguments in other function calls.
- **Inputs**:
    - None
- **Control Flow**:
    - The function initializes an integer variable `x` with the result of the `max` function, which takes the length of the string "test" and the size of an integer as arguments.
    - It then prints the length of the string "example" using the `printf` function, with `strlen("example")` providing the length.
- **Output**:
    - The function does not return any value as it is a `void` function.


---
### test_conditional_calls <!-- {{#callable:test_conditional_calls}} -->
The function `test_conditional_calls` checks if a condition is valid and processes it or handles an error accordingly.
- **Inputs**:
    - None
- **Control Flow**:
    - The function checks the result of `is_valid("test")`.
    - If `is_valid("test")` returns true, it calls the `process("test")` function.
    - If `is_valid("test")` returns false, it calls the `handle_error("invalid")` function.
- **Output**:
    - The function does not return any value; it performs actions based on the validity of a condition.


