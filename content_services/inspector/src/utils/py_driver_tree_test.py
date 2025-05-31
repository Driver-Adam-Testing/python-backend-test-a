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


@pytest.fixture(scope="module")
def imports_test_code() -> str:
    file_path = (
        pathlib.Path(__file__).parent
        / "treesitter_testcases"
        / "python"
        / "test_imports.py"
    )
    with open(file_path, encoding="utf-8") as f:
        return f.read()


def test_extract_import_duplications(
    imports_test_code: str,
) -> None:
    driver_tree = PyDriverTree.from_code(imports_test_code, "does_not_matter.py")
    imports = driver_tree.extract_imports()

    assert len(imports) == 40


@pytest.mark.parametrize(
    "expected_import_name, expected_line_range",
    [
        ("os", (4, 4)),
        ("sys", (5, 5)),
        ("json", (6, 6)),
        ("numpy", (9, 9)),
        ("pandas", (10, 10)),
        ("matplotlib.pyplot", (11, 11)),
        ("typing.List", (14, 14)),
        ("typing.Dict", (14, 14)),
        ("typing.Optional", (14, 14)),
        ("pathlib.Path", (15, 15)),
        ("datetime.datetime", (16, 16)),
        ("datetime.timedelta", (16, 16)),
        ("collections.defaultdict", (19, 19)),
        ("functools.wraps", (20, 20)),
        ("math.*", (23, 23)),
        ("socket", (26, 26)),
        ("threading", (26, 26)),
        ("time", (26, 26)),
        ("ujson", (30, 30)),
        ("json", (32, 32)),
        ("xml.etree.ElementTree", (35, 35)),
        ("xml.etree.ElementTree.Element", (36, 36)),
        ("xml.etree.ElementTree.SubElement", (36, 36)),
        ("email.mime.text", (37, 37)),
        (".sibling_module", (40, 40)),
        ("..parent_module", (41, 41)),
        ("..utils.helper_function", (42, 42)),
        (".subpackage.submodule", (43, 43)),
        ("__future__.annotations", (46, 46)),
        ("__future__.print_function", (47, 47)),
        ("__future__.unicode_literals", (47, 47)),
        ("random", (51, 51)),
        ("secrets.token_hex", (52, 52)),
        ("very.deeply.nested.package.subpackage.module.VeryLongClassName", (56, 60)),
        (
            "very.deeply.nested.package.subpackage.module.another_long_function_name",
            (56, 60),
        ),
        ("very.deeply.nested.package.subpackage.module.SOME_CONSTANT", (56, 60)),
        ("fast_library.fast_function", (70, 70)),
        ("slow_library.fast_function", (73, 73)),
        ("sys", (80, 80)),
        ("importlib", (85, 85)),
    ],
)
def test_extract_import(
    imports_test_code: str,
    expected_import_name: str,
    expected_line_range: tuple[int, int],
) -> None:
    driver_tree = PyDriverTree.from_code(imports_test_code, "does_not_matter.py")
    imports = driver_tree.extract_imports()
    extracted = [(im.name, (im.start_line, im.end_line)) for im in imports]

    assert (expected_import_name, expected_line_range) in extracted, (
        f"Expected function ({expected_import_name}, {expected_line_range}) "
        f"not found in extracted imports: {extracted}"
    )


@pytest.mark.parametrize(
    "expected_not_included_import_name",
    ["some_new_feature", "module", "public_function", "PublicClass", "PUBLIC_CONSTANT"],
)
def test_imports_not_supported(
    imports_test_code: str, expected_not_included_import_name: str
) -> None:
    driver_tree = PyDriverTree.from_code(imports_test_code, "does_not_matter.py")
    imports = driver_tree.extract_imports()
    assert expected_not_included_import_name in imports_test_code

    extracted_import_names = [im.name for im in imports]
    assert expected_not_included_import_name not in extracted_import_names, (
        f"Expected import ({expected_not_included_import_name}) "
        f"to not be found in extracted imports: {extracted_import_names}"
    )


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


def test_extract_functions_duplications(
    functions_test_code: str,
) -> None:
    driver_tree = PyDriverTree.from_code(functions_test_code, "does_not_matter.py")
    functions = driver_tree.extract_function_definitions()

    assert len(functions) == 22


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


@pytest.fixture(scope="module")
def class_test_code() -> str:
    file_path = (
        pathlib.Path(__file__).parent
        / "treesitter_testcases"
        / "python"
        / "test_classes.py"
    )
    with open(file_path, encoding="utf-8") as f:
        return f.read()


def test_extract_classes_duplications(
    class_test_code: str,
) -> None:
    driver_tree = PyDriverTree.from_code(class_test_code, "does_not_matter.py")
    klasses = driver_tree.extract_class_definitions()

    assert len(klasses) == 17


@pytest.mark.parametrize(
    "expected_class_name, expected_line_range",
    [
        ("SimpleClass", (8, 9)),
        ("Animal", (12, 14)),
        ("Dog", (16, 18)),
        ("Mixin", (21, 23)),
        ("MultipleInheritance", (25, 27)),
        ("AbstractShape", (30, 33)),
        ("Rectangle", (35, 41)),
        ("Point", (45, 48)),
        ("DecoratedClass", (52, 53)),
        ("OuterClass", (56, 70)),
        ("InnerClass", (62, 70)),
        ("DeeplyNestedClass", (68, 70)),
        ("MethodTypes", (73, 96)),
        ("SpecialMethods", (99, 119)),
        ("GenericContainer", (126, 131)),
        ("MetaClass", (134, 136)),
        ("WithMetaclass", (138, 140)),
    ],
)
def test_extract_classes(
    class_test_code: str, expected_class_name: str, expected_line_range: tuple[int, int]
) -> None:
    driver_tree = PyDriverTree.from_code(class_test_code, "does_not_matter.py")
    klasses = driver_tree.extract_class_definitions()
    extracted = [(k.name, (k.start_line, k.end_line)) for k in klasses]

    assert (expected_class_name, expected_line_range) in extracted, (
        f"Expected class ({expected_class_name}, {expected_line_range}) "
        f"not found in extracted classes: {extracted}"
    )


@pytest.fixture(scope="module")
def global_vars_test_code() -> str:
    file_path = (
        pathlib.Path(__file__).parent
        / "treesitter_testcases"
        / "python"
        / "test_variables.py"
    )
    with open(file_path, encoding="utf-8") as f:
        return f.read()


def test_extract_global_vars_duplications(
    global_vars_test_code: str,
) -> None:
    driver_tree = PyDriverTree.from_code(global_vars_test_code, "does_not_matter.py")
    global_vars = driver_tree.extract_variables()

    assert len(global_vars) == 16


@pytest.mark.parametrize(
    "expected_gbl_var_name, expected_line_range",
    [
        ("simple_var", (7, 7)),
        ("number_var", (8, 8)),
        ("API_VERSION", (11, 11)),
        ("MAX_CONNECTIONS", (12, 12)),
        ("typed_string", (15, 15)),
        ("typed_list", (16, 16)),
        ("FINAL_CONSTANT", (19, 19)),
        ("FINAL_NUMBER", (20, 20)),
        ("a", (23, 23)),
        ("b", (23, 23)),
        ("c", (23, 23)),
        ("ALLOWED_EXTENSIONS", (26, 26)),
        ("ERROR_CODES", (27, 31)),
        ("global_counter", (51, 51)),
        ("global_registry", (52, 52)),
        ("module_scope", (60, 60)),
    ],
)
def test_extract_global_vars(
    global_vars_test_code: str,
    expected_gbl_var_name: str,
    expected_line_range: tuple[int, int],
) -> None:
    driver_tree = PyDriverTree.from_code(global_vars_test_code, "does_not_matter.py")
    global_vars = driver_tree.extract_variables()
    extracted = [(gv.name, (gv.start_line, gv.end_line)) for gv in global_vars]

    assert (expected_gbl_var_name, expected_line_range) in extracted, (
        f"Expected global variable ({expected_gbl_var_name}, {expected_line_range}) "
        f"not found in extracted global variables: {extracted}"
    )
