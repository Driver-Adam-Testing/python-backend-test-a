import pathlib

import pytest

from utils.treesitter import CDriverTree


@pytest.fixture
def imports_c_code() -> str:
    return """#include <stdio.h>
#include "myheader.h"
#include "../headers/another_header.h"
#include    <stdlib.h>
#  include "utils.h"
#if defined(USE_CUSTOM_HEADER)
    #include "custom.h"
#else
    #include <default.h>
#endif

int main(void) { return 1; }
"""


def test_extract_import_texts(imports_c_code: str) -> None:
    driver_tree = CDriverTree.from_code(imports_c_code)

    imports = driver_tree.extract_imports()

    expected_imports = [
        "stdio.h",
        "myheader.h",
        "../headers/another_header.h",
        "stdlib.h",
        "utils.h",
        "custom.h",  # From conditional #if branch
        "default.h",  # From #else branch
    ]

    assert len(imports) == len(
        expected_imports
    ), f"Expected {len(expected_imports)} imports, but found {len(imports)}."

    # Check the import texts
    extracted_imports = [include_text for _, include_text in imports]
    assert (
        extracted_imports == expected_imports
    ), f"Expected {expected_imports}, but found {extracted_imports}."


def test_extract_import_line_numbers(imports_c_code: str) -> None:
    driver_tree = CDriverTree.from_code(imports_c_code)

    # Extract imports
    imports = driver_tree.extract_imports()

    # Expected start and end line numbers
    expected_line_numbers = [
        (1, 1),  # <stdio.h>
        (2, 2),  # "myheader.h"
        (3, 3),  # "../headers/another_header.h"
        (4, 4),  # <stdlib.h>
        (5, 5),  # "utils.h"
        (7, 7),  # "custom.h"
        (9, 9),  # <default.h>
    ]

    # Verify the line numbers
    extracted_line_numbers = [
        driver_tree.get_node_line_range(node) for node, _ in imports
    ]

    assert (
        extracted_line_numbers == expected_line_numbers
    ), f"Expected {expected_line_numbers}, but found {extracted_line_numbers}."


@pytest.fixture
def functions_test_code() -> str:
    file_path = (
        pathlib.Path(__file__).parent / "treesitter_testcases" / "c" / "test_funcs.c"
    )
    with open(file_path, encoding="utf-8") as f:
        return f.read()


@pytest.mark.parametrize(
    "expected_function_name, expected_line_range",
    [
        ("foo", (4, 6)),
        ("bar", (8, 10)),
        ("baz", (12, 15)),
        ("qux", (17, 19)),
        ("wibble", (21, 23)),
        # ("myFunc", (25, 28)),
        ("<could_not_parse_name>", (25, 28)),  # TODO handle better!
        ("arrayParam", (30, 32)),
        ("roPointerFunc", (34, 37)),
        ("triplePtrFunc", (39, 42)),
        ("returnStruct", (49, 54)),
        ("main", (56, 96)),
    ],
)
def test_extract_function_properties(
    functions_test_code: str,
    expected_function_name: str,
    expected_line_range: tuple[int, int],
) -> None:
    driver_tree = CDriverTree.from_code(functions_test_code)

    # Extract functions
    functions = driver_tree.extract_functions()

    # Find the function by name
    function_nodes = {func_name: node for node, func_name in functions}
    assert (
        expected_function_name in function_nodes
    ), f"Function {expected_function_name} not found."

    # Verify line range
    func_node = function_nodes[expected_function_name]
    start_line, end_line = driver_tree.get_node_line_range(func_node)
    assert (start_line, end_line) == expected_line_range, (
        f"Function {expected_function_name} expected range {expected_line_range}, "
        f"but got ({start_line}, {end_line})."
    )
