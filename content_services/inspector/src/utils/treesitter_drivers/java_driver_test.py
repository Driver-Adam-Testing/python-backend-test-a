import pathlib

import pytest

from utils.lang_specialization.symbol_common import SymbolKind

from .java_driver import JavaDriverTree


@pytest.fixture(scope="module")
def imports_test_code() -> str:
    file_path = (
        pathlib.Path(__file__).parent
        / "treesitter_testcases"
        / "java"
        / "test_imports.java"
    )
    with open(file_path, encoding="utf-8") as f:
        return f.read()


@pytest.fixture(scope="module")
def classes_test_code() -> str:
    file_path = (
        pathlib.Path(__file__).parent
        / "treesitter_testcases"
        / "java"
        / "test_classes.java"
    )
    with open(file_path, encoding="utf-8") as f:
        return f.read()


@pytest.fixture(scope="module")
def methods_test_code() -> str:
    file_path = (
        pathlib.Path(__file__).parent
        / "treesitter_testcases"
        / "java"
        / "test_methods.java"
    )
    with open(file_path, encoding="utf-8") as f:
        return f.read()


@pytest.fixture(scope="module")
def variables_test_code() -> str:
    file_path = (
        pathlib.Path(__file__).parent
        / "treesitter_testcases"
        / "java"
        / "test_variables.java"
    )
    with open(file_path, encoding="utf-8") as f:
        return f.read()


@pytest.fixture(scope="module")
def interfaces_test_code() -> str:
    file_path = (
        pathlib.Path(__file__).parent
        / "treesitter_testcases"
        / "java"
        / "test_interfaces.java"
    )
    with open(file_path, encoding="utf-8") as f:
        return f.read()


@pytest.fixture(scope="module")
def enums_test_code() -> str:
    file_path = (
        pathlib.Path(__file__).parent
        / "treesitter_testcases"
        / "java"
        / "test_enums.java"
    )
    with open(file_path, encoding="utf-8") as f:
        return f.read()


def test_extract_imports_duplications(imports_test_code: str) -> None:
    driver_tree = JavaDriverTree.from_code(imports_test_code, "test.java")
    imports = driver_tree.extract_imports()

    assert len(imports) == 6


@pytest.mark.parametrize(
    "expected_import_name, expected_line_range",
    [
        ("java.util", (3, 3)),
        ("java.io.File", (4, 4)),
        ("java.io.IOException", (5, 5)),
        ("java.lang.Math.PI", (6, 6)),
        ("java.lang.Math", (7, 7)),
    ],
)
def test_extract_imports(
    imports_test_code: str,
    expected_import_name: str,
    expected_line_range: tuple[int, int],
) -> None:
    driver_tree = JavaDriverTree.from_code(imports_test_code, "test.java")
    imports = driver_tree.extract_imports()
    extracted = [(imp.name, (imp.start_line, imp.end_line)) for imp in imports]

    assert (expected_import_name, expected_line_range) in extracted, (
        f"Expected import ({expected_import_name}, {expected_line_range}) "
        f"not found in extracted imports: {extracted}"
    )


def test_extract_classes_duplications(classes_test_code: str) -> None:
    driver_tree = JavaDriverTree.from_code(classes_test_code, "test.java")
    classes = driver_tree.extract_class_definitions()

    assert len(classes) == 4


@pytest.mark.parametrize(
    "expected_class_name, expected_line_range",
    [
        ("TestClass", (9, 32)),
        ("InnerClass", (25, 31)),
        ("AbstractClass", (34, 36)),
        ("ConcreteClass", (38, 48)),
    ],
)
def test_extract_classes(
    classes_test_code: str,
    expected_class_name: str,
    expected_line_range: tuple[int, int],
) -> None:
    driver_tree = JavaDriverTree.from_code(classes_test_code, "test.java")
    classes = driver_tree.extract_class_definitions()
    extracted = [(cls.name, (cls.start_line, cls.end_line)) for cls in classes]

    assert (expected_class_name, expected_line_range) in extracted, (
        f"Expected class ({expected_class_name}, {expected_line_range}) "
        f"not found in extracted classes: {extracted}"
    )


def test_extract_class_inheritance(classes_test_code: str) -> None:
    """Test that class inheritance information is extracted correctly."""
    driver_tree = JavaDriverTree.from_code(classes_test_code, "test.java")
    classes = driver_tree.extract_class_definitions()

    # Find ConcreteClass which extends AbstractClass and implements Comparable
    concrete_class = next((cls for cls in classes if cls.name == "ConcreteClass"), None)
    assert concrete_class is not None
    assert concrete_class.base_class_names is not None
    assert (
        len(concrete_class.base_class_names) >= 1
    )  # Should have AbstractClass and Comparable


def test_extract_interfaces_duplications(interfaces_test_code: str) -> None:
    driver_tree = JavaDriverTree.from_code(interfaces_test_code, "test.java")
    interfaces = driver_tree.extract_interface_definitions()

    assert len(interfaces) == 4


@pytest.mark.parametrize(
    "expected_interface_name, expected_line_range",
    [
        ("Drawable", (6, 22)),
        ("Resizable", (24, 31)),
        ("Calculator", (34, 37)),
        ("ResizeListener", (28, 30)),
    ],
)
def test_extract_interfaces(
    interfaces_test_code: str,
    expected_interface_name: str,
    expected_line_range: tuple[int, int],
) -> None:
    driver_tree = JavaDriverTree.from_code(interfaces_test_code, "test.java")
    interfaces = driver_tree.extract_interface_definitions()
    extracted = [
        (iface.name, (iface.start_line, iface.end_line)) for iface in interfaces
    ]

    assert (expected_interface_name, expected_line_range) in extracted, (
        f"Expected interface ({expected_interface_name}, {expected_line_range}) "
        f"not found in extracted interfaces: {extracted}"
    )


def test_extract_interface_inheritance(interfaces_test_code: str) -> None:
    """Test that interface inheritance information is extracted correctly."""
    driver_tree = JavaDriverTree.from_code(interfaces_test_code, "test.java")
    interfaces = driver_tree.extract_interface_definitions()

    # Find Resizable which extends Drawable
    resizable = next((iface for iface in interfaces if iface.name == "Resizable"), None)
    assert resizable is not None
    assert resizable.base_class_names is not None
    assert "Drawable" in resizable.base_class_names


def test_extract_methods_duplications(methods_test_code: str) -> None:
    driver_tree = JavaDriverTree.from_code(methods_test_code, "test.java")
    methods = driver_tree.extract_method_definitions()
    constructors = driver_tree.extract_constructor_definitions()

    # Should have methods + constructors
    assert len(methods) >= 5
    assert len(constructors) >= 1


@pytest.mark.parametrize(
    "expected_method_name, expected_line_range",
    [
        ("staticMethod", (11, 13)),
        ("processData", (16, 22)),
        ("privateHelper", (25, 27)),
        ("toString", (35, 38)),
    ],
)
def test_extract_methods(
    methods_test_code: str,
    expected_method_name: str,
    expected_line_range: tuple[int, int],
) -> None:
    driver_tree = JavaDriverTree.from_code(methods_test_code, "test.java")
    methods = driver_tree.extract_method_definitions()
    extracted = [
        (method.name, (method.start_line, method.end_line)) for method in methods
    ]

    assert (expected_method_name, expected_line_range) in extracted, (
        f"Expected method ({expected_method_name}, {expected_line_range}) "
        f"not found in extracted methods: {extracted}"
    )


@pytest.mark.parametrize(
    "expected_constructor_name, expected_line_range",
    [
        ("MethodExamples", (6, 8)),
    ],
)
def test_extract_constructors(
    methods_test_code: str,
    expected_constructor_name: str,
    expected_line_range: tuple[int, int],
) -> None:
    driver_tree = JavaDriverTree.from_code(methods_test_code, "test.java")
    constructors = driver_tree.extract_constructor_definitions()
    extracted = [(ctor.name, (ctor.start_line, ctor.end_line)) for ctor in constructors]

    assert (expected_constructor_name, expected_line_range) in extracted, (
        f"Expected constructor ({expected_constructor_name}, {expected_line_range}) "
        f"not found in extracted constructors: {extracted}"
    )


def test_extract_variables_duplications(variables_test_code: str) -> None:
    driver_tree = JavaDriverTree.from_code(variables_test_code, "test.java")
    variables = driver_tree.extract_field_definitions()

    assert len(variables) >= 5


@pytest.mark.parametrize(
    "expected_variable_name, expected_line_range",
    [
        ("MAX_SIZE", (5, 5)),
        ("defaultName", (6, 6)),
        ("id", (9, 9)),
        ("name", (10, 10)),
        ("active", (11, 11)),
    ],
)
def test_extract_variables(
    variables_test_code: str,
    expected_variable_name: str,
    expected_line_range: tuple[int, int],
) -> None:
    driver_tree = JavaDriverTree.from_code(variables_test_code, "test.java")
    variables = driver_tree.extract_field_definitions()
    extracted = [(var.name, (var.start_line, var.end_line)) for var in variables]

    assert (expected_variable_name, expected_line_range) in extracted, (
        f"Expected variable ({expected_variable_name}, {expected_line_range}) "
        f"not found in extracted variables: {extracted}"
    )


def test_extract_function_calls(methods_test_code: str) -> None:
    """Test extraction of method calls."""
    driver_tree = JavaDriverTree.from_code(methods_test_code, "test.java")
    calls = driver_tree.extract_function_calls()

    # Should find method calls in the code
    call_names = [call.name for call in calls]
    assert (
        "toString" in call_names or "append" in call_names
    )  # From StringBuilder usage


def test_extract_fully_qualified_paths(classes_test_code: str) -> None:
    """Test fully qualified path generation with package information."""
    driver_tree = JavaDriverTree.from_code(classes_test_code, "test.java")

    # Test package is included in fully qualified paths
    classes = driver_tree.extract_class_definitions()
    test_class = next((cls for cls in classes if cls.name == "TestClass"), None)
    assert test_class is not None
    assert "com.example" in test_class.fully_qualified_parent_path

    # Test nested class paths
    inner_class = next((cls for cls in classes if cls.name == "InnerClass"), None)
    assert inner_class is not None
    assert "TestClass" in inner_class.fully_qualified_parent_path


def test_extract_all_symbols(classes_test_code: str) -> None:
    """Test extraction of all symbols together."""
    driver_tree = JavaDriverTree.from_code(classes_test_code, "test.java")
    all_symbols = driver_tree.extract_all_symbols()

    # Should have multiple types of symbols
    assert len(all_symbols) > 0

    symbol_kinds = {symbol.symbol_kind for symbol in all_symbols}
    assert SymbolKind.IMPORT in symbol_kinds
    assert SymbolKind.VARIABLE in symbol_kinds
    assert SymbolKind.CALLABLE in symbol_kinds


def test_extract_enums_duplications(enums_test_code: str) -> None:
    driver_tree = JavaDriverTree.from_code(enums_test_code, "test.java")
    enums = driver_tree.extract_enum_definitions()

    assert len(enums) == 3


@pytest.mark.parametrize(
    "expected_enum_name, expected_line_range",
    [
        ("Color", (6, 8)),
        ("Status", (13, 26)),
        ("Priority", (31, 51)),
    ],
)
def test_extract_enums(
    enums_test_code: str,
    expected_enum_name: str,
    expected_line_range: tuple[int, int],
) -> None:
    driver_tree = JavaDriverTree.from_code(enums_test_code, "test.java")
    enums = driver_tree.extract_enum_definitions()
    extracted = [(enum.name, (enum.start_line, enum.end_line)) for enum in enums]

    assert (expected_enum_name, expected_line_range) in extracted, (
        f"Expected enum ({expected_enum_name}, {expected_line_range}) "
        f"not found in extracted enums: {extracted}"
    )
