import pathlib

import pytest

from .csharp_driver import CSharpDriverTree


@pytest.fixture(scope="module")
def class_test_code() -> str:
    file_path = (
        pathlib.Path(__file__).parent
        / "treesitter_testcases"
        / "csharp"
        / "test_classes.cs"
    )
    with open(file_path, encoding="utf-8") as f:
        return f.read()


@pytest.mark.parametrize(
    "expected_class_name, expected_line_range",
    [
        ("SimpleClass", (8, 38)),
    ],
)
def test_extract_classes(
    class_test_code: str, expected_class_name: str, expected_line_range: tuple[int, int]
) -> None:
    driver_tree = CSharpDriverTree.from_code(class_test_code, "does_not_matter.cs")
    klasses = driver_tree.extract_class_definitions()
    extracted = [(k.name, (k.start_line, k.end_line)) for k in klasses]

    assert (expected_class_name, expected_line_range) in extracted, (
        f"Expected class ({expected_class_name}, {expected_line_range}) "
        f"not found in extracted classes: {extracted}"
    )
