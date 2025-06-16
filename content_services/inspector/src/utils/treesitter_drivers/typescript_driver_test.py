"""
Tests for TypeScript tree-sitter driver
"""

from pathlib import Path

import pytest

from utils.lang_specialization.symbol_common import SymbolKind

from .typescript_driver import TypeScriptDriverTree


class TestTypeScriptDriver:
    """Test TypeScript tree-sitter driver functionality"""

    @pytest.fixture
    def test_dir(self) -> Path:
        return Path(__file__).parent / "treesitter_testcases" / "typescript"

    @pytest.fixture
    def imports_code(self, test_dir: Path) -> str:
        return (test_dir / "test_imports.ts").read_text()

    @pytest.fixture
    def functions_code(self, test_dir: Path) -> str:
        return (test_dir / "test_functions.ts").read_text()

    @pytest.fixture
    def classes_code(self, test_dir: Path) -> str:
        return (test_dir / "test_classes.ts").read_text()

    @pytest.fixture
    def interfaces_code(self, test_dir: Path) -> str:
        return (test_dir / "test_interfaces.ts").read_text()

    @pytest.fixture
    def variables_code(self, test_dir: Path) -> str:
        return (test_dir / "test_variables.ts").read_text()

    @pytest.fixture
    def enums_code(self, test_dir: Path) -> str:
        return (test_dir / "test_enums.ts").read_text()

    @pytest.fixture
    def methods_code(self, test_dir: Path) -> str:
        return (test_dir / "test_methods.ts").read_text()

    @pytest.fixture
    def modules_code(self, test_dir: Path) -> str:
        return (test_dir / "test_modules.ts").read_text()

    # Test imports
    def test_extract_imports_count(self, imports_code: str) -> None:
        tree = TypeScriptDriverTree.from_code(imports_code, "test_imports.ts")
        imports = tree.extract_imports()
        # Count all import statements (including side-effect imports, dynamic imports, and import.meta)
        assert len(imports) == 36

    @pytest.mark.parametrize(
        "import_source,expected_line",
        [
            # Default imports
            ("react", 4),
            ("./module", 5),
            # Named imports
            ("@angular/core", 8),
            ("react", 9),
            ("fs/promises", 10),
            # Named imports with aliases
            ("@angular/core", 13),
            ("./module", 14),
            # Namespace imports
            ("fs", 17),
            # Multiple imports from same module
            ("./component", 20),
            ("./library", 21),
            # Type-only imports
            ("./types", 24),
            ("./config", 25),
            ("./all-types", 26),
            ("./default-type", 27),
            # Side-effect imports
            ("./polyfills", 30),
            ("zone.js", 31),
            # Dynamic imports
            ("./lazy", 34),
            ("./lazy-component", 35),
            # Import with assertions
            ("./data.json", 38),
            # CommonJS-style imports
            ("fs", 41),
            ("http", 42),
            # Import meta
            ("import.meta.url", 45),
            ("import.meta.env", 46),
            # Top-level await with dynamic import
            ("./dynamic", 49),
            # Import from node_modules
            ("express", 53),
            ("express", 54),
            # Import from scoped packages
            ("@angular/core", 57),
            ("@rxjs/observable", 58),
            # Import from nested paths
            ("./utils/helpers", 61),
            ("./components/Button/Button", 62),
            # Import with query parameters
            ("./worker.js?worker", 65),
            ("./asset.png?url", 66),
            # Import from parent directories
            ("../helpers", 69),
            ("../../utils", 70),
            # Import index files
            ("./utils", 73),
            ("./components", 74),
        ],
    )
    def test_extract_specific_imports(
        self, imports_code: str, import_source: str, expected_line: int
    ) -> None:
        tree = TypeScriptDriverTree.from_code(imports_code, "test_imports.ts")
        imports = tree.extract_imports()

        matching = [imp for imp in imports if import_source in imp.name]
        assert len(matching) > 0, f"Import '{import_source}' not found"
        assert any(imp.start_line == expected_line for imp in matching)

    # Test functions
    def test_extract_functions_count(self, functions_code: str) -> None:
        tree = TypeScriptDriverTree.from_code(functions_code, "test_functions.ts")
        functions = tree.extract_callable_definitions()
        # Should find function declarations, arrow functions, generators, etc.
        assert len(functions) >= 80

    @pytest.mark.parametrize(
        "function_name,expected_line,is_async,is_generator",
        [
            ("simpleFunction", 4, False, False),
            ("optionalParams", 18, False, False),
            ("restParams", 31, False, False),
            ("arrowFunction", 40, False, False),
            ("genericFunction", 55, False, False),
            ("overloaded", 73, False, False),
            ("asyncFunction", 96, True, False),
            ("generatorFunction", 118, False, True),
            ("asyncGenerator", 138, True, True),
            ("taggedTemplate", 233, False, False),
        ],
    )
    def test_extract_specific_functions(
        self,
        functions_code: str,
        function_name: str,
        expected_line: int,
        is_async: bool,
        is_generator: bool,
    ) -> None:
        tree = TypeScriptDriverTree(functions_code, "test_functions.ts")
        functions = tree.extract_callable_definitions()

        matching = [f for f in functions if f.name == function_name]
        assert len(matching) > 0, f"Function '{function_name}' not found"

        func = matching[0]
        assert func.line_number_start == expected_line
        # Note: async/generator detection would be implemented in the driver

    # Test classes
    def test_extract_classes_count(self, classes_code: str) -> None:
        tree = TypeScriptDriverTree.from_code(classes_code, "test_classes.ts")
        classes = tree.extract_data_structure_definitions()
        # Should find all class definitions including anonymous ones
        # We have 40 classes listed in the test cases plus some anonymous/nested ones
        assert len(classes) >= 40

    @pytest.mark.parametrize(
        "class_name,expected_start_line,expected_end_line",
        [
            ("SimpleClass", 4, 8),
            ("ClassWithProperties", 11, 24),
            ("ClassWithMethods", 27, 43),
            ("ParameterProperties", 46, 53),
            ("GettersSetters", 56, 78),
            ("Animal", 81, 91),
            ("Dog", 93, 108),
            ("Shape", 111, 118),  # Abstract class
            ("Circle", 120, 132),
            ("Container", 135, 149),  # Generic class
            ("TwoTypeContainer", 151, 164),
            ("ConstrainedContainer", 167, 173),  # Generic with constraints
            ("Bird", 186, 193),  # Implements interface
            ("Duck", 195, 202),  # Extends and implements
            ("Amphibian", 205, 216),  # Multiple interfaces
            ("AppComponent", 219, 234),  # With decorators - starts at decorator
            ("ServiceClass", 237, 253),
            ("StaticExample", 256, 277),
            ("PrivateFields", 280, 299),  # ES2022 private fields
            (None, 302, 306),  # Class expression
            ("MyClass", 308, 314),  # Named class expression
            (None, 317, 325),  # Anonymous class extending
            ("Outer", 328, 338),  # With nested class
            ("BasicClass", 363, 368),
            ("AsyncClass", 374, 393),  # With async methods
            ("GeneratorClass", 396, 406),  # With generator methods
            ("IndexedClass", 411, 420),  # With index signatures
            ("FluentAPI", 423, 439),  # Fluent API pattern
            ("OverloadedConstructor", 442, 452),  # Constructor overloads
            ("OverloadedMethods", 455, 467),  # Method overloads
            ("ClassNamespace", 470, 481),  # Classes as namespaces
            ("MergedClass", 484, 488),  # Declaration merging
            ("PropertyAccess", 496, 506),  # Generic with keyof
            ("ConditionalClass", 509, 515),  # Conditional types
            ("AbstractGeneric", 518, 524),  # Abstract generic
            ("ConcreteGeneric", 526, 530),
            ("SymbolClass", 533, 543),  # Symbol members
            ("BrandedClass", 546, 552),  # Brand checking
            ("ReadonlyClass", 555, 565),  # Readonly properties
            ("Validator", 568, 578),  # Assertion signatures
        ],
    )
    def test_extract_specific_classes(
        self,
        classes_code: str,
        class_name: str,
        expected_start_line: int,
        expected_end_line: int,
    ) -> None:
        tree = TypeScriptDriverTree.from_code(classes_code, "test_classes.ts")
        classes = tree.extract_data_structure_definitions()

        if class_name is None:
            # For anonymous classes, we need to match by line number since there can be multiple
            matching = [
                c
                for c in classes
                if c.name is None and c.start_line == expected_start_line
            ]
            assert (
                len(matching) > 0
            ), f"Anonymous class at line {expected_start_line} not found"
        else:
            matching = [c for c in classes if c.name == class_name]
            assert len(matching) > 0, f"Class '{class_name}' not found"

        class_symbol = matching[0]
        assert (
            class_symbol.start_line == expected_start_line
        ), f"Class '{class_name if class_name else 'Anonymous'}' start line mismatch: expected {expected_start_line}, got {class_symbol.start_line}"
        assert (
            class_symbol.end_line == expected_end_line
        ), f"Class '{class_name if class_name else 'Anonymous'}' end line mismatch: expected {expected_end_line}, got {class_symbol.end_line}"

    # Test interfaces
    def test_extract_interfaces_count(self, interfaces_code: str) -> None:
        tree = TypeScriptDriverTree(interfaces_code, "test_interfaces.ts")
        interfaces = tree.extract_data_structure_definitions()
        # Should find interfaces and type aliases
        assert len(interfaces) >= 100

    @pytest.mark.parametrize(
        "interface_name,expected_line",
        [
            (
                "SimpleInterface",
                4,
            ),
            ("InterfaceWithMethods", 8),
            ("StringIndex", 28),
            ("Dog", 45),  # Extends Animal
            ("Container", 74),  # Generic interface
            ("CallableInterface", 108),
            ("HybridInterface", 125),
            ("Person", 157),  # Type alias intersection
        ],
    )
    def test_extract_specific_interfaces(
        self, interfaces_code: str, interface_name: str, expected_line: int
    ) -> None:
        tree = TypeScriptDriverTree(interfaces_code, "test_interfaces.ts")
        interfaces = tree.extract_data_structure_definitions()

        matching = [i for i in interfaces if i.name == interface_name]
        assert len(matching) > 0, f"Interface '{interface_name}' not found"
        assert any(i.line_number_start == expected_line for i in matching)

    # Test variables
    def test_extract_variables_count(self, variables_code: str) -> None:
        tree = TypeScriptDriverTree(variables_code, "test_variables.ts")
        variables = tree.extract_variables()
        # Should find const, let, var declarations
        assert len(variables) >= 150

    @pytest.mark.parametrize(
        "variable_name,expected_line,declaration_type",
        [
            ("simpleConst", 4, "const"),
            ("simpleLet", 11, "let"),
            ("simpleVar", 18, "var"),
            ("simpleArray", 29, "const"),
            ("simpleObject", 38, "const"),
            ("annotatedString", 53, "const"),
            ("stringOrNumber", 61, "let"),
            ("genericArray", 81, "const"),
            ("sym", 122, "const"),
            ("bigIntLiteral", 128, "const"),
            ("template", 153, "const"),
        ],
    )
    def test_extract_specific_variables(
        self,
        variables_code: str,
        variable_name: str,
        expected_line: int,
        declaration_type: str,
    ) -> None:
        tree = TypeScriptDriverTree(variables_code, "test_variables.ts")
        variables = tree.extract_variables()

        matching = [v for v in variables if v.name == variable_name]
        assert len(matching) > 0, f"Variable '{variable_name}' not found"
        assert matching[0].line_number_start == expected_line

    # Test enums
    def test_extract_enums_count(self, enums_code: str) -> None:
        tree = TypeScriptDriverTree(enums_code, "test_enums.ts")
        enums = tree.extract_data_structure_definitions()
        # Should find all enum declarations
        enum_list = [e for e in enums if "enum" in str(e.kind).lower()]
        assert len(enum_list) >= 35

    @pytest.mark.parametrize(
        "enum_name,expected_line,is_const",
        [
            ("Direction", 4, False),
            ("StatusCode", 12, False),
            ("Color", 24, False),  # String enum
            ("Mixed", 33, False),  # Mixed enum
            ("ConstDirection", 50, True),  # Const enum
            ("FileAccess", 63, False),  # With computed values
            ("AmbientEnum", 73, False),  # Ambient enum
        ],
    )
    def test_extract_specific_enums(
        self, enums_code: str, enum_name: str, expected_line: int, is_const: bool
    ) -> None:
        tree = TypeScriptDriverTree(enums_code, "test_enums.ts")
        enums = tree.extract_data_structure_definitions()

        matching = [e for e in enums if e.name == enum_name]
        assert len(matching) > 0, f"Enum '{enum_name}' not found"
        assert any(e.line_number_start == expected_line for e in matching)

    # Test methods
    def test_extract_methods_count(self, methods_code: str) -> None:
        tree = TypeScriptDriverTree(methods_code, "test_methods.ts")
        methods = tree.extract_callable_definitions()
        # Should find all method definitions
        method_list = [m for m in methods if "." in m.fully_qualified_path_to_parent]
        assert len(method_list) >= 100

    @pytest.mark.parametrize(
        "method_name,class_name,expected_line",
        [
            ("simpleMethod", "BasicMethods", 4),
            ("publicMethod", "AccessModifiers", 22),
            ("simpleStatic", "StaticMethods", 38),
            ("simpleAsync", "AsyncMethods", 58),
            ("simpleGenerator", "GeneratorMethods", 86),
            ("value", "GettersSetters", 110),  # Getter
            ("identity", "GenericMethods", 150),
            ("process", "MethodOverloading", 180),
        ],
    )
    def test_extract_specific_methods(
        self, methods_code: str, method_name: str, class_name: str, expected_line: int
    ) -> None:
        tree = TypeScriptDriverTree(methods_code, "test_methods.ts")
        methods = tree.extract_callable_definitions()

        matching = [
            m
            for m in methods
            if m.name == method_name and class_name in m.fully_qualified_path_to_parent
        ]
        assert (
            len(matching) > 0
        ), f"Method '{method_name}' in class '{class_name}' not found"
        assert any(m.line_number_start == expected_line for m in matching)

    # Test modules/namespaces
    def test_extract_modules_count(self, modules_code: str) -> None:
        tree = TypeScriptDriverTree(modules_code, "test_modules.ts")
        # Namespaces and modules might be extracted as data structures or have special handling
        structures = tree.extract_data_structure_definitions()
        namespace_list = [
            s
            for s in structures
            if "namespace" in str(s.kind).lower() or "module" in str(s.kind).lower()
        ]
        assert len(namespace_list) >= 20

    # Test function calls
    def test_extract_function_calls_count(self, functions_code: str) -> None:
        tree = TypeScriptDriverTree(functions_code, "test_functions.ts")
        calls = tree.extract_function_calls()
        assert len(calls) >= 10  # Various function calls in the code

    @pytest.mark.parametrize(
        "call_name,expected_kind",
        [
            ("console.log", SymbolKind.CALL),
            ("add", SymbolKind.CALL),
            ("Promise.resolve", SymbolKind.CALL),
            ("fetch", SymbolKind.CALL),
            ("setTimeout", SymbolKind.CALL),
        ],
    )
    def test_function_call_types(
        self, functions_code: str, call_name: str, expected_kind: SymbolKind
    ) -> None:
        tree = TypeScriptDriverTree(functions_code, "test_functions.ts")
        calls = tree.extract_function_calls()

        matching = [c for c in calls if c.name == call_name]
        assert len(matching) > 0, f"Function call '{call_name}' not found"
        # All function calls should have SymbolKind.CALL
        assert all(c.symbol_kind == expected_kind for c in matching)

    # Test edge cases
    def test_decorators(self, classes_code: str) -> None:
        """Test that decorators are properly handled"""
        tree = TypeScriptDriverTree(classes_code, "test_classes.ts")
        classes = tree.extract_data_structure_definitions()

        # Find decorated class
        app_component = [c for c in classes if c.name == "AppComponent"]
        assert len(app_component) > 0
        # Decorator handling would be in the implementation

    def test_generic_types(self, interfaces_code: str) -> None:
        """Test generic type extraction"""
        tree = TypeScriptDriverTree(interfaces_code, "test_interfaces.ts")
        interfaces = tree.extract_data_structure_definitions()

        # Find generic interfaces
        container = [
            i for i in interfaces if i.name == "Container" and i.line_number_start == 74
        ]
        assert len(container) > 0

    def test_type_aliases(self, interfaces_code: str) -> None:
        """Test type alias extraction"""
        tree = TypeScriptDriverTree(interfaces_code, "test_interfaces.ts")
        types = tree.extract_data_structure_definitions()

        # Find type aliases
        string_or_number = [t for t in types if t.name == "StringOrNumber"]
        assert len(string_or_number) > 0

    def test_namespace_members(self, modules_code: str) -> None:
        """Test namespace member extraction"""
        tree = TypeScriptDriverTree(modules_code, "test_modules.ts")

        # Extract various symbols from namespaces
        functions = tree.extract_callable_definitions()
        namespace_funcs = [
            f for f in functions if "BasicNamespace" in f.fully_qualified_path_to_parent
        ]
        assert len(namespace_funcs) > 0

    def test_no_duplicates(self, functions_code: str) -> None:
        """Test that symbols are not duplicated"""
        tree = TypeScriptDriverTree(functions_code, "test_functions.ts")
        functions = tree.extract_callable_definitions()

        # Check for duplicate function names at same line
        seen = set()
        for func in functions:
            key = (func.name, func.line_number_start)
            assert (
                key not in seen
            ), f"Duplicate function {func.name} at line {func.line_number_start}"
            seen.add(key)

    def test_nested_structures(self, classes_code: str) -> None:
        """Test nested class/interface extraction"""
        tree = TypeScriptDriverTree(classes_code, "test_classes.ts")

        # Test nested classes
        classes = tree.extract_data_structure_definitions()
        nested = [
            c
            for c in classes
            if "Outer.NestedClass" in c.fully_qualified_path_to_parent
            or c.name == "NestedClass"
        ]
        assert len(nested) > 0

    def test_method_overloading(self, methods_code: str) -> None:
        """Test method overloading detection"""
        tree = TypeScriptDriverTree(methods_code, "test_methods.ts")
        methods = tree.extract_callable_definitions()

        # Find overloaded methods
        process_methods = [
            m
            for m in methods
            if m.name == "process"
            and "MethodOverloading" in m.fully_qualified_path_to_parent
        ]
        # Should find the implementation, not the overload signatures
        assert len(process_methods) == 1

    def test_symbols_not_extracted(self, variables_code: str) -> None:
        """Test that certain constructs are not extracted as variables"""
        tree = TypeScriptDriverTree(variables_code, "test_variables.ts")
        variables = tree.extract_variables()

        # Destructured variables should be extracted individually
        names = [v.name for v in variables]
        assert "name" in names  # From destructuring
        assert "age" in names  # From destructuring

        # But the destructuring pattern itself should not be a variable
        assert "{ name, age }" not in names

    def test_export_extraction(self, imports_code: str) -> None:
        """Test export statement handling"""
        tree = TypeScriptDriverTree(imports_code, "test_imports.ts")

        # Exports might be tracked separately or as part of other symbols
        # This would depend on implementation requirements
        functions = tree.extract_callable_definitions()
        # Check that exported functions exist
        assert any("export" in f.symbol_code for f in functions)

    def test_ambient_declarations(self, modules_code: str) -> None:
        """Test ambient declaration handling"""
        tree = TypeScriptDriverTree(modules_code, "test_modules.ts")

        # Ambient declarations might have special handling
        all_symbols = (
            tree.extract_callable_definitions()
            + tree.extract_data_structure_definitions()
            + tree.extract_variables()
        )

        ambient = [s for s in all_symbols if "declare" in s.symbol_code]
        assert len(ambient) > 0
