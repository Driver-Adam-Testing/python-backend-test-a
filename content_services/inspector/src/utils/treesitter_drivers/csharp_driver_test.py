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


@pytest.fixture(scope="module")
def method_test_code() -> str:
    file_path = (
        pathlib.Path(__file__).parent
        / "treesitter_testcases"
        / "csharp"
        / "test_methods.cs"
    )
    with open(file_path, encoding="utf-8") as f:
        return f.read()


def test_extract_method_likes_no_false_positives(method_test_code: str) -> None:
    driver_tree = CSharpDriverTree.from_code(method_test_code, "does_not_matter.cs")
    method_likes = driver_tree.extract_method_like_definitions()
    assert len(method_likes) == 27


@pytest.mark.parametrize(
    "expected_method_name, expected_line_range, expected_kind, expected_modifiers",
    [
        ("MethodExamples", (11, 13), "constructor", {"public"}),
        ("MethodExamples", (16, 20), "constructor", {"public"}),
        ("Name", (23, 23), "property", {"public"}),
        ("Value", (24, 24), "property", {"public"}),
        ("CreatedAt", (27, 27), "property", {"public"}),
        ("Description", (31, 35), "property", {"public"}),
        ("StaticMethod", (38, 41), "method", {"static", "public"}),
        ("ProcessData", (44, 52), "method", {"public"}),
        ("PrivateHelper", (55, 58), "method", {"private"}),
        ("CreateList", (61, 64), "method", {"public"}),
        ("ToString", (67, 70), "method", {"public", "override"}),
        ("VirtualMethod", (73, 76), "method", {"public", "virtual"}),
        ("AbstractMethod", (79, 79), "method", {"public", "abstract"}),
        ("AsyncMethod", (82, 86), "method", {"public", "async"}),
        ("TryGetValue", (89, 93), "method", {"public"}),
        ("ModifyValue", (96, 99), "method", {"public"}),
        ("ProcessReadOnly", (102, 105), "method", {"public"}),
        ("Reverse", (108, 108), "method", {"public", "static"}),
        ("+", (111, 114), "operator_overload", {"public", "static"}),
        (
            "string",
            (117, 120),
            "conversion_operator_declaration",
            {"public", "static", "implicit"},
        ),
        (
            "int",
            (123, 126),
            "conversion_operator_declaration",
            {"public", "static", "explicit"},
        ),
        ("~MethodExamples", (129, 132), "destructor", set()),
        ("GetDisplayName", (138, 138), "method", {"public"}),
        ("CalculateComplex", (141, 149), "method", {"public"}),
        ("LocalHelper", (143, 146), "local_function", set()),
        ("Reverse", (155, 163), "method", {"public", "static"}),
        ("IsNullOrWhiteSpace", (165, 168), "method", {"public", "static"}),
    ],
)
def test_extract_method_likes(
    method_test_code: str,
    expected_method_name: str,
    expected_line_range: tuple[int, int],
    expected_kind: str,
    expected_modifiers: set[str],
) -> None:
    driver_tree = CSharpDriverTree.from_code(method_test_code, "does_not_matter.cs")
    method_likes = driver_tree.extract_method_like_definitions()
    extracted = []
    for m in method_likes:
        name = m.name
        line_range = (m.start_line, m.end_line)
        callable_kind = m.lang_specific_data["callable_kind"].value
        modifiers = {v.value for v in m.lang_specific_data.get("modifiers")}
        extracted.append((name, line_range, callable_kind, modifiers))

    assert (
        expected_method_name,
        expected_line_range,
        expected_kind,
        expected_modifiers,
    ) in extracted, (
        f"Expected method-like ({expected_method_name}, {expected_line_range}, {expected_kind, expected_modifiers}) "
        f"not found in extracted method-likes: {extracted}"
    )


@pytest.mark.parametrize(
    "expected_op_overload_name, expected_line_range, expected_op_return_ty",
    [
        (("+"), (111, 114), "MethodExamples"),
    ],
)
def test_extract_operator_overload_op_and_target(
    method_test_code: str,
    expected_op_overload_name: str,
    expected_line_range: tuple[int, int],
    expected_op_return_ty: str,
) -> None:
    driver_tree = CSharpDriverTree.from_code(method_test_code, "does_not_matter.cs")
    method_likes = driver_tree.extract_method_like_definitions()
    op_overloads = []
    for m in method_likes:
        if m.lang_specific_data["callable_kind"].value == "operator_overload":
            name = m.name
            line_range = (m.start_line, m.end_line)
            return_ty = m.lang_specific_data["op_overload_return_ty"]
            op_overloads.append((name, line_range, return_ty))

    assert (
        expected_op_overload_name,
        expected_line_range,
        expected_op_return_ty,
    ) in op_overloads, (
        f"expected operator overload ({expected_op_overload_name}, {expected_line_range}, {expected_op_return_ty}) "
        f"not found in extracted operator overloads: {op_overloads}"
    )
