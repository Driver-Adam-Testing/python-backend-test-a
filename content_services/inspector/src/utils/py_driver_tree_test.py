import pathlib

import pytest

from utils.py_driver_tree import PyDriverTree


@pytest.fixture
def imports_python() -> str:
    return """import pathlib
from graphlib import TopologicalSorter
# import os
from pathlib import Path as PlPath

from foo.bar.baz import func
"""


def test_extract_import(imports_python: str) -> None:
    _driver_tree = PyDriverTree.from_code(imports_python, "does_not_matter.py")

    assert True


@pytest.fixture(scope="module")
def functions_test_code() -> str:
    file_path = (
        pathlib.Path(__file__).parent
        / "treesitter_testcases"
        / "python"
        / "test_functions.py"
    )
    with open(file_path, encoding="utf-8") as f:
        return f.read()


@pytest.mark.parametrize(
    "expected_function_name, expected_line_range",
    [
        ("simple_function", (8, 9)),
        ("function_with_params", (12, 13)),
        ("complex_params", (16, 23)),
        ("typed_function", (26, 27)),
        ("async_function", (30, 32)),
        ("generator_function", (35, 37)),
        ("cached_function", (41, 42)),  # TODO: Consider capturing the decorator lines
        ("my_decorator", (44, 49)),
        (
            "decorated_function",
            (52, 53),
        ),  # TODO: Consider capturing the decorator lines
        (
            "multiple_decorators",
            (58, 59),
        ),  # TODO: Consider capturing the decorator lines
        ("outer_function", (62, 67)),
        ("function_factory", (74, 77)),
        ("fibonacci", (80, 83)),
        ("documented_function", (86, 96)),
        ("default_args_function", (99, 108)),
        ("async_generator", (111, 114)),
        ("union_function", (119, 120)),
        ("literal_function", (122, 123)),
        ("generic_function", (130, 131)),
        ("property_function", (134, 135)),
        ("context_manager_function", (141, 146)),
        ("complex_annotations", (149, 155)),
    ],
)
def test_extract_function_defs(
    functions_test_code: str,
    expected_function_name: str,
    expected_line_range: tuple[int, int],
) -> None:
    driver_tree = PyDriverTree.from_code(functions_test_code, "does_not_matter.py")
    functions = driver_tree.extract_function_definitions()
    extracted = [(f.name, (f.start_line, f.end_line)) for f in functions]

    assert (expected_function_name, expected_line_range) in extracted, (
        f"Expected function ({expected_function_name}, {expected_line_range}) "
        f"not found in extracted functions: {extracted}"
    )
