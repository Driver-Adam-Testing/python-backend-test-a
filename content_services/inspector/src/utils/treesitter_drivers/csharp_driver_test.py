import pathlib

import pytest

from .csharp_driver import CSharpDriverTree


@pytest.fixture(scope="module")
def import_test_code() -> str:
    file_path = (
        pathlib.Path(__file__).parent
        / "treesitter_testcases"
        / "csharp"
        / "test_usings.cs"
    )
    with open(file_path, encoding="utf-8") as f:
        return f.read()


def test_extract_imports_no_false_positives(import_test_code: str) -> None:
    driver_tree = CSharpDriverTree.from_code(import_test_code, "does_not_matter.cs")
    klasses = driver_tree.extract_imports()
    assert len(klasses) == 12


@pytest.mark.parametrize(
    "expected_import_name, expected_line_range",
    [
        ("System", (2, 2)),
        ("System.Collections.Generic", (3, 3)),
        ("System.Linq", (4, 4)),
        ("System.Collections.Generic.Dictionary<string, object>", (7, 7)),
        ("System.Text.StringBuilder", (8, 8)),
        ("System", (9, 9)),
        ("System.Math", (12, 12)),
        ("System.Console", (13, 13)),
        ("System.Threading.Tasks", (16, 16)),
        ("System.Collections.Concurrent.ConcurrentDictionary<string, int>", (19, 19)),
        ("global::System.Text.Json", (22, 22)),
        ("global::System.Text.Json.JsonSerializer", (23, 23)),
    ],
)
def test_extract_imports(
    import_test_code: str,
    expected_import_name: str,
    expected_line_range: tuple[int, int],
) -> None:
    driver_tree = CSharpDriverTree.from_code(import_test_code, "does_not_matter.cs")
    imports = driver_tree.extract_imports()
    extracted = [(im.name, (im.start_line, im.end_line)) for im in imports]

    assert (expected_import_name, expected_line_range) in extracted, (
        f"Expected import ({expected_import_name}. {expected_line_range}) "
        f"not found in extracted imports: {extracted}"
    )


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


def test_extract_classes_no_false_positives(class_test_code: str) -> None:
    driver_tree = CSharpDriverTree.from_code(class_test_code, "does_not_matter.cs")
    klasses = driver_tree.extract_class_definitions()
    assert len(klasses) == 9


@pytest.mark.parametrize(
    "expected_class_name, expected_line_range",
    [
        ("SimpleClass", (8, 38)),
        ("InnerClass", (29, 37)),
        ("AbstractClass", (41, 49)),
        ("ConcreteClass", (52, 68)),
        ("GenericClass", (71, 84)),
        ("PartialClass", (87, 96)),
        ("StaticUtilities", (99, 105)),
        ("SealedClass", (108, 114)),
        ("AttributedClass", (128, 151)),
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


@pytest.mark.parametrize(
    "expected_class_name, expected_bases",
    [
        ("ConcreteClass", ("AbstractClass", "IComparable<ConcreteClass>")),
        ("SealedClass", ("AbstractClass",)),
    ],
)
def test_extract_base_classes_and_interfaces(
    class_test_code: str, expected_class_name: str, expected_bases: list[str]
) -> None:
    driver_tree = CSharpDriverTree.from_code(class_test_code, "does_not_matter.cs")
    klasses = driver_tree.extract_class_definitions()
    extracted = [(k.name, k.base_class_names) for k in klasses]

    assert (expected_class_name, expected_bases) in extracted, (
        f"Expected base classes and interfaces: ({expected_bases}) for class ({expected_class_name}) "
        f"but not found in extracted classes: {extracted}"
    )
