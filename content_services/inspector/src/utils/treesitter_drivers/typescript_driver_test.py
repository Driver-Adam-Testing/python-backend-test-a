"""
Tests for TypeScript tree-sitter driver
"""

from pathlib import Path

import pytest

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
    def object_types_code(self, test_dir: Path) -> str:
        return (test_dir / "test_object_types.ts").read_text()

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

    @pytest.fixture
    def calls_code(self, test_dir: Path) -> str:
        return (test_dir / "test_calls.ts").read_text()

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
        assert len(functions) == 28

    @pytest.mark.parametrize(
        "function_name,expected_start_line,expected_end_line",
        [
            # Basic function declarations
            ("functionWithTypeParams", 4, 6),
            ("mixedRest", 9, 11),
            # Arrow functions
            ("arrowFunction", 14, 14),
            ("arrowWithParams", 16, 16),
            ("arrowWithBlock", 18, 21),
            ("arrowWithTypes", 23, 25),
            ("singleParam", 28, 28),
            ("singleParamWithType", 29, 29),
            # Generic functions
            ("genericFunction", 32, 34),
            ("multipleGenerics", 36, 38),
            ("constrainedGeneric", 40, 42),
            ("genericWithDefault", 44, 46),
            ("genericArrow", 48, 48),
            ("genericArrowConstrained", 50, 50),
            # Function overloading (implementation only)
            ("overloaded", 56, 58),
            # Async functions
            ("asyncWithParams", 61, 64),
            ("asyncArrowWithReturn", 66, 68),
            # Generator functions
            ("generatorWithReturn", 71, 75),
            ("generatorArrow", 77, 79),
            # Async generator functions
            ("asyncGenerator", 82, 85),
            ("asyncGeneratorWithType", 87, 90),
            # Function expressions
            ("functionExpression", 93, 95),
            ("namedFunc", 97, 99),
            # IIFEs (anonymous functions)
            # TODO: Currently not supporting IIFEs
            # (None, 102, 104),  # Anonymous IIFE
            # ("namedIIFE", 106, 108),
            # (None, 110, 112),  # Arrow IIFE
            # Type assertions and special cases
            ("assertionParams", 115, 117),
            ("taggedTemplate", 124, 126),
            # Curried functions
            ("curry", 129, 129),
            # Complex functions
            ("complexArrow", 162, 165),
            ("createMultiplier", 168, 170),
        ],
    )
    def test_extract_specific_functions(
        self,
        functions_code: str,
        function_name: str | None,
        expected_start_line: int,
        expected_end_line: int,
    ) -> None:
        tree = TypeScriptDriverTree.from_code(functions_code, "test_functions.ts")
        functions = tree.extract_callable_definitions()

        if function_name is None:
            # For anonymous functions, match by line number
            matching = [
                f
                for f in functions
                if f.name is None and f.start_line == expected_start_line
            ]
            assert (
                len(matching) > 0
            ), f"Anonymous function at line {expected_start_line} not found"
        else:
            matching = [f for f in functions if f.name == function_name]
            assert len(matching) > 0, f"Function '{function_name}' not found"

        func = matching[0]
        assert (
            func.start_line == expected_start_line
        ), f"Function '{function_name or 'Anonymous'}' start line mismatch: expected {expected_start_line}, got {func.start_line}"
        assert (
            func.end_line == expected_end_line
        ), f"Function '{function_name or 'Anonymous'}' end line mismatch: expected {expected_end_line}, got {func.end_line}"

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
        tree = TypeScriptDriverTree.from_code(interfaces_code, "test_interfaces.ts")
        interfaces = tree.extract_data_structure_definitions()
        # Should find interfaces and type aliases
        assert len(interfaces) == 20

    @pytest.mark.parametrize(
        "interface_name,expected_start_line,expected_end_line",
        [
            # Basic interfaces
            ("InterfaceWithOptional", 4, 8),
            # Readonly properties
            ("ReadonlyInterface", 11, 17),
            # Index signatures
            ("StringIndex", 20, 22),
            ("NumberIndex", 24, 26),
            ("MixedIndex", 28, 32),
            # Interface inheritance
            ("Animal", 35, 38),
            ("Dog", 40, 43),
            # Multiple inheritance
            ("Flyable", 46, 49),
            ("Swimmable", 51, 54),
            ("Duck", 56, 58),
            # Generic interfaces
            ("Pair", 61, 64),
            # Nested interfaces
            ("OuterInterface", 67, 75),
            # Interface merging - will have multiple entries
            ("MergedInterface", 78, 80),
            ("MergedInterface", 82, 84),
            ("MergedInterface", 86, 88),
            # Module augmentation interfaces
            ("Request", 94, 99),
            # Global augmentation
            ("Window", 104, 106),
            ("Array", 108, 110),
            # Ambient interfaces
            ("AmbientInterface", 114, 117),
            # Type-only exports
            ("ExportedInterface", 120, 122),
        ],
    )
    def test_extract_specific_interfaces(
        self,
        interfaces_code: str,
        interface_name: str,
        expected_start_line: int,
        expected_end_line: int,
    ) -> None:
        tree = TypeScriptDriverTree.from_code(interfaces_code, "test_interfaces.ts")
        interfaces = tree.extract_data_structure_definitions()

        matching = [i for i in interfaces if i.name == interface_name]
        assert len(matching) > 0, f"Interface '{interface_name}' not found"

        # Find the interface with the expected start line (for merged interfaces)
        interface = None
        for i in matching:
            if i.start_line == expected_start_line:
                interface = i
                break

        assert (
            interface is not None
        ), f"Interface '{interface_name}' at line {expected_start_line} not found"
        assert (
            interface.end_line == expected_end_line
        ), f"Interface '{interface_name}' end line mismatch: expected {expected_end_line}, got {interface.end_line}"

    # Test object types
    def test_extract_object_type_count(self, object_types_code: str) -> None:
        tree = TypeScriptDriverTree.from_code(object_types_code, "test_object_types.ts")
        object_types = tree.extract_data_structure_definitions()
        # Should find all class definitions including anonymous ones
        # We have 40 classes listed in the test cases plus some anonymous/nested ones
        assert len(object_types) == 17

    @pytest.mark.parametrize(
        "type_name,expected_start_line,expected_end_line",
        [
            # Intersection types with object literals
            ("PersonName", 12, 12),
            ("PersonAge", 13, 13),
            ("OverloadedFunction", 29, 32),
            # Object types
            ("Point", 35, 38),
            ("ReadonlyPoint", 40, 43),
            ("OptionalPoint", 45, 48),
            # Mapped types
            ("Readonly", 51, 53),
            ("Partial", 55, 57),
            ("Nullable", 59, 61),
            # Key remapping
            ("Getters", 64, 66),
            ("RemovePrefix", 68, 70),
            # Complex generic constraints
            ("ConstrainedGeneric", 103, 106),
            # Recursive types
            ("LinkedList", 117, 120),
            # This type
            ("FluentInterface", 155, 158),
            # Complex real-world types
            ("APIResponse", 160, 165),
            ("DeepPartial", 173, 175),
            ("DeepReadonly", 177, 179),
        ],
    )
    def test_extract_specific_object_types(
        self,
        object_types_code: str,
        type_name: str,
        expected_start_line: int,
        expected_end_line: int,
    ) -> None:
        tree = TypeScriptDriverTree.from_code(object_types_code, "test_object_types.ts")
        types = tree.extract_data_structure_definitions()

        matching = [i for i in types if i.name == type_name]
        assert len(matching) > 0, f"Type '{type_name}' not found"

        # Find the object type with the expected start line (for merged interfaces)
        object_type = None
        for i in matching:
            if i.start_line == expected_start_line:
                object_type = i
                break

        assert (
            object_type is not None
        ), f"Type '{type_name}' at line {expected_start_line} not found"
        assert (
            object_type.end_line == expected_end_line
        ), f"Type '{type_name}' end line mismatch: expected {expected_end_line}, got {object_type.end_line}"

    # Test variables
    def test_extract_variables_count(self, variables_code: str) -> None:
        tree = TypeScriptDriverTree.from_code(variables_code, "test_variables.ts")
        variables = tree.extract_variables()
        # Should find const, let, var declarations
        assert len(variables) == 29

    @pytest.mark.parametrize(
        "variable_name,expected_line",
        [
            # Const declarations
            ("simpleConst", 4),
            # Let declarations
            ("simpleLet", 7),
            # Var declarations
            ("simpleVar", 10),
            # Multiple declarations
            ("a", 13),
            ("b", 13),
            ("c", 13),
            ("x", 14),
            ("y", 14),
            ("z", 14),
            ("m", 15),
            ("n", 15),
            ("o", 15),
            # Array declarations
            ("simpleArray", 18),
            # Object declarations
            ("simpleObject", 21),
            # Type annotations
            ("annotatedString", 24),
            # Union types
            ("stringOrNumber", 27),
            # Intersection types
            ("intersection", 30),
            # Generic variables
            ("genericArray", 39),
            # Spread operator
            ("spreadArray", 42),
            ("spreadObject", 43),
            # Template literals
            ("template", 57),
            ("multiline", 58),
            # ("tagged", 62),
            # Export declarations
            ("exportedConst", 65),
            ("exportedLet", 66),
            ("exportedVar", 67),
            # Conditional expressions
            ("conditional", 71),
            # Readonly modifiers
            ("readonlyObj", 74),
            # Iterator protocol
            ("iteratorResult", 77),
            # Async iterators
            ("asyncIterable", 83),
        ],
    )
    def test_extract_specific_variables(
        self,
        variables_code: str,
        variable_name: str,
        expected_line: int,
    ) -> None:
        tree = TypeScriptDriverTree.from_code(variables_code, "test_variables.ts")
        variables = tree.extract_variables()

        matching = [v for v in variables if v.name == variable_name]
        assert len(matching) > 0, f"Variable '{variable_name}' not found"
        assert matching[0].start_line == expected_line

    # Test enums
    def test_extract_enums_count(self, enums_code: str) -> None:
        tree = TypeScriptDriverTree.from_code(enums_code, "test_enums.ts")
        enums = tree.extract_data_structure_definitions()
        # Should find all enum declarations
        enum_list = [e for e in enums if "enum" in str(e.kind).lower()]
        assert len(enum_list) >= 35

    @pytest.mark.parametrize(
        "enum_name,expected_line",
        [
            ("Direction", 4),
            ("StatusCode", 12),
            ("Color", 24),  # String enum
            ("Mixed", 33),  # Mixed enum
            ("ConstDirection", 50),  # Const enum
            ("FileAccess", 63),  # With computed values
            ("AmbientEnum", 73),  # Ambient enum
        ],
    )
    def test_extract_specific_enums(
        self, enums_code: str, enum_name: str, expected_line: int
    ) -> None:
        tree = TypeScriptDriverTree(enums_code, "test_enums.ts")
        enums = tree.extract_data_structure_definitions()

        matching = [e for e in enums if e.name == enum_name]
        assert len(matching) > 0, f"Enum '{enum_name}' not found"
        assert any(e.start_line == expected_line for e in matching)

    # Test methods
    def test_extract_methods_count(self, methods_code: str) -> None:
        tree = TypeScriptDriverTree.from_code(methods_code, "test_methods.ts")
        methods = tree.extract_callable_definitions()
        # Should find all method definitions inside classes/objects
        method_list = [m for m in methods if m.fully_qualified_parent_path != ""]
        assert len(method_list) >= 74

    @pytest.mark.parametrize(
        "method_name,class_name,expected_start_line,expected_end_line",
        [
            # BasicMethods
            ("methodWithOptional", "BasicMethods", 5, 7),
            ("methodWithDefault", "BasicMethods", 9, 11),
            # AccessModifiers
            ("publicMethod", "AccessModifiers", 15, 17),
            ("privateMethod", "AccessModifiers", 19, 21),
            ("protectedMethod", "AccessModifiers", 23, 25),
            # StaticMethods
            ("privateStatic", "StaticMethods", 29, 31),
            ("protectedStatic", "StaticMethods", 33, 35),
            ("#privateStaticMethod", "StaticMethods", 39, 41),
            # AsyncMethods
            ("asyncWithParams", "AsyncMethods", 45, 48),
            ("privateAsync", "AsyncMethods", 50, 52),
            ("staticAsync", "AsyncMethods", 54, 56),
            ("asyncGenerator", "AsyncMethods", 58, 62),
            # GeneratorMethods
            ("generatorWithReturn", "GeneratorMethods", 66, 70),
            ("privateGenerator", "GeneratorMethods", 72, 74),
            ("staticGenerator", "GeneratorMethods", 76, 78),
            ("[Symbol.iterator]", "GeneratorMethods", 80, 82),
            # GettersSetters
            ("value", "GettersSetters", 88, 90),  # getter
            ("value", "GettersSetters", 92, 94),  # setter
            ("readOnlyProp", "GettersSetters", 96, 98),
            ("privateGetter", "GettersSetters", 100, 102),
            ("protectedSetter", "GettersSetters", 104, 106),
            ("staticGetter", "GettersSetters", 108, 110),
            ("staticSetter", "GettersSetters", 112, 114),
            ("data", "GettersSetters", 119, 121),  # getter
            ("data", "GettersSetters", 123, 125),  # setter
            # GenericMethods
            ("identity", "GenericMethods", 129, 131),
            ("map", "GenericMethods", 133, 135),
            ("constrainedGeneric", "GenericMethods", 137, 139),
            ("multipleGenerics", "GenericMethods", 141, 143),
            ("staticGeneric", "GenericMethods", 145, 147),
            ("asyncGeneric", "GenericMethods", 149, 151),
            ("withDefault", "GenericMethods", 154, 156),
            # MethodOverloading (implementation only)
            ("process", "MethodOverloading", 163, 168),
            ("create", "MethodOverloading", 173, 175),
            # SpecialMethods
            ("constructor", "SpecialMethods", 180, 180),
            ("['computed' + 'Method']", "SpecialMethods", 186, 188),
            ("[Symbol.toString]", "SpecialMethods", 191, 193),
            ("[Symbol.toPrimitive]", "SpecialMethods", 195, 197),
            ("[Symbol.asyncIterator]", "SpecialMethods", 199, 202),
            ("compareWith", "SpecialMethods", 205, 207),
            ("regularMethod", "SpecialMethods", 217, 219),
            # DecoratedMethods
            ("simpleDecorated", "DecoratedMethods", 224, 226),
            ("multipleDecorators", "DecoratedMethods", 230, 232),
            # AbstractMethods
            ("concreteMethod", "AbstractMethods", 244, 246),
            ("staticInAbstract", "AbstractMethods", 252, 254),
            # ConcreteImplementation
            ("abstractMethod", "ConcreteImplementation", 258, 260),
            ("abstractGetter", "ConcreteImplementation", 262, 264),
            ("abstractSetter", "ConcreteImplementation", 266, 268),
            ("protectedAbstract", "ConcreteImplementation", 270, 272),
            # PrivateFieldMethods
            ("#privateMethod", "PrivateFieldMethods", 278, 280),
            ("publicAccessor", "PrivateFieldMethods", 282, 284),
            ("#staticPrivateMethod", "PrivateFieldMethods", 288, 290),
            ("publicStaticAccessor", "PrivateFieldMethods", 292, 294),
            ("#privateValue", "PrivateFieldMethods", 299, 301),  # getter
            ("#privateValue", "PrivateFieldMethods", 303, 305),  # setter
            # MethodChaining
            ("add", "MethodChaining", 311, 314),
            # ComplexMethods
            ("createCallback", "ComplexMethods", 319, 321),
            ("getAsyncCallback", "ComplexMethods", 324, 326),
            ("higherOrder", "ComplexMethods", 329, 334),
            ("curry", "ComplexMethods", 337, 339),
            ("destructured", "ComplexMethods", 342, 344),
            ("isValid", "ComplexMethods", 347, 349),
            ("assert", "ComplexMethods", 352, 356),
            # InterfaceImplementation
            ("requiredMethod", "InterfaceImplementation", 366, 368),
            ("optionalMethod", "InterfaceImplementation", 370, 372),
            ("methodWithParams", "InterfaceImplementation", 374, 376),
            # MixinClass
            ("useLogging", "MixinClass", 426, 429),
            # BaseClass
            ("baseMethod", "BaseClass", 420, 422),
            # objectWithMethods (these will be in the global scope)
            ("method", "objectWithMethods", 381, 383),
            ("asyncMethod", "objectWithMethods", 385, 387),
            ("generatorMethod", "objectWithMethods", 389, 391),
            ("getter", "objectWithMethods", 393, 395),
            ("setter", "objectWithMethods", 397, 399),
            ("['computed' + 'Method']", "objectWithMethods", 401, 403),
        ],
    )
    def test_extract_specific_methods(
        self,
        methods_code: str,
        method_name: str,
        class_name: str,
        expected_start_line: int,
        expected_end_line: int,
    ) -> None:
        tree = TypeScriptDriverTree.from_code(methods_code, "test_methods.ts")
        methods = tree.extract_callable_definitions()

        matching = [
            m
            for m in methods
            if m.name == method_name and class_name in m.fully_qualified_parent_path
        ]
        assert (
            len(matching) > 0
        ), f"Method '{method_name}' in class '{class_name}' not found"

        # Find the method with the expected start line (for overloaded methods)
        method = None
        for m in matching:
            if m.start_line == expected_start_line:
                method = m
                break

        assert (
            method is not None
        ), f"Method '{method_name}' in class '{class_name}' at line {expected_start_line} not found"
        assert (
            method.end_line == expected_end_line
        ), f"Method '{method_name}' in class '{class_name}' end line mismatch: expected {expected_end_line}, got {method.end_line}"

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

    def test_extract_calls_count(self, calls_code: str) -> None:
        tree = TypeScriptDriverTree.from_code(calls_code, "test_calls.ts")
        calls = tree.extract_function_calls()
        for call in calls:
            print(f"Found call: {call.name} at line {call.start_line}")
        # Should find a large number of function calls
        assert len(calls) == 41

    @pytest.mark.parametrize(
        "call_name,expected_line",
        [
            # Multiple arguments
            ("multipleArgs", 3),
            # Tagged template calls
            ("myTag", 48),
            ("complexTag", 54),
            # Spread operator calls
            ("spreadFunc", 65),
            ("spreadFunc", 66),
            # Mixed spread
            ("mixedSpread", 70),
            # Multiple type parameters
            ("multiGeneric", 79),
            # Async calls
            ("asyncFunc", 83),
            ("asyncFunc", 87),
            ("asyncFunc", 88),
            # Function.prototype methods
            ("bound", 98),
            # Nested calls
            ("outer", 155),
            ("inner", 155),
            # Deep nesting
            ("c", 161),
            ("b", 161),
            ("a", 161),
            # Generator calls
            ("generator", 182),
            # Async generator calls
            ("asyncGenerator", 193),
            # Non-null assertion calls
            ("nullableFunc!", 212),
            # Currying
            ("curry", 223),  # NOTE: only capturing the first curry call
            # Arrow currying
            ("arrowCurry", 227),
            # Rest parameters
            ("restFunc", 233),
            # Callback calls
            ("cb", 237),
            ("withCallback", 239),
            ("withCallback", 240),
            # Assertion functions
            ("assert", 354),
            # Type predicate calls
            ("isString", 360),
            ("isString", 361),
            # Recursive calls
            ("factorial", 368),
            ("factorial", 366),
            # Mutually recursive
            ("isEven", 379),
            ("isOdd", 373),
            ("isEven", 377),
            ("isOdd", 380),
            # Implicit calls
            ("String", 407),
            ("Number", 408),
            # BigInt constructor
            ("BigInt", 439),
            ("BigInt", 440),
            # Symbol constructor
            ("Symbol", 443),
            # Pipe operator simulation
            ("f", 470),
            ("pipe", 473),
        ],
    )
    def test_extract_specific_calls(
        self, calls_code: str, call_name: str, expected_line: int
    ) -> None:
        tree = TypeScriptDriverTree.from_code(calls_code, "test_calls.ts")
        calls = tree.extract_function_calls()

        if call_name == "":
            # For anonymous functions, match by line number
            matching = [c for c in calls if c.start_line == expected_line]
            assert (
                len(matching) > 0
            ), f"Anonymous call at line {expected_line} not found"
        else:
            matching = [
                c
                for c in calls
                if c.name == call_name and c.start_line == expected_line
            ]
            assert (
                len(matching) > 0
            ), f"Function call '{call_name}' at line {expected_line} not found"

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
            i for i in interfaces if i.name == "Container" and i.start_line == 74
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
            key = (func.name, func.start_line)
            assert (
                key not in seen
            ), f"Duplicate function {func.name} at line {func.start_line}"
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
