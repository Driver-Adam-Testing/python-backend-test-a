import pathlib

import pytest

from .ruby_driver import RubyDriverTree, RubyMethodKind


@pytest.fixture(scope="module")
def requires_test_code() -> str:
    file_path = (
        pathlib.Path(__file__).parent
        / "treesitter_testcases"
        / "ruby"
        / "test_requires.rb"
    )
    with open(file_path, encoding="utf-8") as f:
        return f.read()


def test_extract_requires_count(requires_test_code: str) -> None:
    """Test that we extract the correct number of requires"""
    driver_tree = RubyDriverTree.from_code(requires_test_code, "test_requires.rb")
    requires = driver_tree._extract_requires()
    # Count from test_requires.rb: 26 top-level + 10 inside classes/methods = 36 total
    assert len(requires) == 36
    # All requires should have empty FQP (always top-level semantically in Ruby)
    for req in requires:
        assert req.fully_qualified_parent_path == ""


def test_extract_absolute_requires(requires_test_code: str) -> None:
    """Test extraction of absolute requires (using 'require')"""
    driver_tree = RubyDriverTree.from_code(requires_test_code, "test_requires.rb")
    requires = driver_tree._extract_requires()

    # Filter for absolute requires only
    absolute_requires = [r for r in requires if not r.bespoke_data.is_relative]

    # Should have 17 require statements (12 top-level + 5 inside classes/methods)
    assert len(absolute_requires) == 17

    # All requires should have empty FQP (semantically top-level in Ruby)
    for req in absolute_requires:
        assert req.fully_qualified_parent_path == ""

    # Validate specific absolute requires (including those in classes/methods)
    absolute_names = [r.name for r in absolute_requires]
    # Top-level requires
    assert "json" in absolute_names
    assert "yaml" in absolute_names
    assert "active_support" in absolute_names
    assert "fileutils" in absolute_names
    assert "active_support/core_ext" in absolute_names
    assert "rails/all" in absolute_names
    assert "rack/utils" in absolute_names
    assert "rack" in absolute_names
    assert "sinatra" in absolute_names
    assert "bundler" in absolute_names  # .rb stripped
    assert "nokogiri" in absolute_names
    assert "open-uri" in absolute_names
    # Requires inside classes/methods
    assert "set" in absolute_names
    assert "forwardable" in absolute_names
    assert "tmpdir" in absolute_names
    assert "benchmark" in absolute_names
    assert "digest" in absolute_names


def test_extract_relative_requires(requires_test_code: str) -> None:
    """Test extraction of relative requires (using 'require_relative')"""
    driver_tree = RubyDriverTree.from_code(requires_test_code, "test_requires.rb")
    requires = driver_tree._extract_requires()

    # Filter for relative requires only
    relative_requires = [r for r in requires if r.bespoke_data.is_relative]

    # Should have 19 require_relative statements (14 top-level + 5 inside classes/methods)
    assert len(relative_requires) == 19

    # All requires should have empty FQP (semantically top-level in Ruby)
    for req in relative_requires:
        assert req.fully_qualified_parent_path == ""

    # Validate specific relative requires with full paths preserved
    relative_names = [r.name for r in relative_requires]
    # Top-level requires
    assert "../models/user" in relative_names
    assert "./helper" in relative_names
    assert "config/database" in relative_names
    assert "../lib/constants" in relative_names
    assert "./services/auth_service" in relative_names
    assert "utils" in relative_names
    assert "validators/email_validator" in relative_names
    assert "../../shared/logger" in relative_names
    assert "../../../common/base" in relative_names
    assert "lib/utils" in relative_names
    assert "../app" in relative_names
    assert "./config" in relative_names  # .rb stripped
    assert "helpers" in relative_names
    assert "../models/post" in relative_names
    # Requires inside classes/methods
    assert "class_helper" in relative_names
    assert "module_helper" in relative_names
    assert "method_helper" in relative_names
    assert "benchmark_helper" in relative_names
    assert "digest_helper" in relative_names


@pytest.mark.parametrize(
    "expected_name, expected_line, expected_is_relative",
    [
        # Absolute requires (lines 4-7)
        ("json", 4, False),
        ("yaml", 5, False),
        ("active_support", 6, False),
        ("fileutils", 7, False),
        # Nested path absolute requires (lines 10-12)
        ("active_support/core_ext", 10, False),
        ("rails/all", 11, False),
        ("rack/utils", 12, False),
        # Relative requires (lines 15-17)
        ("../models/user", 15, True),
        ("./helper", 16, True),
        ("config/database", 17, True),
        # Relative with double quotes (lines 20-21)
        ("../lib/constants", 20, True),
        ("./services/auth_service", 21, True),
        # Relative without ./ (lines 24-25)
        ("utils", 24, True),
        ("validators/email_validator", 25, True),
        # Deep relative paths (lines 28-29)
        ("../../shared/logger", 28, True),
        ("../../../common/base", 29, True),
        # Mixed section (lines 32-35)
        ("rack", 32, False),
        ("lib/utils", 33, True),
        ("sinatra", 34, False),
        ("../app", 35, True),
        # With .rb extension (lines 38-39) - should be stripped
        ("bundler", 38, False),
        ("./config", 39, True),
        # Quote variations (lines 42-45)
        ("nokogiri", 42, False),
        ("open-uri", 43, False),
        ("helpers", 44, True),
        ("../models/post", 45, True),
    ],
)
def test_extract_requires_details(
    requires_test_code: str,
    expected_name: str,
    expected_line: int,
    expected_is_relative: bool,
) -> None:
    """Test that we extract correct require details: name, line, is_relative flag, and FQP"""
    driver_tree = RubyDriverTree.from_code(requires_test_code, "test_requires.rb")
    requires = driver_tree._extract_requires()

    # Find the require at the expected line
    matching_requires = [r for r in requires if r.start_line == expected_line]

    assert len(matching_requires) > 0, (
        f"No require found at line {expected_line}. "
        f"Available lines: {[r.start_line for r in requires]}"
    )

    req = matching_requires[0]

    assert req.name == expected_name, (
        f"Expected name '{expected_name}' at line {expected_line}, "
        f"but got '{req.name}'"
    )

    assert req.bespoke_data.is_relative == expected_is_relative, (
        f"Expected is_relative={expected_is_relative} for '{expected_name}' "
        f"at line {expected_line}, but got {req.bespoke_data.is_relative}"
    )

    # All requires should have empty FQP (top-level in Ruby)
    assert req.fully_qualified_parent_path == "", (
        f"Expected empty FQP for '{expected_name}' at line {expected_line}, "
        f"but got '{req.fully_qualified_parent_path}'"
    )


def test_extract_requires_with_rb_extension_stripped(requires_test_code: str) -> None:
    """Test that .rb extensions are stripped from require paths"""
    driver_tree = RubyDriverTree.from_code(requires_test_code, "test_requires.rb")
    requires = driver_tree._extract_requires()

    # Find the requires that originally had .rb
    bundler_req = next(r for r in requires if r.start_line == 38)
    config_req = next(r for r in requires if r.start_line == 39)

    assert bundler_req.name == "bundler"
    assert not bundler_req.name.endswith(".rb")

    assert config_req.name == "./config"
    assert not config_req.name.endswith(".rb")


def test_extract_requires_preserves_path_structure(requires_test_code: str) -> None:
    """Test that full path structure is preserved in require names"""
    driver_tree = RubyDriverTree.from_code(requires_test_code, "test_requires.rb")
    requires = driver_tree._extract_requires()

    # Check that nested paths are preserved
    nested_absolute = next(r for r in requires if r.name == "active_support/core_ext")
    assert nested_absolute.name == "active_support/core_ext"
    assert not nested_absolute.bespoke_data.is_relative

    # Check that relative path components are preserved
    deep_relative = next(r for r in requires if r.name == "../../shared/logger")
    assert deep_relative.name == "../../shared/logger"
    assert deep_relative.bespoke_data.is_relative

    # Check that ./ prefix is preserved
    dot_slash_relative = next(r for r in requires if r.name == "./helper")
    assert dot_slash_relative.name == "./helper"
    assert dot_slash_relative.bespoke_data.is_relative


def test_extract_requires_in_classes_and_methods(requires_test_code: str) -> None:
    """Test that requires inside classes, modules, and methods are extracted correctly"""
    driver_tree = RubyDriverTree.from_code(requires_test_code, "test_requires.rb")
    requires = driver_tree._extract_requires()

    # Find requires that are syntactically inside classes/methods
    # These should still have empty FQP because requires are semantically top-level in Ruby
    set_require = next((r for r in requires if r.name == "set"), None)
    assert set_require is not None, "require 'set' inside class should be extracted"
    assert set_require.fully_qualified_parent_path == ""
    assert not set_require.bespoke_data.is_relative

    class_helper = next((r for r in requires if r.name == "class_helper"), None)
    assert (
        class_helper is not None
    ), "require_relative 'class_helper' inside class should be extracted"
    assert class_helper.fully_qualified_parent_path == ""
    assert class_helper.bespoke_data.is_relative

    forwardable_require = next((r for r in requires if r.name == "forwardable"), None)
    assert (
        forwardable_require is not None
    ), "require 'forwardable' inside module should be extracted"
    assert forwardable_require.fully_qualified_parent_path == ""

    tmpdir_require = next((r for r in requires if r.name == "tmpdir"), None)
    assert (
        tmpdir_require is not None
    ), "require 'tmpdir' inside method should be extracted"
    assert tmpdir_require.fully_qualified_parent_path == ""

    benchmark_require = next((r for r in requires if r.name == "benchmark"), None)
    assert (
        benchmark_require is not None
    ), "require 'benchmark' inside class method should be extracted"
    assert benchmark_require.fully_qualified_parent_path == ""

    digest_require = next((r for r in requires if r.name == "digest"), None)
    assert (
        digest_require is not None
    ), "require 'digest' inside instance method should be extracted"
    assert digest_require.fully_qualified_parent_path == ""


def test_extract_imports_alias(requires_test_code: str) -> None:
    """Test that extract_imports works as an alias for extract_requires"""
    driver_tree = RubyDriverTree.from_code(requires_test_code, "test_requires.rb")
    requires = driver_tree._extract_requires()
    imports = driver_tree.extract_imports()

    assert len(requires) == len(imports)
    assert [r.name for r in requires] == [i.name for i in imports]


@pytest.fixture(scope="module")
def data_structures_test_code() -> str:
    file_path = (
        pathlib.Path(__file__).parent
        / "treesitter_testcases"
        / "ruby"
        / "test_classes_modules.rb"
    )
    with open(file_path, encoding="utf-8") as f:
        return f.read()


def test_extract_classes_count(data_structures_test_code: str) -> None:
    """Test that we extract the correct number of classes"""
    driver_tree = RubyDriverTree.from_code(
        data_structures_test_code, "test_classes_modules.rb"
    )
    classes = driver_tree.extract_data_structure_definitions()
    # Should extract both classes and modules (will update counts after implementation)
    assert len(classes) >= 20  # At least 20 classes defined


def test_extract_class_name_and_lines(data_structures_test_code: str) -> None:
    """Test that we extract the correct class name and line numbers for Calculator"""
    driver_tree = RubyDriverTree.from_code(
        data_structures_test_code, "test_classes_modules.rb"
    )
    classes = driver_tree.extract_data_structure_definitions()

    # Find Calculator class
    calc_class = next((c for c in classes if c.name == "Calculator"), None)
    assert calc_class is not None, "Calculator class should be extracted"
    assert calc_class.name == "Calculator"
    assert calc_class.start_line == 4
    assert calc_class.end_line == 14


def test_extract_methods_count(data_structures_test_code: str) -> None:
    """Test that we extract the correct number of methods from Calculator class"""
    driver_tree = RubyDriverTree.from_code(
        data_structures_test_code, "test_classes_modules.rb"
    )
    methods = driver_tree.extract_callable_definitions()

    # Filter for Calculator methods only
    calculator_methods = [
        m for m in methods if m.fully_qualified_parent_path == "Calculator"
    ]
    assert len(calculator_methods) == 2


@pytest.mark.parametrize(
    "expected_name, expected_start_line, expected_end_line",
    [
        ("add", 6, 8),
        ("subtract", 11, 13),
    ],
)
def test_extract_methods_names_and_lines(
    data_structures_test_code: str,
    expected_name: str,
    expected_start_line: int,
    expected_end_line: int,
) -> None:
    """Test that we extract the correct method names and line numbers from Calculator"""
    driver_tree = RubyDriverTree.from_code(
        data_structures_test_code, "test_classes_modules.rb"
    )
    methods = driver_tree.extract_callable_definitions()

    # Filter for Calculator methods only
    calculator_methods = [
        m for m in methods if m.fully_qualified_parent_path == "Calculator"
    ]
    extracted = [(m.name, m.start_line, m.end_line) for m in calculator_methods]

    assert (expected_name, expected_start_line, expected_end_line) in extracted, (
        f"Expected method ({expected_name}, lines {expected_start_line}-{expected_end_line}) "
        f"not found in extracted Calculator methods: {extracted}"
    )


@pytest.mark.parametrize(
    "expected_name, expected_kind",
    [
        ("add", RubyMethodKind.INSTANCE_METHOD),
        ("subtract", RubyMethodKind.CLASS_METHOD),
    ],
)
def test_extract_methods_bespoke_data(
    data_structures_test_code: str, expected_name: str, expected_kind: RubyMethodKind
) -> None:
    """Test that we extract the correct method kind in bespoke_data"""
    driver_tree = RubyDriverTree.from_code(
        data_structures_test_code, "test_classes_modules.rb"
    )
    methods = driver_tree.extract_callable_definitions()

    method = next((m for m in methods if m.name == expected_name), None)
    assert method is not None, f"Method {expected_name} not found"
    assert (
        method.bespoke_data is not None
    ), f"Method {expected_name} has no bespoke_data"
    assert method.bespoke_data.kind == expected_kind, (
        f"Expected method {expected_name} to have kind {expected_kind}, "
        f"but got {method.bespoke_data.kind}"
    )


def test_extract_methods_fully_qualified_parent_path(
    data_structures_test_code: str,
) -> None:
    """Test that Calculator methods have the correct fully_qualified_parent_path"""
    driver_tree = RubyDriverTree.from_code(
        data_structures_test_code, "test_classes_modules.rb"
    )
    methods = driver_tree.extract_callable_definitions()

    # Filter for Calculator methods only
    calculator_methods = [m for m in methods if m.name in ["add", "subtract"]]

    for method in calculator_methods:
        assert method.fully_qualified_parent_path == "Calculator", (
            f"Expected method {method.name} to have parent path 'Calculator', "
            f"but got '{method.fully_qualified_parent_path}'"
        )


def test_extract_class_fully_qualified_parent_path(
    data_structures_test_code: str,
) -> None:
    """Test that top-level classes have empty fully_qualified_parent_path"""
    driver_tree = RubyDriverTree.from_code(
        data_structures_test_code, "test_classes_modules.rb"
    )
    classes = driver_tree.extract_data_structure_definitions()

    # Test Calculator (top-level)
    calc_class = next((c for c in classes if c.name == "Calculator"), None)
    assert calc_class is not None
    assert calc_class.fully_qualified_parent_path == "", (
        f"Expected top-level class to have empty parent path, "
        f"but got '{calc_class.fully_qualified_parent_path}'"
    )


# ========== New Comprehensive Tests for Class/Module Extraction ==========


def test_extract_class_with_inheritance(data_structures_test_code: str) -> None:
    """Test extraction of class with inheritance"""
    driver_tree = RubyDriverTree.from_code(
        data_structures_test_code, "test_classes_modules.rb"
    )
    classes = driver_tree._extract_class_and_module_definitions()

    # Find Dog class
    dog_class = next((c for c in classes if c.name == "Dog"), None)
    assert dog_class is not None, "Dog class should be extracted"

    # Should have base_class_names set
    assert dog_class.base_class_names is not None, "Dog should have base classes"
    assert len(dog_class.base_class_names) == 1
    assert "Animal" in dog_class.base_class_names

    # Should have no included/extended modules
    assert (
        dog_class.bespoke_data is None
        or dog_class.bespoke_data.included_modules is None
    )
    assert (
        dog_class.bespoke_data is None
        or dog_class.bespoke_data.extended_modules is None
    )


def test_extract_class_with_single_include(data_structures_test_code: str) -> None:
    """Test extraction of class with single include statement"""
    driver_tree = RubyDriverTree.from_code(
        data_structures_test_code, "test_classes_modules.rb"
    )
    classes = driver_tree._extract_class_and_module_definitions()

    # Find Person class
    person_class = next((c for c in classes if c.name == "Person"), None)
    assert person_class is not None, "Person class should be extracted"

    # Should have included_modules
    assert person_class.bespoke_data is not None, "Person should have bespoke data"
    assert person_class.bespoke_data.included_modules is not None
    assert len(person_class.bespoke_data.included_modules) == 1
    assert "Walkable" in person_class.bespoke_data.included_modules

    # Should have no extended modules
    assert person_class.bespoke_data.extended_modules is None

    # Should have no inheritance
    assert person_class.base_class_names is None


def test_extract_class_with_multiple_includes_one_statement(
    data_structures_test_code: str,
) -> None:
    """Test extraction of class with multiple includes in one statement"""
    driver_tree = RubyDriverTree.from_code(
        data_structures_test_code, "test_classes_modules.rb"
    )
    classes = driver_tree._extract_class_and_module_definitions()

    # Find Athlete class
    athlete_class = next((c for c in classes if c.name == "Athlete"), None)
    assert athlete_class is not None, "Athlete class should be extracted"

    # Should have all three included modules
    assert athlete_class.bespoke_data is not None
    assert athlete_class.bespoke_data.included_modules is not None
    assert len(athlete_class.bespoke_data.included_modules) == 3
    assert "Walkable" in athlete_class.bespoke_data.included_modules
    assert "Swimmable" in athlete_class.bespoke_data.included_modules
    assert "Runnable" in athlete_class.bespoke_data.included_modules


def test_extract_class_with_duplicate_includes(data_structures_test_code: str) -> None:
    """Test that duplicate includes are deduplicated"""
    driver_tree = RubyDriverTree.from_code(
        data_structures_test_code, "test_classes_modules.rb"
    )
    classes = driver_tree._extract_class_and_module_definitions()

    # Find MultiInclude class
    multi_class = next((c for c in classes if c.name == "MultiInclude"), None)
    assert multi_class is not None, "MultiInclude class should be extracted"

    # Should have only 2 unique modules (Walkable deduplicated)
    assert multi_class.bespoke_data is not None
    assert multi_class.bespoke_data.included_modules is not None
    assert len(multi_class.bespoke_data.included_modules) == 2
    assert "Walkable" in multi_class.bespoke_data.included_modules
    assert "Swimmable" in multi_class.bespoke_data.included_modules

    # Walkable should appear only once
    walkable_count = multi_class.bespoke_data.included_modules.count("Walkable")
    assert walkable_count == 1, "Walkable should be deduplicated"


def test_extract_class_with_single_extend(data_structures_test_code: str) -> None:
    """Test extraction of class with single extend statement"""
    driver_tree = RubyDriverTree.from_code(
        data_structures_test_code, "test_classes_modules.rb"
    )
    classes = driver_tree._extract_class_and_module_definitions()

    # Find WithExtend class
    with_extend_class = next((c for c in classes if c.name == "WithExtend"), None)
    assert with_extend_class is not None, "WithExtend class should be extracted"

    # Should have extended_modules
    assert with_extend_class.bespoke_data is not None
    assert with_extend_class.bespoke_data.extended_modules is not None
    assert len(with_extend_class.bespoke_data.extended_modules) == 1
    assert "ClassMethods" in with_extend_class.bespoke_data.extended_modules

    # Should have no included modules
    assert with_extend_class.bespoke_data.included_modules is None


def test_extract_class_with_multiple_extends(data_structures_test_code: str) -> None:
    """Test extraction of class with multiple extends"""
    driver_tree = RubyDriverTree.from_code(
        data_structures_test_code, "test_classes_modules.rb"
    )
    classes = driver_tree._extract_class_and_module_definitions()

    # Find Service class
    service_class = next((c for c in classes if c.name == "Service"), None)
    assert service_class is not None, "Service class should be extracted"

    # Should have both extended modules
    assert service_class.bespoke_data is not None
    assert service_class.bespoke_data.extended_modules is not None
    assert len(service_class.bespoke_data.extended_modules) == 2
    assert "Loggable" in service_class.bespoke_data.extended_modules
    assert "Configurable" in service_class.bespoke_data.extended_modules


def test_extract_class_with_include_and_extend(data_structures_test_code: str) -> None:
    """Test extraction of class with both include and extend"""
    driver_tree = RubyDriverTree.from_code(
        data_structures_test_code, "test_classes_modules.rb"
    )
    classes = driver_tree._extract_class_and_module_definitions()

    # Find FullFeatured class
    full_class = next((c for c in classes if c.name == "FullFeatured"), None)
    assert full_class is not None, "FullFeatured class should be extracted"

    # Should have both included and extended modules
    assert full_class.bespoke_data is not None
    assert full_class.bespoke_data.included_modules is not None
    assert full_class.bespoke_data.extended_modules is not None

    assert len(full_class.bespoke_data.included_modules) == 1
    assert "InstanceMethods" in full_class.bespoke_data.included_modules

    assert len(full_class.bespoke_data.extended_modules) == 1
    assert "MoreClassMethods" in full_class.bespoke_data.extended_modules


def test_extract_class_with_inheritance_include_extend(
    data_structures_test_code: str,
) -> None:
    """Test extraction of class with inheritance, include, and extend"""
    driver_tree = RubyDriverTree.from_code(
        data_structures_test_code, "test_classes_modules.rb"
    )
    classes = driver_tree._extract_class_and_module_definitions()

    # Find CompleteClass
    complete_class = next((c for c in classes if c.name == "CompleteClass"), None)
    assert complete_class is not None, "CompleteClass should be extracted"

    # Should have base class
    assert complete_class.base_class_names is not None
    assert "BaseClass" in complete_class.base_class_names

    # Should have included module
    assert complete_class.bespoke_data is not None
    assert complete_class.bespoke_data.included_modules is not None
    assert "Mixin1" in complete_class.bespoke_data.included_modules

    # Should have extended module
    assert complete_class.bespoke_data.extended_modules is not None
    assert "Mixin2" in complete_class.bespoke_data.extended_modules


def test_extract_module_definitions(data_structures_test_code: str) -> None:
    """Test that modules are extracted as well as classes"""
    driver_tree = RubyDriverTree.from_code(
        data_structures_test_code, "test_classes_modules.rb"
    )
    all_defs = driver_tree._extract_class_and_module_definitions()

    # Find MyModule
    my_module = next((m for m in all_defs if m.name == "MyModule"), None)
    assert my_module is not None, "MyModule should be extracted"

    # Check symbol kind and bespoke data
    # Modules use SymbolKind.CLASS with is_module=True in bespoke data
    from utils.lang_specialization.symbol_common import SymbolKind

    assert my_module.symbol_kind == SymbolKind.CLASS
    assert my_module.bespoke_data is not None
    assert my_module.bespoke_data.is_module is True


def test_extract_module_with_include(data_structures_test_code: str) -> None:
    """Test extraction of module with include"""
    driver_tree = RubyDriverTree.from_code(
        data_structures_test_code, "test_classes_modules.rb"
    )
    all_defs = driver_tree._extract_class_and_module_definitions()

    # Find ComposedModule
    composed_module = next((m for m in all_defs if m.name == "ComposedModule"), None)
    assert composed_module is not None, "ComposedModule should be extracted"

    # Should have included modules
    assert composed_module.bespoke_data is not None
    assert composed_module.bespoke_data.included_modules is not None
    assert "Walkable" in composed_module.bespoke_data.included_modules


def test_extract_module_with_extend(data_structures_test_code: str) -> None:
    """Test extraction of module with extend"""
    driver_tree = RubyDriverTree.from_code(
        data_structures_test_code, "test_classes_modules.rb"
    )
    all_defs = driver_tree._extract_class_and_module_definitions()

    # Find ExtendedModule
    extended_module = next((m for m in all_defs if m.name == "ExtendedModule"), None)
    assert extended_module is not None, "ExtendedModule should be extracted"

    # Should have extended modules
    assert extended_module.bespoke_data is not None
    assert extended_module.bespoke_data.extended_modules is not None
    assert "ClassMethods" in extended_module.bespoke_data.extended_modules


def test_extract_module_with_include_and_extend(
    data_structures_test_code: str,
) -> None:
    """Test extraction of module with both include and extend"""
    driver_tree = RubyDriverTree.from_code(
        data_structures_test_code, "test_classes_modules.rb"
    )
    all_defs = driver_tree._extract_class_and_module_definitions()

    # Find FullModule
    full_module = next((m for m in all_defs if m.name == "FullModule"), None)
    assert full_module is not None, "FullModule should be extracted"

    # Should have both
    assert full_module.bespoke_data is not None
    assert full_module.bespoke_data.included_modules is not None
    assert "Mixin1" in full_module.bespoke_data.included_modules
    assert full_module.bespoke_data.extended_modules is not None
    assert "Mixin2" in full_module.bespoke_data.extended_modules


def test_extract_class_with_single_prepend(data_structures_test_code: str) -> None:
    """Test extraction of class with single prepend"""
    driver_tree = RubyDriverTree.from_code(
        data_structures_test_code, "test_classes_modules.rb"
    )
    all_defs = driver_tree._extract_class_and_module_definitions()

    # Find PrependSingle class
    prepend_single = next((c for c in all_defs if c.name == "PrependSingle"), None)
    assert prepend_single is not None, "PrependSingle class should be extracted"

    # Should have prepended modules
    assert prepend_single.bespoke_data is not None
    assert prepend_single.bespoke_data.prepended_modules is not None
    assert len(prepend_single.bespoke_data.prepended_modules) == 1
    assert prepend_single.bespoke_data.prepended_modules[0] == "Prependable"


def test_extract_class_with_multiple_prepends(data_structures_test_code: str) -> None:
    """Test extraction of class with multiple prepends in one statement"""
    driver_tree = RubyDriverTree.from_code(
        data_structures_test_code, "test_classes_modules.rb"
    )
    all_defs = driver_tree._extract_class_and_module_definitions()

    # Find PrependMultiple class
    prepend_multiple = next((c for c in all_defs if c.name == "PrependMultiple"), None)
    assert prepend_multiple is not None, "PrependMultiple class should be extracted"

    # Should have both modules in order
    assert prepend_multiple.bespoke_data is not None
    assert prepend_multiple.bespoke_data.prepended_modules is not None
    assert len(prepend_multiple.bespoke_data.prepended_modules) == 2
    assert prepend_multiple.bespoke_data.prepended_modules[0] == "PrependA"
    assert prepend_multiple.bespoke_data.prepended_modules[1] == "PrependB"


def test_extract_class_with_prepend_deduplication(
    data_structures_test_code: str,
) -> None:
    """Test that duplicate prepend statements are deduplicated"""
    driver_tree = RubyDriverTree.from_code(
        data_structures_test_code, "test_classes_modules.rb"
    )
    all_defs = driver_tree._extract_class_and_module_definitions()

    # Find PrependDeduplicate class
    prepend_dedup = next((c for c in all_defs if c.name == "PrependDeduplicate"), None)
    assert prepend_dedup is not None, "PrependDeduplicate class should be extracted"

    # Should have both modules but PrependA only once (dedup)
    assert prepend_dedup.bespoke_data is not None
    assert prepend_dedup.bespoke_data.prepended_modules is not None
    assert len(prepend_dedup.bespoke_data.prepended_modules) == 2
    assert prepend_dedup.bespoke_data.prepended_modules[0] == "PrependA"
    assert prepend_dedup.bespoke_data.prepended_modules[1] == "PrependB"


def test_extract_class_with_include_extend_prepend(
    data_structures_test_code: str,
) -> None:
    """Test extraction of class with include, extend, and prepend"""
    driver_tree = RubyDriverTree.from_code(
        data_structures_test_code, "test_classes_modules.rb"
    )
    all_defs = driver_tree._extract_class_and_module_definitions()

    # Find MixedMixins class
    mixed = next((c for c in all_defs if c.name == "MixedMixins"), None)
    assert mixed is not None, "MixedMixins class should be extracted"

    # Should have all three types
    assert mixed.bespoke_data is not None
    assert mixed.bespoke_data.included_modules is not None
    assert "Walkable" in mixed.bespoke_data.included_modules
    assert mixed.bespoke_data.extended_modules is not None
    assert "ClassMethods" in mixed.bespoke_data.extended_modules
    assert mixed.bespoke_data.prepended_modules is not None
    assert "Prependable" in mixed.bespoke_data.prepended_modules


def test_extract_module_with_prepend(data_structures_test_code: str) -> None:
    """Test extraction of module with prepend"""
    driver_tree = RubyDriverTree.from_code(
        data_structures_test_code, "test_classes_modules.rb"
    )
    all_defs = driver_tree._extract_class_and_module_definitions()

    # Find ModuleWithPrepend
    module_prepend = next((m for m in all_defs if m.name == "ModuleWithPrepend"), None)
    assert module_prepend is not None, "ModuleWithPrepend should be extracted"

    # Should have prepend
    assert module_prepend.bespoke_data is not None
    assert module_prepend.bespoke_data.prepended_modules is not None
    assert "PrependA" in module_prepend.bespoke_data.prepended_modules


def test_extract_nested_class_with_prepend(data_structures_test_code: str) -> None:
    """Test extraction of nested classes with prepend"""
    driver_tree = RubyDriverTree.from_code(
        data_structures_test_code, "test_classes_modules.rb"
    )
    all_defs = driver_tree._extract_class_and_module_definitions()

    # Find OuterPrepend and InnerPrepend
    outer = next((c for c in all_defs if c.name == "OuterPrepend"), None)
    inner = next((c for c in all_defs if c.name == "InnerPrepend"), None)

    assert outer is not None
    assert outer.bespoke_data.prepended_modules is not None
    assert "PrependA" in outer.bespoke_data.prepended_modules

    assert inner is not None
    assert inner.bespoke_data.prepended_modules is not None
    assert "PrependB" in inner.bespoke_data.prepended_modules


def test_extract_class_with_namespaced_prepend(data_structures_test_code: str) -> None:
    """Test extraction of class with namespaced prepend"""
    driver_tree = RubyDriverTree.from_code(
        data_structures_test_code, "test_classes_modules.rb"
    )
    all_defs = driver_tree._extract_class_and_module_definitions()

    # Find NamespacedPrepend class
    namespaced = next((c for c in all_defs if c.name == "NamespacedPrepend"), None)
    assert namespaced is not None, "NamespacedPrepend class should be extracted"

    # Should have namespaced prepend
    assert namespaced.bespoke_data is not None
    assert namespaced.bespoke_data.prepended_modules is not None
    assert "Namespaced::PrependModule" in namespaced.bespoke_data.prepended_modules


def test_extract_nested_class(data_structures_test_code: str) -> None:
    """Test extraction of nested class with correct FQP"""
    driver_tree = RubyDriverTree.from_code(
        data_structures_test_code, "test_classes_modules.rb"
    )
    all_defs = driver_tree._extract_class_and_module_definitions()

    # Find Inner class
    inner_class = next((c for c in all_defs if c.name == "Inner"), None)
    assert inner_class is not None, "Inner class should be extracted"

    # Should have Outer as parent
    assert inner_class.fully_qualified_parent_path == "Outer"


def test_extract_nested_module(data_structures_test_code: str) -> None:
    """Test extraction of nested module with correct FQP"""
    driver_tree = RubyDriverTree.from_code(
        data_structures_test_code, "test_classes_modules.rb"
    )
    all_defs = driver_tree._extract_class_and_module_definitions()

    # Find InnerModule
    inner_module = next((m for m in all_defs if m.name == "InnerModule"), None)
    assert inner_module is not None, "InnerModule should be extracted"

    # Should have OuterModule as parent
    assert inner_module.fully_qualified_parent_path == "OuterModule"


def test_extract_class_inside_module(data_structures_test_code: str) -> None:
    """Test extraction of class inside module"""
    driver_tree = RubyDriverTree.from_code(
        data_structures_test_code, "test_classes_modules.rb"
    )
    all_defs = driver_tree._extract_class_and_module_definitions()

    # Find NamespacedClass
    namespaced_class = next((c for c in all_defs if c.name == "NamespacedClass"), None)
    assert namespaced_class is not None, "NamespacedClass should be extracted"

    # Should have Namespace as parent
    assert namespaced_class.fully_qualified_parent_path == "Namespace"


def test_extract_namespaced_includes(data_structures_test_code: str) -> None:
    """Test that namespaced includes are preserved with :: notation"""
    driver_tree = RubyDriverTree.from_code(
        data_structures_test_code, "test_classes_modules.rb"
    )
    all_defs = driver_tree._extract_class_and_module_definitions()

    # Find WithNamespacedMixins
    namespaced_mixins = next(
        (c for c in all_defs if c.name == "WithNamespacedMixins"), None
    )
    assert namespaced_mixins is not None, "WithNamespacedMixins should be extracted"

    # Should preserve namespace notation
    assert namespaced_mixins.bespoke_data is not None
    assert namespaced_mixins.bespoke_data.included_modules is not None
    assert "ActiveSupport::Concern" in namespaced_mixins.bespoke_data.included_modules


def test_extract_empty_class(data_structures_test_code: str) -> None:
    """Test extraction of empty class"""
    driver_tree = RubyDriverTree.from_code(
        data_structures_test_code, "test_classes_modules.rb"
    )
    all_defs = driver_tree._extract_class_and_module_definitions()

    # Find Empty class
    empty_class = next((c for c in all_defs if c.name == "Empty"), None)
    assert empty_class is not None, "Empty class should be extracted"

    # Should have no mixins or inheritance
    assert empty_class.base_class_names is None
    assert empty_class.bespoke_data is None or (
        empty_class.bespoke_data.included_modules is None
        and empty_class.bespoke_data.extended_modules is None
    )


def test_extract_empty_module(data_structures_test_code: str) -> None:
    """Test extraction of empty module"""
    driver_tree = RubyDriverTree.from_code(
        data_structures_test_code, "test_classes_modules.rb"
    )
    all_defs = driver_tree._extract_class_and_module_definitions()

    # Find EmptyModule
    empty_module = next((m for m in all_defs if m.name == "EmptyModule"), None)
    assert empty_module is not None, "EmptyModule should be extracted"

    # Should have no mixins
    assert empty_module.bespoke_data is None or (
        empty_module.bespoke_data.included_modules is None
        and empty_module.bespoke_data.extended_modules is None
    )


def test_module_order_preserved(data_structures_test_code: str) -> None:
    """Test that order of included/extended modules is preserved"""
    driver_tree = RubyDriverTree.from_code(
        data_structures_test_code, "test_classes_modules.rb"
    )
    all_defs = driver_tree._extract_class_and_module_definitions()

    # Find Athlete class (includes Walkable, Swimmable, Runnable in that order)
    athlete_class = next((c for c in all_defs if c.name == "Athlete"), None)
    assert athlete_class is not None

    # Order should be preserved
    included = athlete_class.bespoke_data.included_modules
    assert included[0] == "Walkable"
    assert included[1] == "Swimmable"
    assert included[2] == "Runnable"


# Comprehensive tests for extract_callable_definitions


@pytest.fixture(scope="module")
def callables_test_code() -> str:
    file_path = (
        pathlib.Path(__file__).parent
        / "treesitter_testcases"
        / "ruby"
        / "test_callables.rb"
    )
    with open(file_path, encoding="utf-8") as f:
        return f.read()


def test_extract_top_level_methods(callables_test_code: str) -> None:
    """Test extraction of methods defined at the top level (outside any class/module)"""
    driver_tree = RubyDriverTree.from_code(callables_test_code, "test_callables.rb")
    methods = driver_tree.extract_callable_definitions()

    # Find top-level methods
    top_level_methods = [
        m for m in methods if m.bespoke_data.kind == RubyMethodKind.TOP_LEVEL
    ]

    # Should have at least the two defined at the top
    assert len(top_level_methods) >= 2

    # Check specific top-level methods
    top_level_method = next(
        (m for m in top_level_methods if m.name == "top_level_method"), None
    )
    another_top_level = next(
        (m for m in top_level_methods if m.name == "another_top_level"), None
    )

    assert top_level_method is not None
    assert another_top_level is not None

    for method in [top_level_method, another_top_level]:
        assert method.bespoke_data is not None
        assert method.bespoke_data.kind == RubyMethodKind.TOP_LEVEL
        assert method.fully_qualified_parent_path == ""
        assert method.bespoke_data.visibility is None


def test_extract_instance_methods_in_class(callables_test_code: str) -> None:
    """Test extraction of instance methods in a class"""
    driver_tree = RubyDriverTree.from_code(callables_test_code, "test_callables.rb")
    methods = driver_tree.extract_callable_definitions()

    # Find methods from MyClass
    my_class_methods = [
        m
        for m in methods
        if m.fully_qualified_parent_path == "MyClass"
        and m.bespoke_data.kind == RubyMethodKind.INSTANCE_METHOD
    ]

    assert len(my_class_methods) == 2

    method_names = {m.name for m in my_class_methods}
    assert method_names == {"instance_method_one", "instance_method_two"}

    for method in my_class_methods:
        assert method.bespoke_data is not None
        assert method.bespoke_data.kind == RubyMethodKind.INSTANCE_METHOD
        assert method.fully_qualified_parent_path == "MyClass"


def test_extract_class_methods_with_self(callables_test_code: str) -> None:
    """Test extraction of class methods defined with def self.method_name"""
    driver_tree = RubyDriverTree.from_code(callables_test_code, "test_callables.rb")
    methods = driver_tree.extract_callable_definitions()

    # Find methods from ClassWithClassMethods
    class_methods = [
        m
        for m in methods
        if m.fully_qualified_parent_path == "ClassWithClassMethods"
        and m.bespoke_data.kind == RubyMethodKind.CLASS_METHOD
    ]

    assert len(class_methods) == 2

    method_names = {m.name for m in class_methods}
    assert method_names == {"class_method_one", "class_method_two"}

    for method in class_methods:
        assert method.bespoke_data is not None
        assert method.bespoke_data.kind == RubyMethodKind.CLASS_METHOD
        assert method.fully_qualified_parent_path == "ClassWithClassMethods"


def test_extract_mixed_instance_and_class_methods(callables_test_code: str) -> None:
    """Test extraction of both instance and class methods in the same class"""
    driver_tree = RubyDriverTree.from_code(callables_test_code, "test_callables.rb")
    methods = driver_tree.extract_callable_definitions()

    # Find methods from Calculator class
    calculator_methods = [
        m for m in methods if m.fully_qualified_parent_path == "Calculator"
    ]

    assert len(calculator_methods) == 4

    instance_methods = [
        m
        for m in calculator_methods
        if m.bespoke_data.kind == RubyMethodKind.INSTANCE_METHOD
    ]
    class_methods = [
        m
        for m in calculator_methods
        if m.bespoke_data.kind == RubyMethodKind.CLASS_METHOD
    ]

    assert len(instance_methods) == 2
    assert len(class_methods) == 2

    assert {m.name for m in instance_methods} == {"add", "subtract"}
    assert {m.name for m in class_methods} == {"version", "author"}


def test_extract_methods_with_private_keyword(callables_test_code: str) -> None:
    """Test that methods after 'private' keyword have private visibility"""
    driver_tree = RubyDriverTree.from_code(callables_test_code, "test_callables.rb")
    methods = driver_tree.extract_callable_definitions()

    # Find methods from WithPrivateKeyword class
    class_methods = [
        m for m in methods if m.fully_qualified_parent_path == "WithPrivateKeyword"
    ]

    assert len(class_methods) == 3

    public_method = next(m for m in class_methods if m.name == "public_method")
    private_one = next(m for m in class_methods if m.name == "private_method_one")
    private_two = next(m for m in class_methods if m.name == "private_method_two")

    # Validate visibility
    assert (
        public_method.bespoke_data.visibility is None
    )  # Default is public, but not explicitly set
    assert private_one.bespoke_data.visibility == "private"
    assert private_two.bespoke_data.visibility == "private"

    # Validate fully_qualified_parent_path
    assert public_method.fully_qualified_parent_path == "WithPrivateKeyword"
    assert private_one.fully_qualified_parent_path == "WithPrivateKeyword"
    assert private_two.fully_qualified_parent_path == "WithPrivateKeyword"


def test_extract_methods_with_protected_keyword(callables_test_code: str) -> None:
    """Test that methods after 'protected' keyword have protected visibility"""
    driver_tree = RubyDriverTree.from_code(callables_test_code, "test_callables.rb")
    methods = driver_tree.extract_callable_definitions()

    # Find methods from WithProtectedKeyword class
    class_methods = [
        m for m in methods if m.fully_qualified_parent_path == "WithProtectedKeyword"
    ]

    assert len(class_methods) == 2

    public_method = next(m for m in class_methods if m.name == "public_method")
    protected_method = next(m for m in class_methods if m.name == "protected_method")

    # Validate visibility
    assert public_method.bespoke_data.visibility is None
    assert protected_method.bespoke_data.visibility == "protected"

    # Validate fully_qualified_parent_path
    assert public_method.fully_qualified_parent_path == "WithProtectedKeyword"
    assert protected_method.fully_qualified_parent_path == "WithProtectedKeyword"


def test_extract_methods_with_explicit_public_keyword(callables_test_code: str) -> None:
    """Test that methods after explicit 'public' keyword have public visibility"""
    driver_tree = RubyDriverTree.from_code(callables_test_code, "test_callables.rb")
    methods = driver_tree.extract_callable_definitions()

    # Find methods from WithExplicitPublic class
    class_methods = [
        m for m in methods if m.fully_qualified_parent_path == "WithExplicitPublic"
    ]

    assert len(class_methods) == 2

    private_method = next(m for m in class_methods if m.name == "private_method")
    public_method = next(
        m for m in class_methods if m.name == "explicitly_public_method"
    )

    # Validate visibility
    assert private_method.bespoke_data.visibility == "private"
    assert public_method.bespoke_data.visibility == "public"

    # Validate fully_qualified_parent_path
    assert private_method.fully_qualified_parent_path == "WithExplicitPublic"
    assert public_method.fully_qualified_parent_path == "WithExplicitPublic"


def test_extract_methods_with_inline_visibility(callables_test_code: str) -> None:
    """Test methods with inline visibility modifiers like 'private def method_name'"""
    driver_tree = RubyDriverTree.from_code(callables_test_code, "test_callables.rb")
    methods = driver_tree.extract_callable_definitions()

    # Find methods from WithInlineVisibility class
    class_methods = [
        m for m in methods if m.fully_qualified_parent_path == "WithInlineVisibility"
    ]

    assert len(class_methods) == 3

    private_method = next(m for m in class_methods if m.name == "inline_private")
    protected_method = next(m for m in class_methods if m.name == "inline_protected")
    public_method = next(m for m in class_methods if m.name == "inline_public")

    # Validate visibility
    assert private_method.bespoke_data.visibility == "private"
    assert protected_method.bespoke_data.visibility == "protected"
    assert public_method.bespoke_data.visibility == "public"

    # Validate fully_qualified_parent_path
    assert private_method.fully_qualified_parent_path == "WithInlineVisibility"
    assert protected_method.fully_qualified_parent_path == "WithInlineVisibility"
    assert public_method.fully_qualified_parent_path == "WithInlineVisibility"


def test_extract_methods_in_nested_class(callables_test_code: str) -> None:
    """Test extraction of methods in nested classes"""
    driver_tree = RubyDriverTree.from_code(callables_test_code, "test_callables.rb")
    methods = driver_tree.extract_callable_definitions()

    outer_method = next((m for m in methods if m.name == "outer_method"), None)
    inner_method = next((m for m in methods if m.name == "inner_method"), None)

    assert outer_method is not None
    assert inner_method is not None

    assert outer_method.fully_qualified_parent_path == "MyModule::OuterClass"
    assert (
        inner_method.fully_qualified_parent_path == "MyModule::OuterClass::InnerClass"
    )


def test_extract_methods_mixed_contexts(callables_test_code: str) -> None:
    """Test extraction of methods in mixed contexts: top-level, class, and nested"""
    driver_tree = RubyDriverTree.from_code(callables_test_code, "test_callables.rb")
    methods = driver_tree.extract_callable_definitions()

    # Find specific methods from different contexts
    top_level_helper = next((m for m in methods if m.name == "top_level_helper"), None)
    another_helper = next((m for m in methods if m.name == "another_helper"), None)
    first_instance = next((m for m in methods if m.name == "first_instance"), None)
    first_class_method = next(
        (m for m in methods if m.name == "first_class_method"), None
    )
    second_instance = next((m for m in methods if m.name == "second_instance"), None)

    assert top_level_helper is not None
    assert another_helper is not None
    assert first_instance is not None
    assert first_class_method is not None
    assert second_instance is not None

    # Check top-level methods
    assert top_level_helper.bespoke_data.kind == RubyMethodKind.TOP_LEVEL
    assert top_level_helper.fully_qualified_parent_path == ""
    assert another_helper.bespoke_data.kind == RubyMethodKind.TOP_LEVEL
    assert another_helper.fully_qualified_parent_path == ""

    # Check class methods
    assert first_instance.bespoke_data.kind == RubyMethodKind.INSTANCE_METHOD
    assert first_instance.fully_qualified_parent_path == "FirstClass"
    assert first_class_method.bespoke_data.kind == RubyMethodKind.CLASS_METHOD
    assert first_class_method.fully_qualified_parent_path == "FirstClass"

    # Check nested methods
    assert second_instance.bespoke_data.kind == RubyMethodKind.INSTANCE_METHOD
    assert second_instance.fully_qualified_parent_path == "AnotherModule::SecondClass"


def test_extract_callables_from_empty_class(callables_test_code: str) -> None:
    """Test that extracting from a class with no methods works correctly"""
    driver_tree = RubyDriverTree.from_code(callables_test_code, "test_callables.rb")
    methods = driver_tree.extract_callable_definitions()

    # EmptyClass should have no methods extracted
    empty_class_methods = [
        m for m in methods if m.fully_qualified_parent_path == "EmptyClass"
    ]

    assert len(empty_class_methods) == 0


def test_extract_only_private_methods(callables_test_code: str) -> None:
    """Test extraction of a class with only private methods"""
    driver_tree = RubyDriverTree.from_code(callables_test_code, "test_callables.rb")
    methods = driver_tree.extract_callable_definitions()

    # Find methods from OnlyPrivate class
    only_private_methods = [
        m for m in methods if m.fully_qualified_parent_path == "OnlyPrivate"
    ]

    assert len(only_private_methods) == 2

    for method in only_private_methods:
        # Validate visibility
        assert method.bespoke_data.visibility == "private"
        # Validate fully_qualified_parent_path
        assert method.fully_qualified_parent_path == "OnlyPrivate"


def test_extract_visibility_changes_within_class(callables_test_code: str) -> None:
    """Test multiple visibility changes within a class"""
    driver_tree = RubyDriverTree.from_code(callables_test_code, "test_callables.rb")
    methods = driver_tree.extract_callable_definitions()

    # Find methods from VisibilityChanges class
    visibility_methods = [
        m for m in methods if m.fully_qualified_parent_path == "VisibilityChanges"
    ]

    assert len(visibility_methods) == 5

    starts_public = next(m for m in visibility_methods if m.name == "starts_public")
    goes_private = next(m for m in visibility_methods if m.name == "goes_private")
    then_protected = next(m for m in visibility_methods if m.name == "then_protected")
    back_to_public = next(m for m in visibility_methods if m.name == "back_to_public")
    ends_private = next(m for m in visibility_methods if m.name == "ends_private")

    # Validate visibility
    assert starts_public.bespoke_data.visibility is None
    assert goes_private.bespoke_data.visibility == "private"
    assert then_protected.bespoke_data.visibility == "protected"
    assert back_to_public.bespoke_data.visibility == "public"
    assert ends_private.bespoke_data.visibility == "private"

    # Validate fully_qualified_parent_path for all methods
    for method in visibility_methods:
        assert method.fully_qualified_parent_path == "VisibilityChanges"


def test_extract_methods_in_module(callables_test_code: str) -> None:
    """Test extraction of methods defined directly in a module"""
    driver_tree = RubyDriverTree.from_code(callables_test_code, "test_callables.rb")
    methods = driver_tree.extract_callable_definitions()

    # Find methods from Utilities module
    utilities_methods = [
        m for m in methods if m.fully_qualified_parent_path == "Utilities"
    ]

    assert len(utilities_methods) == 2

    for method in utilities_methods:
        assert method.fully_qualified_parent_path == "Utilities"


def test_extract_methods_with_parameters(callables_test_code: str) -> None:
    """Test extraction of methods with various parameter patterns"""
    driver_tree = RubyDriverTree.from_code(callables_test_code, "test_callables.rb")
    methods = driver_tree.extract_callable_definitions()

    # Find methods from ParameterTest class
    parameter_test_methods = [
        m for m in methods if m.fully_qualified_parent_path == "ParameterTest"
    ]

    # Should extract all methods regardless of parameter complexity
    assert len(parameter_test_methods) == 7

    expected_names = {
        "no_params",
        "single_param",
        "multiple_params",
        "default_params",
        "keyword_params",
        "splat_params",
        "block_param",
    }
    actual_names = {m.name for m in parameter_test_methods}

    assert actual_names == expected_names

    # Validate fully_qualified_parent_path for all methods
    for method in parameter_test_methods:
        assert method.fully_qualified_parent_path == "ParameterTest"


# =============================================================================
# Tests for extract_variables()
# =============================================================================


@pytest.fixture(scope="module")
def variables_test_code() -> str:
    file_path = (
        pathlib.Path(__file__).parent
        / "treesitter_testcases"
        / "ruby"
        / "test_variables.rb"
    )
    with open(file_path, encoding="utf-8") as f:
        return f.read()


def test_extract_variables_count(variables_test_code: str) -> None:
    """Test that we extract the correct total number of variables"""

    driver_tree = RubyDriverTree.from_code(variables_test_code, "test_variables.rb")
    variables = driver_tree._extract_variables_and_constants()

    # Count from test_variables.rb:
    # - Top-level: 3 constants + 2 globals + 1 instance var = 6
    # - SimpleClass: 1 constant + 1 class var + 6 instance vars (deduplicated) = 8
    # - MyModule: 2 constants + 1 module instance var + 1 instance var = 4
    # - OuterClass: 1 constant + 1 class var + 1 instance var = 3
    # - OuterClass::InnerClass: 1 constant + 1 class var + 2 instance vars = 4
    # - NamespacedConstants: 5 constants = 5
    # - VariableSpread: 1 instance var in initialize + 3 in methods (deduplicated @var_a) = 4
    # - ParallelAssignment: 4 instance vars = 4
    # - Globals in function/class: 2 globals = 2
    # - OnlyConstants: 2 constants = 2
    # - OnlyClassVariables: 2 class vars = 2
    # - OnlyInstanceVariables: 3 instance vars = 3
    # - EmptyClass: 0 = 0
    # - ClassWithNestedModule: 1 constant + NestedModule(1 constant + 1 instance var) = 3
    # - SimilarNames: 3 class vars + 3 instance vars = 6
    # - UnicodeVariables: 1 constant + 1 instance var = 2
    # - ConstantTypes: 13 constants = 13
    # - ReopenedClass (both): 2 constants + 2 instance vars = 4
    # - SingletonExample: 1 constant + 2 singleton vars + 1 instance var = 4
    # Total = 80
    assert len(variables) >= 70, f"Expected at least 70 variables, got {len(variables)}"


def test_extract_top_level_constants(variables_test_code: str) -> None:
    """Test extraction of top-level constants"""
    from .ruby_driver import RubyVariableKind

    driver_tree = RubyDriverTree.from_code(variables_test_code, "test_variables.rb")
    variables = driver_tree._extract_variables_and_constants()

    # Filter for top-level constants
    top_level_constants = [
        v
        for v in variables
        if v.bespoke_data.kind == RubyVariableKind.CONSTANT
        and v.bespoke_data.is_top_level
        and v.fully_qualified_parent_path == ""
    ]

    assert len(top_level_constants) >= 2

    constant_names = {v.name for v in top_level_constants}
    assert "TOP_LEVEL_CONSTANT" in constant_names
    assert "ANOTHER_TOP_LEVEL" in constant_names


def test_extract_top_level_globals(variables_test_code: str) -> None:
    """Test extraction of global variables"""

    driver_tree = RubyDriverTree.from_code(variables_test_code, "test_variables.rb")
    variables = driver_tree._extract_variables_and_constants()

    # Filter for global variables
    globals_vars = [v for v in variables if v.name.startswith("$")]

    # Should have at least 4: $global_config, $global_counter, $global_in_function, $global_in_class_method
    assert len(globals_vars) >= 4

    global_names = {v.name for v in globals_vars}
    assert "$global_config" in global_names
    assert "$global_counter" in global_names
    assert "$global_in_function" in global_names
    assert "$global_in_class_method" in global_names


def test_extract_class_constants(variables_test_code: str) -> None:
    """Test extraction of constants within classes"""
    from .ruby_driver import RubyVariableKind

    driver_tree = RubyDriverTree.from_code(variables_test_code, "test_variables.rb")
    variables = driver_tree._extract_variables_and_constants()

    # Filter for SimpleClass constants
    simple_class_constants = [
        v
        for v in variables
        if v.fully_qualified_parent_path == "SimpleClass"
        and v.bespoke_data.kind == RubyVariableKind.CONSTANT
    ]

    assert len(simple_class_constants) == 1
    assert simple_class_constants[0].name == "MAX_SIZE"
    assert simple_class_constants[0].bespoke_data.is_top_level is False


def test_extract_class_variables(variables_test_code: str) -> None:
    """Test extraction of class variables (@@var)"""
    driver_tree = RubyDriverTree.from_code(variables_test_code, "test_variables.rb")
    variables = driver_tree._extract_variables_and_constants()

    # Filter for SimpleClass class variables
    simple_class_vars = [
        v
        for v in variables
        if v.fully_qualified_parent_path == "SimpleClass" and v.name.startswith("@@")
    ]

    assert len(simple_class_vars) == 1
    assert simple_class_vars[0].name == "@@class_counter"
    assert simple_class_vars[0].bespoke_data.is_top_level is False


def test_extract_instance_variables(variables_test_code: str) -> None:
    """Test extraction of instance variables (@var)"""
    driver_tree = RubyDriverTree.from_code(variables_test_code, "test_variables.rb")
    variables = driver_tree._extract_variables_and_constants()

    # Filter for SimpleClass instance variables
    simple_instance_vars = [
        v
        for v in variables
        if v.fully_qualified_parent_path == "SimpleClass"
        and v.name.startswith("@")
        and not v.name.startswith("@@")
    ]

    # Should have: @name, @age, @created_at, @status, @result
    # (@name appears in multiple methods but should be deduplicated)
    assert len(simple_instance_vars) == 5

    instance_var_names = {v.name for v in simple_instance_vars}
    assert "@name" in instance_var_names
    assert "@age" in instance_var_names
    assert "@created_at" in instance_var_names
    assert "@status" in instance_var_names
    assert "@result" in instance_var_names


def test_extract_instance_variables_deduplication(variables_test_code: str) -> None:
    """Test that duplicate instance variables in different methods are deduplicated"""
    driver_tree = RubyDriverTree.from_code(variables_test_code, "test_variables.rb")
    variables = driver_tree._extract_variables_and_constants()

    # Filter for VariableSpread class
    variable_spread_vars = [
        v
        for v in variables
        if v.fully_qualified_parent_path == "VariableSpread" and v.name.startswith("@")
    ]

    # Should have: @id, @var_a, @var_b, @var_c
    # (@var_a appears in method_a and method_c but should only be extracted once)
    assert len(variable_spread_vars) == 4

    var_names = {v.name for v in variable_spread_vars}
    assert "@id" in var_names
    assert "@var_a" in var_names
    assert "@var_b" in var_names
    assert "@var_c" in var_names


def test_extract_module_variables(variables_test_code: str) -> None:
    """Test extraction of variables within modules"""

    driver_tree = RubyDriverTree.from_code(variables_test_code, "test_variables.rb")
    variables = driver_tree._extract_variables_and_constants()

    # Filter for MyModule variables
    module_vars = [v for v in variables if v.fully_qualified_parent_path == "MyModule"]

    # Should have: VERSION, CONFIG_KEY (constants), @module_instance_var, @instance_var_in_module
    assert len(module_vars) == 4

    var_names = {v.name for v in module_vars}
    assert "VERSION" in var_names
    assert "CONFIG_KEY" in var_names
    assert "@module_instance_var" in var_names
    assert "@instance_var_in_module" in var_names


def test_extract_nested_class_variables(variables_test_code: str) -> None:
    """Test extraction of variables in nested classes"""
    driver_tree = RubyDriverTree.from_code(variables_test_code, "test_variables.rb")
    variables = driver_tree._extract_variables_and_constants()

    # Filter for OuterClass variables
    outer_vars = [v for v in variables if v.fully_qualified_parent_path == "OuterClass"]

    # Should have: OUTER_CONSTANT, @@outer_class_var, @outer_instance
    assert len(outer_vars) == 3

    # Filter for InnerClass variables
    inner_vars = [
        v
        for v in variables
        if v.fully_qualified_parent_path == "OuterClass::InnerClass"
    ]

    # Should have: INNER_CONSTANT, @@inner_class_var, @inner_instance, @another_inner
    assert len(inner_vars) == 4

    inner_var_names = {v.name for v in inner_vars}
    assert "INNER_CONSTANT" in inner_var_names
    assert "@@inner_class_var" in inner_var_names
    assert "@inner_instance" in inner_var_names
    assert "@another_inner" in inner_var_names


def test_extract_variables_fqp(variables_test_code: str) -> None:
    """Test that fully_qualified_parent_path is correct for all variables"""
    driver_tree = RubyDriverTree.from_code(variables_test_code, "test_variables.rb")
    variables = driver_tree._extract_variables_and_constants()

    # Check specific variables and their FQP
    fqp_map = {v.name: v.fully_qualified_parent_path for v in variables}

    # Top-level variables
    assert fqp_map.get("TOP_LEVEL_CONSTANT") == ""
    assert fqp_map.get("$global_config") == ""

    # Class variables
    assert fqp_map.get("MAX_SIZE") == "SimpleClass"

    # Nested class variables
    assert "OuterClass::InnerClass" in [
        v.fully_qualified_parent_path for v in variables if v.name == "INNER_CONSTANT"
    ]


def test_extract_parallel_assignment_variables(variables_test_code: str) -> None:
    """Test extraction of variables from parallel assignment"""
    driver_tree = RubyDriverTree.from_code(variables_test_code, "test_variables.rb")
    variables = driver_tree._extract_variables_and_constants()

    # Filter for ParallelAssignment class
    parallel_vars = [
        v for v in variables if v.fully_qualified_parent_path == "ParallelAssignment"
    ]

    # Should extract all 4 variables: @x, @y, @width, @height
    assert len(parallel_vars) == 4

    var_names = {v.name for v in parallel_vars}
    assert "@x" in var_names
    assert "@y" in var_names
    assert "@width" in var_names
    assert "@height" in var_names


def test_extract_variables_excludes_locals(variables_test_code: str) -> None:
    """Test that local variables are NOT extracted"""
    driver_tree = RubyDriverTree.from_code(variables_test_code, "test_variables.rb")
    variables = driver_tree._extract_variables_and_constants()

    # Verify no lowercase local variables are extracted
    local_var_names = ["local_var", "temp", "local", "x"]
    extracted_names = {v.name for v in variables}

    for local_name in local_var_names:
        assert (
            local_name not in extracted_names
        ), f"Local variable '{local_name}' should not be extracted"


def test_extract_empty_class_variables(variables_test_code: str) -> None:
    """Test that empty classes have no variables"""
    driver_tree = RubyDriverTree.from_code(variables_test_code, "test_variables.rb")
    variables = driver_tree._extract_variables_and_constants()

    # Filter for EmptyClass
    empty_class_vars = [
        v for v in variables if v.fully_qualified_parent_path == "EmptyClass"
    ]

    assert len(empty_class_vars) == 0


def test_extract_constant_types(variables_test_code: str) -> None:
    """Test extraction of constants with different value types"""
    from .ruby_driver import RubyVariableKind

    driver_tree = RubyDriverTree.from_code(variables_test_code, "test_variables.rb")
    variables = driver_tree._extract_variables_and_constants()

    # Filter for ConstantTypes class
    constant_types_vars = [
        v
        for v in variables
        if v.fully_qualified_parent_path == "ConstantTypes"
        and v.bespoke_data.kind == RubyVariableKind.CONSTANT
    ]

    # Should have many constants with different types
    assert len(constant_types_vars) >= 10

    constant_names = {v.name for v in constant_types_vars}
    assert "NIL_CONSTANT" in constant_names
    assert "BOOL_TRUE" in constant_names
    assert "INTEGER" in constant_names
    assert "STRING" in constant_names
    assert "ARRAY" in constant_names
    assert "HASH" in constant_names


def test_extract_unicode_variables(variables_test_code: str) -> None:
    """Test extraction of variables with unicode characters"""
    driver_tree = RubyDriverTree.from_code(variables_test_code, "test_variables.rb")
    variables = driver_tree._extract_variables_and_constants()

    # Filter for UnicodeVariables class
    unicode_vars = [
        v for v in variables if v.fully_qualified_parent_path == "UnicodeVariables"
    ]

    assert len(unicode_vars) == 2

    var_names = {v.name for v in unicode_vars}
    assert "CAFÉ" in var_names
    assert "@naïve" in var_names


def test_extract_reopened_class_variables(variables_test_code: str) -> None:
    """Test extraction of variables from reopened classes"""
    driver_tree = RubyDriverTree.from_code(variables_test_code, "test_variables.rb")
    variables = driver_tree._extract_variables_and_constants()

    # Filter for ReopenedClass (both definitions should be captured)
    reopened_vars = [
        v for v in variables if v.fully_qualified_parent_path == "ReopenedClass"
    ]

    # Should have variables from both class definitions
    # FIRST_CONSTANT, SECOND_CONSTANT, @first_var, @second_var
    assert len(reopened_vars) == 4

    var_names = {v.name for v in reopened_vars}
    assert "FIRST_CONSTANT" in var_names
    assert "SECOND_CONSTANT" in var_names
    assert "@first_var" in var_names
    assert "@second_var" in var_names


def test_extract_singleton_class_variables(variables_test_code: str) -> None:
    """Test extraction of variables in singleton classes (class << self)"""
    driver_tree = RubyDriverTree.from_code(variables_test_code, "test_variables.rb")
    variables = driver_tree._extract_variables_and_constants()

    # Filter for SingletonExample
    singleton_vars = [
        v
        for v in variables
        if v.fully_qualified_parent_path.startswith("SingletonExample")
    ]

    # Should extract variables from both the class and singleton class
    assert len(singleton_vars) >= 2

    var_names = {v.name for v in singleton_vars}
    assert "CLASS_CONSTANT" in var_names
    assert "@instance" in var_names


def test_extract_similar_variable_names(variables_test_code: str) -> None:
    """Test that variables with similar names are all extracted"""
    driver_tree = RubyDriverTree.from_code(variables_test_code, "test_variables.rb")
    variables = driver_tree._extract_variables_and_constants()

    # Filter for SimilarNames class
    similar_vars = [
        v for v in variables if v.fully_qualified_parent_path == "SimilarNames"
    ]

    # Should have: @@count, @@counter, @@count_total, @name, @name_full, @nickname
    assert len(similar_vars) == 6

    var_names = {v.name for v in similar_vars}
    # Class variables
    assert "@@count" in var_names
    assert "@@counter" in var_names
    assert "@@count_total" in var_names
    # Instance variables
    assert "@name" in var_names
    assert "@name_full" in var_names
    assert "@nickname" in var_names


@pytest.mark.parametrize(
    "class_name,expected_count",
    [
        ("OnlyConstants", 2),
        ("OnlyClassVariables", 2),
        ("OnlyInstanceVariables", 3),
        ("NamespacedConstants", 4),
    ],
)
def test_extract_variables_by_class(
    variables_test_code: str, class_name: str, expected_count: int
) -> None:
    """Parametrized test for variable extraction by class"""
    driver_tree = RubyDriverTree.from_code(variables_test_code, "test_variables.rb")
    variables = driver_tree._extract_variables_and_constants()

    class_vars = [v for v in variables if v.fully_qualified_parent_path == class_name]

    assert (
        len(class_vars) == expected_count
    ), f"Expected {expected_count} variables in {class_name}, got {len(class_vars)}"


def test_extract_variables_symbol_kind(variables_test_code: str) -> None:
    """Test that all extracted variables have SymbolKind.VARIABLE_DEFINITION"""
    from utils.lang_specialization.symbol_common import SymbolKind

    driver_tree = RubyDriverTree.from_code(variables_test_code, "test_variables.rb")
    variables = driver_tree._extract_variables_and_constants()

    for var in variables:
        assert var.symbol_kind == SymbolKind.VARIABLE_DEFINITION


def test_extract_variables_bespoke_data(variables_test_code: str) -> None:
    """Test that all extracted variables have valid bespoke data"""
    from .ruby_driver import RubyVariableBespokeMarker, RubyVariableKind

    driver_tree = RubyDriverTree.from_code(variables_test_code, "test_variables.rb")
    variables = driver_tree._extract_variables_and_constants()

    for var in variables:
        assert var.bespoke_data is not None
        assert isinstance(var.bespoke_data, RubyVariableBespokeMarker)
        assert var.bespoke_data.kind in [
            RubyVariableKind.CONSTANT,
            RubyVariableKind.VARIABLE,
        ]
        assert isinstance(var.bespoke_data.is_top_level, bool)


# =============================================================================
# Tests for extract_attributes()
# =============================================================================


@pytest.fixture(scope="module")
def attributes_test_code() -> str:
    file_path = (
        pathlib.Path(__file__).parent
        / "treesitter_testcases"
        / "ruby"
        / "test_attributes.rb"
    )
    with open(file_path, encoding="utf-8") as f:
        return f.read()


def test_extract_attributes_count(attributes_test_code: str) -> None:
    """Test that we extract the correct total number of attributes"""
    driver_tree = RubyDriverTree.from_code(attributes_test_code, "test_attributes.rb")
    attributes = driver_tree._extract_attributes()

    # Should extract many attributes across all test classes
    # Each attr_accessor creates 1 attribute, attr_reader creates 1, attr_writer creates 1
    # Multiple symbols in one call create multiple attributes
    assert (
        len(attributes) >= 50
    ), f"Expected at least 50 attributes, got {len(attributes)}"


def test_extract_simple_attributes(attributes_test_code: str) -> None:
    """Test extraction of basic attr_accessor, attr_reader, attr_writer"""
    from .ruby_driver import RubyAttributeAccessKind

    driver_tree = RubyDriverTree.from_code(attributes_test_code, "test_attributes.rb")
    attributes = driver_tree._extract_attributes()

    # Filter for SimpleAttributes class
    simple_attrs = [
        a for a in attributes if a.fully_qualified_parent_path == "SimpleAttributes"
    ]

    # Should have: name, age (accessor=RW), id (reader=R), status (writer=W) = 4 attributes
    assert len(simple_attrs) == 4

    attr_map = {a.name: a.bespoke_data.access for a in simple_attrs}
    assert attr_map["name"] == RubyAttributeAccessKind.READ_WRITE
    assert attr_map["age"] == RubyAttributeAccessKind.READ_WRITE
    assert attr_map["id"] == RubyAttributeAccessKind.READ
    assert attr_map["status"] == RubyAttributeAccessKind.WRITE


def test_extract_multiple_symbols_in_one_call(attributes_test_code: str) -> None:
    """Test that multiple symbols in one attr call create multiple attributes"""

    driver_tree = RubyDriverTree.from_code(attributes_test_code, "test_attributes.rb")
    attributes = driver_tree._extract_attributes()

    # Filter for MixedAttributes class
    mixed_attrs = [
        a for a in attributes if a.fully_qualified_parent_path == "MixedAttributes"
    ]

    # Should have: first_name, last_name (RW), email, phone (R), address, city, zip (W) = 7 attributes
    assert len(mixed_attrs) == 7

    attr_names = {a.name for a in mixed_attrs}
    assert "first_name" in attr_names
    assert "last_name" in attr_names
    assert "email" in attr_names
    assert "phone" in attr_names
    assert "address" in attr_names
    assert "city" in attr_names
    assert "zip" in attr_names


def test_extract_module_attributes(attributes_test_code: str) -> None:
    """Test extraction of attributes in modules"""
    driver_tree = RubyDriverTree.from_code(attributes_test_code, "test_attributes.rb")
    attributes = driver_tree._extract_attributes()

    # Filter for AttributeModule
    module_attrs = [
        a for a in attributes if a.fully_qualified_parent_path == "AttributeModule"
    ]

    # Should have: config (RW), version (R), debug_mode (W) = 3 attributes
    assert len(module_attrs) == 3

    attr_names = {a.name for a in module_attrs}
    assert "config" in attr_names
    assert "version" in attr_names
    assert "debug_mode" in attr_names


def test_extract_nested_class_attributes(attributes_test_code: str) -> None:
    """Test extraction of attributes in nested classes"""
    driver_tree = RubyDriverTree.from_code(attributes_test_code, "test_attributes.rb")
    attributes = driver_tree._extract_attributes()

    # Filter for OuterAttributes
    outer_attrs = [
        a for a in attributes if a.fully_qualified_parent_path == "OuterAttributes"
    ]

    assert len(outer_attrs) == 1
    assert outer_attrs[0].name == "outer_attr"

    # Filter for InnerAttributes
    inner_attrs = [
        a
        for a in attributes
        if a.fully_qualified_parent_path == "OuterAttributes::InnerAttributes"
    ]

    assert len(inner_attrs) == 2
    attr_names = {a.name for a in inner_attrs}
    assert "inner_attr" in attr_names
    assert "inner_readonly" in attr_names


def test_extract_attributes_fqp(attributes_test_code: str) -> None:
    """Test that fully_qualified_parent_path is correct for all attributes"""
    driver_tree = RubyDriverTree.from_code(attributes_test_code, "test_attributes.rb")
    attributes = driver_tree._extract_attributes()

    # Check specific attributes and their FQP
    fqp_map = {}
    for attr in attributes:
        if attr.name not in fqp_map:
            fqp_map[attr.name] = []
        fqp_map[attr.name].append(attr.fully_qualified_parent_path)

    # Check class-level attributes
    assert "SimpleAttributes" in fqp_map.get("name", [])
    assert "AttributeModule" in fqp_map.get("config", [])

    # Check nested attributes
    assert "OuterAttributes::InnerAttributes" in fqp_map.get("inner_attr", [])


def test_extract_empty_class_attributes(attributes_test_code: str) -> None:
    """Test that classes without attr declarations have no attributes"""
    driver_tree = RubyDriverTree.from_code(attributes_test_code, "test_attributes.rb")
    attributes = driver_tree._extract_attributes()

    # Filter for NoAttributes class
    no_attrs = [
        a for a in attributes if a.fully_qualified_parent_path == "NoAttributes"
    ]

    assert len(no_attrs) == 0


def test_extract_only_accessor_attributes(attributes_test_code: str) -> None:
    """Test class with only attr_accessor"""
    from .ruby_driver import RubyAttributeAccessKind

    driver_tree = RubyDriverTree.from_code(attributes_test_code, "test_attributes.rb")
    attributes = driver_tree._extract_attributes()

    # Filter for OnlyAccessor class
    only_accessor = [
        a for a in attributes if a.fully_qualified_parent_path == "OnlyAccessor"
    ]

    assert len(only_accessor) == 2
    for attr in only_accessor:
        assert attr.bespoke_data.access == RubyAttributeAccessKind.READ_WRITE


def test_extract_only_reader_attributes(attributes_test_code: str) -> None:
    """Test class with only attr_reader"""
    from .ruby_driver import RubyAttributeAccessKind

    driver_tree = RubyDriverTree.from_code(attributes_test_code, "test_attributes.rb")
    attributes = driver_tree._extract_attributes()

    # Filter for OnlyReader class
    only_reader = [
        a for a in attributes if a.fully_qualified_parent_path == "OnlyReader"
    ]

    assert len(only_reader) == 3
    for attr in only_reader:
        assert attr.bespoke_data.access == RubyAttributeAccessKind.READ


def test_extract_only_writer_attributes(attributes_test_code: str) -> None:
    """Test class with only attr_writer"""
    from .ruby_driver import RubyAttributeAccessKind

    driver_tree = RubyDriverTree.from_code(attributes_test_code, "test_attributes.rb")
    attributes = driver_tree._extract_attributes()

    # Filter for OnlyWriter class
    only_writer = [
        a for a in attributes if a.fully_qualified_parent_path == "OnlyWriter"
    ]

    assert len(only_writer) == 1
    assert only_writer[0].bespoke_data.access == RubyAttributeAccessKind.WRITE


def test_extract_unicode_attributes(attributes_test_code: str) -> None:
    """Test extraction of attributes with unicode characters"""
    driver_tree = RubyDriverTree.from_code(attributes_test_code, "test_attributes.rb")
    attributes = driver_tree._extract_attributes()

    # Filter for UnicodeAttributes class
    unicode_attrs = [
        a for a in attributes if a.fully_qualified_parent_path == "UnicodeAttributes"
    ]

    assert len(unicode_attrs) == 2
    attr_names = {a.name for a in unicode_attrs}
    assert "café" in attr_names
    assert "naïve" in attr_names


def test_extract_number_attributes(attributes_test_code: str) -> None:
    """Test extraction of attributes with numbers in names"""
    driver_tree = RubyDriverTree.from_code(attributes_test_code, "test_attributes.rb")
    attributes = driver_tree._extract_attributes()

    # Filter for NumberAttributes class
    number_attrs = [
        a for a in attributes if a.fully_qualified_parent_path == "NumberAttributes"
    ]

    assert len(number_attrs) == 3
    attr_names = {a.name for a in number_attrs}
    assert "attr_1" in attr_names
    assert "attr_2" in attr_names
    assert "readonly_3" in attr_names


def test_extract_reopened_class_attributes(attributes_test_code: str) -> None:
    """Test extraction of attributes from reopened classes"""
    driver_tree = RubyDriverTree.from_code(attributes_test_code, "test_attributes.rb")
    attributes = driver_tree._extract_attributes()

    # Filter for ReopenedAttributeClass
    reopened_attrs = [
        a
        for a in attributes
        if a.fully_qualified_parent_path == "ReopenedAttributeClass"
    ]

    # Should have attributes from both class definitions
    assert len(reopened_attrs) == 2
    attr_names = {a.name for a in reopened_attrs}
    assert "first" in attr_names
    assert "second" in attr_names


def test_extract_singleton_class_attributes(attributes_test_code: str) -> None:
    """Test extraction of attributes in singleton classes"""
    driver_tree = RubyDriverTree.from_code(attributes_test_code, "test_attributes.rb")
    attributes = driver_tree._extract_attributes()

    # Filter for SingletonAttributes (both regular and singleton)
    singleton_attrs = [
        a
        for a in attributes
        if a.fully_qualified_parent_path.startswith("SingletonAttributes")
    ]

    # Should extract attributes from both the class and singleton class
    assert len(singleton_attrs) >= 1


def test_extract_attributes_symbol_kind(attributes_test_code: str) -> None:
    """Test that all extracted attributes have SymbolKind.VARIABLE_DEFINITION"""
    from utils.lang_specialization.symbol_common import SymbolKind

    driver_tree = RubyDriverTree.from_code(attributes_test_code, "test_attributes.rb")
    attributes = driver_tree._extract_attributes()

    for attr in attributes:
        assert attr.symbol_kind == SymbolKind.VARIABLE_DEFINITION


def test_extract_attributes_bespoke_data(attributes_test_code: str) -> None:
    """Test that all extracted attributes have valid bespoke data"""
    from .ruby_driver import RubyAttributeAccessKind, RubyVariableBespokeMarker

    driver_tree = RubyDriverTree.from_code(attributes_test_code, "test_attributes.rb")
    attributes = driver_tree._extract_attributes()

    for attr in attributes:
        assert attr.bespoke_data is not None
        assert isinstance(attr.bespoke_data, RubyVariableBespokeMarker)
        assert attr.bespoke_data.access in [
            RubyAttributeAccessKind.READ,
            RubyAttributeAccessKind.WRITE,
            RubyAttributeAccessKind.READ_WRITE,
        ]


def test_extract_attributes_access_modes(attributes_test_code: str) -> None:
    """Test that access modes are correctly assigned"""
    from .ruby_driver import RubyAttributeAccessKind

    driver_tree = RubyDriverTree.from_code(attributes_test_code, "test_attributes.rb")
    attributes = driver_tree._extract_attributes()

    # Count by access mode
    access_counts = {
        RubyAttributeAccessKind.READ: 0,
        RubyAttributeAccessKind.WRITE: 0,
        RubyAttributeAccessKind.READ_WRITE: 0,
    }

    for attr in attributes:
        access_counts[attr.bespoke_data.access] += 1

    # Should have some of each type
    assert access_counts[RubyAttributeAccessKind.READ] > 0
    assert access_counts[RubyAttributeAccessKind.WRITE] > 0
    assert access_counts[RubyAttributeAccessKind.READ_WRITE] > 0


@pytest.mark.parametrize(
    "class_name,expected_count",
    [
        ("SimpleAttributes", 4),
        ("SingleAttributes", 3),
        ("MixedAttributes", 7),
        ("OnlyAccessor", 2),
        ("OnlyReader", 3),
        ("OnlyWriter", 1),
    ],
)
def test_extract_attributes_by_class(
    attributes_test_code: str, class_name: str, expected_count: int
) -> None:
    """Parametrized test for attribute extraction by class"""
    driver_tree = RubyDriverTree.from_code(attributes_test_code, "test_attributes.rb")
    attributes = driver_tree._extract_attributes()

    class_attrs = [a for a in attributes if a.fully_qualified_parent_path == class_name]

    assert (
        len(class_attrs) == expected_count
    ), f"Expected {expected_count} attributes in {class_name}, got {len(class_attrs)}"
