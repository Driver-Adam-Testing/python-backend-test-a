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

    includes = driver_tree.extract_imports()

    expected_imports = [
        "stdio.h",
        "myheader.h",
        "../headers/another_header.h",
        "stdlib.h",
        "utils.h",
        "custom.h",  # From conditional #if branch
        "default.h",  # From #else branch
    ]

    assert len(includes) == len(
        expected_imports
    ), f"Expected {len(expected_imports)} imports, but found {len(includes)}."

    extracted_imports = [include.name for include in includes]
    assert (
        extracted_imports == expected_imports
    ), f"Expected {expected_imports}, but found {extracted_imports}."


def test_extract_import_line_numbers(imports_c_code: str) -> None:
    driver_tree = CDriverTree.from_code(imports_c_code)

    includes = driver_tree.extract_imports()

    expected_line_numbers = [
        (1, 1),  # <stdio.h>
        (2, 2),  # "myheader.h"
        (3, 3),  # "../headers/another_header.h"
        (4, 4),  # <stdlib.h>
        (5, 5),  # "utils.h"
        (7, 7),  # "custom.h"
        (9, 9),  # <default.h>
    ]

    extracted_line_numbers = [
        (include.start_line, include.end_line) for include in includes
    ]

    assert (
        extracted_line_numbers == expected_line_numbers
    ), f"Expected {expected_line_numbers}, but found {extracted_line_numbers}."


@pytest.fixture(scope="module")
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
        (None, (25, 28)),
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

    functions = driver_tree.extract_functions()

    extracted = [(f.name, (f.start_line, f.end_line)) for f in functions]

    assert (expected_function_name, expected_line_range) in extracted, (
        f"Expected function ({expected_function_name}, {expected_line_range}) "
        f"not found in extracted functions: {extracted}"
    )


@pytest.fixture(scope="module")
def enums_test_code() -> str:
    file_path = (
        pathlib.Path(__file__).parent / "treesitter_testcases" / "c" / "test_enums.c"
    )
    with open(file_path, encoding="utf-8") as f:
        return f.read()


@pytest.mark.parametrize(
    "expected_enum_name, expected_line_range",
    [
        ("Color", (4, 8)),
        ("Weekday", (11, 17)),
        ("MyAnonEnum", (20, 24)),
        (None, (28, 31)),  # Anonymous global enum
        ("Direction", (35, 40)),
        ("Kind", (43, 47)),
        pytest.param(
            "KindPtr",
            (43, 47),
            marks=pytest.mark.xfail(
                reason="Known issue: we don't capture typedefs that define multiple types"
            ),
        ),
    ],
)
def test_extract_enums(
    enums_test_code: str,
    expected_enum_name: str,
    expected_line_range: tuple[int, int],
) -> None:
    driver_tree = CDriverTree.from_code(enums_test_code)

    data_structs = driver_tree.extract_data_structures()

    extracted = [
        (data_struct.name, (data_struct.start_line, data_struct.end_line))
        for data_struct in data_structs
    ]

    assert (expected_enum_name, expected_line_range) in extracted, (
        f"Expected enum ({expected_enum_name}, {expected_line_range}) "
        f"not found in extracted enums: {extracted}"
    )


@pytest.fixture(scope="module")
def structs_test_code() -> str:
    file_path = (
        pathlib.Path(__file__).parent / "treesitter_testcases" / "c" / "test_structs.c"
    )
    with open(file_path, encoding="utf-8") as f:
        return f.read()


@pytest.mark.parametrize(
    "expected_struct_name, expected_line_range",
    [
        ("Named", (7, 10)),
        ("MyStruct", (19, 22)),
        ("MyAnonTypedef", (25, 27)),
        (None, (30, 33)),
        ("Outer", (36, 42)),
        ("Point", (45, 48)),
        ("Point2", (51, 55)),
        pytest.param(
            "Point2Ptr",
            (51, 55),
            marks=pytest.mark.xfail(
                reason="Known issue: we don't capture typedefs that define multiple types"
            ),
        ),
    ],
)
def test_extract_structs(
    structs_test_code: str,
    expected_struct_name: str,
    expected_line_range: tuple[int, int],
) -> None:
    driver_tree = CDriverTree.from_code(structs_test_code)

    data_structs = driver_tree.extract_data_structures()

    extracted = [
        (data_struct.name, (data_struct.start_line, data_struct.end_line))
        for data_struct in data_structs
    ]

    dupes = [item for item in extracted if extracted.count(item) > 1]
    assert not dupes, f"Found duplicate declarations: {dupes}"

    assert (expected_struct_name, expected_line_range) in extracted, (
        f"Expected struct ({expected_struct_name}, {expected_line_range}) "
        f"not found in extracted structs: {extracted}"
    )


@pytest.fixture(scope="module")
def unions_test_code() -> str:
    file_path = (
        pathlib.Path(__file__).parent / "treesitter_testcases" / "c" / "test_unions.c"
    )
    with open(file_path, encoding="utf-8") as f:
        return f.read()


@pytest.mark.parametrize(
    "expected_union_name, expected_line_range",
    [
        ("Named", (7, 10)),
        ("ForwardDecl", (13, 16)),
        ("MyUnion", (19, 22)),
        ("MyAnonUnion", (25, 28)),
        (None, (31, 34)),
        ("Outer", (40, 46)),
        ("Combined", (49, 52)),
        ("Point2", (54, 58)),
        pytest.param(
            "Point2Ptr",
            (54, 58),
            marks=pytest.mark.xfail(
                reason="Known issue: we don't capture typedefs that define multiple types"
            ),
        ),
    ],
)
def test_extract_unions(
    unions_test_code: str,
    expected_union_name: str,
    expected_line_range: tuple[int, int],
) -> None:
    driver_tree = CDriverTree.from_code(unions_test_code)

    data_structs = driver_tree.extract_data_structures()

    extracted = [
        (data_struct.name, (data_struct.start_line, data_struct.end_line))
        for data_struct in data_structs
    ]

    dupes = [item for item in extracted if extracted.count(item) > 1]
    assert not dupes, f"Found duplicate declarations: {dupes}"

    assert (expected_union_name, expected_line_range) in extracted, (
        f"Expected unions ({expected_union_name}, {expected_line_range}) "
        f"not found in extracted unions: {extracted}"
    )


@pytest.fixture(scope="module")
def globals_test_code() -> str:
    file_path = (
        pathlib.Path(__file__).parent / "treesitter_testcases" / "c" / "test_globals.c"
    )
    with open(file_path, encoding="utf-8") as f:
        return f.read()


@pytest.mark.parametrize(
    "expected_global_name, expected_line_range",
    [
        # This was very helpful for crafting the test cases!
        # https://github.com/tree-sitter/tree-sitter-c/blob/master/test/corpus/declarations.txt
        # Primitive types
        ("a", (2, 2)),
        ("b", (3, 3)),
        ("c", (4, 4)),
        ("d", (5, 5)),
        # Multiple declarations
        ("e", (8, 9)),
        ("f", (8, 9)),
        ("g", (8, 9)),
        ("h", (10, 10)),
        ("i", (10, 10)),
        # Storage class vars
        ("aa", (13, 13)),
        ("bb", (13, 13)),
        ("cc", (14, 14)),
        ("dd", (15, 15)),
        ("ee", (16, 16)),
        # Pointers
        ("ptr", (19, 19)),
        ("ptr2", (20, 20)),
        ("ptr3", (21, 21)),
        # Type qualifier variables
        ("q", (24, 24)),
        ("q2", (25, 25)),
        ("q3", (26, 26)),
        ("q4", (27, 27)),
        ("q5", (28, 28)),
        # Attribute variables
        ("ii", (31, 31)),
        ("jj", (32, 32)),
        # ("kk", (33, 33)),
        # Struct/union/enum variables
        ("bbb", (36, 36)),
        ("ddd", (37, 37)),
        ("ggg", (38, 38)),
        # Assembly register variable
        ("rd_", (41, 41)),
        # GNU attribute variable
        ("foo", (44, 44)),
        # Array
        ("extra_lbits", (48, 49)),
    ],
)
def test_extract_globals(
    globals_test_code: str,
    expected_global_name: str,
    expected_line_range: tuple[int, int],
) -> None:
    driver_tree = CDriverTree.from_code(globals_test_code)

    globals_found = driver_tree.extract_variables()

    extracted = [(g.name, (g.start_line, g.end_line)) for g in globals_found]

    dupes = [item for item in extracted if extracted.count(item) > 1]
    assert not dupes, f"Found duplicate declarations: {dupes}"

    assert (expected_global_name, expected_line_range) in extracted, (
        f"Expected globals ({expected_global_name}, {expected_line_range}) "
        f"not found in extracted globals: {extracted}"
    )
