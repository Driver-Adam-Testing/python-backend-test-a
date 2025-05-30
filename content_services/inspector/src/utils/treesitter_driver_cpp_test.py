import pathlib

import pytest

from utils.treesitter_driver import CppCDriverTree


@pytest.fixture
def includes_cpp_code() -> str:
    """Load C++ includes test file"""
    file_path = (
        pathlib.Path(__file__).parent
        / "treesitter_testcases"
        / "cpp"
        / "test_includes.cpp"
    )
    with open(file_path, encoding="utf-8") as f:
        return f.read()


@pytest.mark.parametrize(
    "expected_include_name",
    [
        # Standard library includes
        "iostream",
        "vector",
        "string",
        "memory",
        "algorithm",
        "map",
        "unordered_map",
        "thread",
        "future",
        "cstdio",
        "cstdlib",
        # Local includes
        "myheader.h",
        "../headers/another_header.hpp",
        "utils/utility.h",
        "core/engine.hpp",
        # Conditional includes
        "GL/gl.h",
        "GL/glu.h",
        "windows.h",
        "unistd.h",
        "sys/types.h",
        # Third-party includes
        "boost/algorithm/string.hpp",
        "fmt/format.h",
    ],
)
def test_extract_includes(includes_cpp_code: str, expected_include_name: str) -> None:
    """Test extraction of #include directives"""
    driver_tree = CppCDriverTree.from_code(includes_cpp_code, "test.cpp")
    includes = driver_tree.extract_imports()

    extracted_includes = [include.name for include in includes]
    assert (
        expected_include_name in extracted_includes
    ), f"Expected include '{expected_include_name}' not found in extracted includes: {extracted_includes}"


def test_extract_includes_count(includes_cpp_code: str) -> None:
    """Test that we extract the expected number of includes"""
    driver_tree = CppCDriverTree.from_code(includes_cpp_code, "test.cpp")
    includes = driver_tree.extract_imports()

    # Should extract most includes (some might be skipped due to conditional compilation)
    assert (
        len(includes) >= 20
    ), f"Expected at least 20 includes, but found {len(includes)}"


@pytest.fixture(scope="module")
def function_definitions_cpp_code() -> str:
    """Load C++ function definitions test file"""
    file_path = (
        pathlib.Path(__file__).parent
        / "treesitter_testcases"
        / "cpp"
        / "test_func_defs.cpp"
    )
    with open(file_path, encoding="utf-8") as f:
        return f.read()


@pytest.mark.parametrize(
    "expected_function_name, expected_start_line, expected_end_line, expected_parent_path",
    [
        # Basic functions
        ("printMessage", 6, 8, ""),
        ("multiply", 11, 13, ""),
        ("divide", 16, 18, ""),
        ("maximum", 22, 24, ""),
        ("fibonacci", 27, 29, ""),
        ("square", 32, 34, ""),
        ("swap", 37, 41, ""),
        ("processVector", 44, 46, ""),
        # Namespace functions
        ("calculateArea", 50, 52, "MathUtils"),
        ("complexCalculation", 55, 57, "MathUtils::Advanced"),
        # Class constructors and methods
        ("Calculator", 68, 68, "Calculator"),  # Default constructor
        ("Calculator", 71, 71, "Calculator"),  # Parameterized constructor
        ("Calculator", 74, 74, "Calculator"),  # Copy constructor
        ("Calculator", 77, 79, "Calculator"),  # Move constructor
        ("~Calculator", 82, 82, "Calculator"),  # Destructor
        ("operator=", 85, 90, "Calculator"),
        ("operator=", 93, 99, "Calculator"),
        ("getValue", 102, 104, "Calculator"),
        ("setValue", 107, 109, "Calculator"),
        ("operator+", 112, 114, "Calculator"),
        ("operator-", 116, 118, "Calculator"),
        ("operator*", 120, 122, "Calculator"),
        ("operator/", 124, 126, "Calculator"),
        ("operator-", 129, 131, "Calculator"),  # Unary minus
        ("operator++", 134, 137, "Calculator"),  # Pre-increment
        ("operator++", 139, 143, "Calculator"),  # Post-increment
        ("operator==", 146, 148, "Calculator"),
        ("createZero", 151, 153, "Calculator"),
        # Template class methods
        ("Container", 163, 163, "Container"),
        ("getData", 165, 167, "Container"),
        ("setData", 169, 171, "Container"),
        ("convertAndSet", 174, 176, "Container"),
        # Inheritance
        ("~Shape", 182, 182, "Shape"),
        # (
        #     "calculateArea",
        #     183,
        #     183,
        #     "Shape",
        # ),  # Shape::calculateArea #TODO: known failure case, can mark as xfail
        ("draw", 184, 186, "Shape"),  # Shape::draw
        ("Circle", 194, 194, "Circle"),
        ("calculateArea", 196, 198, "Circle"),  # Circle::calculateArea
        ("draw", 200, 202, "Circle"),  # Circle::draw
        ("Rectangle", 210, 210, "Rectangle"),
        ("calculateArea", 212, 214, "Rectangle"),
        ("draw", 216, 218, "Rectangle"),
        # Lambda demonstrations
        ("demonstrateLambdas", 222, 234, ""),
        # TODO: we don't handle lambdas yet
        ("safeDivide", 237, 245, ""),
        ("maximum<bool>", 249, 251, ""),
        # Friend functions
        ("operator+", 261, 263, "Point"),  # Point friend operator
        ("operator<<", 265, 267, "Point"),  # Point friend ostream operator
        ("test", 278, 278, "MyClass"),
        ("operator+", 280, 280, "MyClass"),
        ("add", 284, 286, "MyClass"),
        ("display", 288, 290, "MyClass::Inner"),
        ("~MyClass", 292, 292, "MyClass"),
    ],
)
def test_extract_function_definitions(
    function_definitions_cpp_code: str,
    expected_function_name: str,
    expected_start_line: int,
    expected_end_line: int,
    expected_parent_path: str,
) -> None:
    """Test extraction of C++ function definitions"""
    # TODO: test scopes as well
    driver_tree = CppCDriverTree.from_code(function_definitions_cpp_code, "test.cpp")
    functions = driver_tree.extract_callable_definitions()

    extracted_functions = [
        (f.name, f.start_line, f.fully_qualified_parent_path) for f in functions
    ]

    # Check if the expected function is found
    matching_functions = [
        (name, line, parent_path)
        for name, line, parent_path in extracted_functions
        if name == expected_function_name and abs(line - expected_start_line) <= 2
    ]

    assert len(matching_functions) > 0, (
        f"Expected function '{expected_function_name}' around line {expected_start_line} "
        f"not found in extracted functions: {extracted_functions}"
    )

    # Verify the fully_qualified_parent_path for the matching function(s)
    for _name, line, parent_path in matching_functions:
        assert parent_path == expected_parent_path, (
            f"Function '{expected_function_name}' at line {line} has parent path '{parent_path}', "
            f"expected '{expected_parent_path}'"
        )


@pytest.fixture(scope="module")
def classes_cpp_code() -> str:
    """Load C++ classes test file"""
    file_path = (
        pathlib.Path(__file__).parent
        / "treesitter_testcases"
        / "cpp"
        / "test_classes.cpp"
    )
    with open(file_path, encoding="utf-8") as f:
        return f.read()


@pytest.mark.parametrize(
    "expected_class_name, expected_start_line, expected_end_line",
    [
        # Basic classes and structs
        ("BasicClass", 6, 13),
        ("AccessLevels", 16, 27),
        ("AbstractShape", 30, 36),
        ("Circle", 39, 57),
        ("Drawable", 60, 63),
        ("Serializable", 65, 68),
        ("DrawableShape", 70, 77),
        # Multiple inheritance
        ("Animal", 80, 87),
        ("Mammal", 89, 93),
        ("Bird", 95, 99),
        ("Bat", 101, 108),
        # Template classes
        ("Container", 112, 121),
        ("FixedMap", 125, 150),
        # ("Container", 154, 164),  # Template specialization # NOTE: known failure case
        # Nested classes
        ("Outer", 167, 188),
        ("Inner", 172, 179),
        # Friend classes
        ("FriendClass", 191, 198),
        ("FriendlyClass", 200, 205),
        # Other patterns
        ("Counter", 208, 221),
        ("ConstExample", 227, 243),
        ("FileWrapper", 246, 285),
        ("Logger", 289, 298),
        ("ConsolePrinter", 300, 307),
        ("Singleton", 310, 332),
        ("UsesForwardDeclaration", 341, 349),
        ("ForwardDeclared", 339, 339),
        ("AnonymousNamespaceClass", 371, 376),
    ],
)
def test_extract_class_definitions(
    classes_cpp_code: str,
    expected_class_name: str,
    expected_start_line: int,
    expected_end_line: int,
) -> None:
    """Test extraction of C++ class/struct definitions"""
    driver_tree = CppCDriverTree.from_code(classes_cpp_code, "test.cpp")
    data_structures = driver_tree.extract_data_structure_definitions()

    extracted_structures = [
        (ds.name, ds.start_line, ds.end_line) for ds in data_structures
    ]

    # Check if the expected class/struct is found
    matching_structures = [
        (name, line)
        for name, line, _ in extracted_structures
        if name == expected_class_name and abs(line - expected_start_line) <= 3
    ]

    assert len(matching_structures) > 0, (
        f"Expected class/struct '{expected_class_name}' around line {expected_start_line}-{expected_end_line} "
        f"not found in extracted structures: {extracted_structures}"
    )


@pytest.fixture(scope="module")
def enums_cpp_code() -> str:
    """Load C++ enums test file"""
    file_path = (
        pathlib.Path(__file__).parent
        / "treesitter_testcases"
        / "cpp"
        / "test_enums.cpp"
    )
    with open(file_path, encoding="utf-8") as f:
        return f.read()


@pytest.mark.parametrize(
    "expected_enum_name, expected_start_line",
    [
        ("Color", 4),
        ("StatusCode", 10),
        ("Priority", 17),
        ("Direction", 23),
        ("Grade", 30),
        (None, 38),  # Anonymous enum
        ("NetworkState", 41),  # Forward declaration
        ("RenderMode", 45),
        ("BlendMode", 51),
        ("EntityType", 62),
        ("MovementType", 67),
        ("FilePermissions", 87),
        ("AccessFlags", 95),
        ("NetworkState", 111),  # Definition of forward declared enum
        ("InsertionPolicy", 119),
        ("SortOrder", 125),
        ("DebugLevel", 197),
        ("WeekDay", 205),
        ("WeekEnd", 205),  # Multiple enums in single statement
    ],
)
def test_extract_enums(
    enums_cpp_code: str,
    expected_enum_name: str | None,
    expected_start_line: int,
) -> None:
    """Test extraction of C++ enum definitions"""
    driver_tree = CppCDriverTree.from_code(enums_cpp_code, "test.cpp")
    data_structures = driver_tree.extract_data_structure_definitions()

    extracted_structures = [(ds.name, ds.start_line) for ds in data_structures]

    # Check if the expected enum is found
    matching_structures = [
        (name, line)
        for name, line in extracted_structures
        if name == expected_enum_name and abs(line - expected_start_line) <= 3
    ]

    assert len(matching_structures) > 0, (
        f"Expected enum '{expected_enum_name}' around line {expected_start_line} "
        f"not found in extracted structures: {extracted_structures}"
    )


@pytest.fixture(scope="module")
def namespaces_cpp_code() -> str:
    """Load C++ namespaces test file"""
    file_path = (
        pathlib.Path(__file__).parent
        / "treesitter_testcases"
        / "cpp"
        / "test_namespaces.cpp"
    )
    with open(file_path, encoding="utf-8") as f:
        return f.read()


@pytest.mark.parametrize(
    "expected_namespace_name, expected_start_line",
    [
        ("Math", 6),
        ("Graphics", 17),  # From Graphics::Rendering::OpenGL
        ("Network", 27),
        ("TCP", 28),
        ("UDP", 39),
        ("Containers", 59),
        ("Constants", 98),
        ("Physics", 103),
        ("Time", 109),
        ("Utils", 118),
        ("Math", 142),  # Reopened namespace
        ("Version", 172),
        ("v2", 173),
        ("v1", 180),
        ("Geometry", 188),
        ("Database", 220),
        ("std", 244),  # std specialization
    ],
)
def test_extract_namespaces(
    namespaces_cpp_code: str,
    expected_namespace_name: str,
    expected_start_line: int,
) -> None:
    """Test extraction of C++ namespace definitions"""
    driver_tree = CppCDriverTree.from_code(namespaces_cpp_code, "test.cpp")
    data_structures = driver_tree.extract_data_structure_definitions()

    extracted_structures = [(ds.name, ds.start_line) for ds in data_structures]

    # Check if the expected namespace is found
    matching_structures = [
        (name, line)
        for name, line in extracted_structures
        if name == expected_namespace_name and abs(line - expected_start_line) <= 3
    ]

    assert len(matching_structures) > 0, (
        f"Expected namespace '{expected_namespace_name}' around line {expected_start_line} "
        f"not found in extracted structures: {extracted_structures}"
    )


@pytest.fixture(scope="module")
def variables_cpp_code() -> str:
    """Load C++ variables test file"""
    file_path = (
        pathlib.Path(__file__).parent
        / "treesitter_testcases"
        / "cpp"
        / "test_variables.cpp"
    )
    with open(file_path, encoding="utf-8") as f:
        return f.read()


@pytest.mark.parametrize(
    "expected_variable_name, expected_start_line, expected_end_line",
    [
        # Basic global variables
        ("global_int", 9, 9),
        ("global_double", 10, 10),
        ("global_string", 11, 11),
        ("global_flag", 12, 12),
        # Const and constexpr variables
        ("CONST_VALUE", 15, 15),
        ("CONSTEXPR_PI", 16, 16),
        ("CONST_STRING", 17, 17),
        ("int_pointer", 28, 28),
        ("const_int_pointer", 29, 29),
        ("pointer_to_const", 30, 30),
        ("const_pointer_to_const", 31, 31),
        ("auto_int", 38, 38),
        ("auto_double", 39, 39),
        ("auto_string", 40, 40),
        ("auto_vector", 41, 41),
        ("decltype_int", 44, 44),
        ("decltype_auto_var", 45, 45),
        ("global_array", 48, 48),
        ("matrix", 49, 49),
        ("string_array", 50, 50),
        ("global_vector", 53, 53),
        ("string_vector", 54, 54),
        ("unique_int_ptr", 57, 57),
        ("shared_string_ptr", 58, 58),
        ("weak_string_ptr", 59, 59),
        ("atomic_counter", 62, 62),
        ("thread_local_var", 63, 63),
        ("function_pointer", 66, 66),
        ("lambda_var", 67, 67),
        # ('pi', 71, 71), # TODO: special case - under a tempalte node, not translation unit
        # ('anonymous_global', 75, 75), # TODO: do we document variables inside of a non-global namespace?
        ("debug_level", 93, 93),
        # ('BUFFER_SIZE', 102, 102), # TODO: support macros?
    ],
)
def test_extract_variables(
    variables_cpp_code: str,
    expected_variable_name: str,
    expected_start_line: int,
    expected_end_line: int,
) -> None:
    """Test extraction of C++ global variables"""
    driver_tree = CppCDriverTree.from_code(variables_cpp_code, "test.cpp")
    variables = driver_tree.extract_variables()

    extracted_variables = [(v.name, v.start_line, v.end_line) for v in variables]

    # Check if the expected variable is found
    matching_variables = [
        (name, line, end_line)
        for name, line, end_line in extracted_variables
        if name == expected_variable_name and abs(line - expected_start_line) <= 3
    ]

    assert len(matching_variables) > 0, (
        f"Expected variable '{expected_variable_name}' around line {expected_start_line} "
        f"not found in extracted variables: {extracted_variables}"
    )


@pytest.fixture(scope="module")
def function_calls_cpp_code() -> str:
    """Load C++ function calls test file"""
    file_path = (
        pathlib.Path(__file__).parent
        / "treesitter_testcases"
        / "cpp"
        / "test_func_calls.cpp"
    )
    with open(file_path, encoding="utf-8") as f:
        return f.read()


@pytest.mark.parametrize(
    "expected_function_call_name, expected_start_line, expected_end_line, expected_qualified_parent_path",
    [
        # Basic function calls
        ("add", 84, 84, "main"),
        ("multiply", 85, 85, "main"),
        ("printMessage", 86, 86, "main"),
        # Template function calls
        # ("maximum", 98),
        # ("maximum", 99),
        # ("maximum", 100),
        # # Namespace qualified calls
        # ("square", 103),
        # ("power", 104),
        # ("logarithm", 105),
        # # Member function calls
        # ("getValue", 109),
        # ("setValue", 110),
        # # Method chaining
        # ("add", 113),
        # ("multiply", 113),
        # ("add", 113),
        # # Static method calls
        # ("createZero", 116),
        # ("createOne", 117),
        # # Constructor calls
        # ("Calculator", 134),
        # ("Calculator", 135),
        # ("Calculator", 136),
        # # Template class method calls
        # ("get", 139),
        # ("set", 140),
        # ("convertFrom", 141),
        # ("get", 144),
        # ("convertFrom", 145),
        # # STL function calls
        # ("sort", 150),
        # ("find", 151),
        # ("count_if", 152),
        # ("push_back", 155),
        # ("pop_back", 156),
        # ("size", 157),
        # ("empty", 158),
        # # Lambda calls
        # ("lambda_add", 171),
        # ("capture_lambda", 175),
        # # Function object calls
        # ("func_obj", 179),
        # ("func_obj", 182),
        # # Smart pointer method calls
        # ("getValue", 194),
        # ("setValue", 195),
        # ("getValue", 198),
        # # Type conversion calls
        # ("static_cast", 202),
        # ("static_cast", 203),
        # # Various other calls
        # ("makeUnique", 246),
        # ("make_shared", 193),
        # ("make_unique", 197),
    ],
)
def test_extract_function_calls(
    function_calls_cpp_code: str,
    expected_function_call_name: str,
    expected_start_line: int,
    expected_end_line: int,
    expected_qualified_parent_path: str,
) -> None:
    """Test extraction of C++ function calls"""
    driver_tree = CppCDriverTree.from_code(function_calls_cpp_code, "test.cpp")
    function_calls = driver_tree.extract_function_calls()

    extracted_calls = [
        (call.name, call.start_line, call.end_line, call.fully_qualified_parent_path)
        for call in function_calls
    ]

    # Check if the expected function call is found
    matching_calls = [
        (name, line, end_line, parent_path)
        for name, line, end_line, parent_path in extracted_calls
        if name == expected_function_call_name and abs(line - expected_start_line) <= 2
    ]

    assert len(matching_calls) > 0, (
        f"Expected function call '{expected_function_call_name}' around line {expected_start_line} "
        f"not found in extracted calls: {extracted_calls}"
    )

    # Verify the fully_qualified_parent_path for the matching function(s)
    for _name, line, _end_line, parent_path in matching_calls:
        assert parent_path == expected_qualified_parent_path, (
            f"Function '{expected_function_call_name}' at line {line} has parent path '{parent_path}', "
            f"expected '{expected_qualified_parent_path}'"
        )


@pytest.fixture(scope="module")
def function_declarations_cpp_code() -> str:
    """Load C++ function declarations test file"""
    file_path = (
        pathlib.Path(__file__).parent
        / "treesitter_testcases"
        / "cpp"
        / "test_func_declarations.cpp"
    )
    with open(file_path, encoding="utf-8") as f:
        return f.read()


@pytest.mark.parametrize(
    "expected_function_name, expected_start_line, expected_end_line, expected_parent_path",
    [
        # Basic function declarations
        ("add", 7, 7, ""),
        ("multiply", 8, 8, ""),
        ("printMessage", 9, 9, ""),
        ("concatenate", 10, 10, ""),
        # Function declarations with default parameters
        ("divide", 13, 13, ""),
        ("setupConnection", 14, 14, ""),
        # Function declarations with references
        ("processData", 17, 17, ""),
        ("swapValues", 18, 18, ""),
        ("processString", 19, 19, ""),
        # Rvalue reference functions
        ("processVector", 22, 22, ""),
        ("moveString", 23, 23, ""),
        # Template function declarations
        ("maximum", 27, 27, ""),
        ("addValues", 30, 30, ""),
        ("allOf", 33, 33, ""),
        ("callFunction", 37, 37, ""),
        # Constexpr functions
        ("factorial", 40, 40, ""),
        ("calculateCircleArea", 41, 41, ""),
        # Inline functions
        ("square", 44, 44, ""),
        ("cube", 45, 45, ""),
        # Noexcept functions
        ("safeFunction", 48, 48, ""),
        ("safeMath", 49, 49, ""),
        ("conditionalNoexcept", 50, 50, ""),
        # Auto return type functions
        ("detectType", 53, 53, ""),
        ("computeValue", 54, 54, ""),
        # Namespace function declarations
        ("sin", 58, 58, "Math"),
        ("cos", 59, 59, "Math"),
        ("pow", 60, 60, "Math"),
        ("integrate", 63, 63, "Math::Advanced"),
        ("solve", 64, 64, "Math::Advanced"),
        # Global operator overloads
        ("Calculator", 75, 75, "Calculator"),  # Constructor
        ("Calculator", 76, 76, "Calculator"),  # Copy constructor
        ("Calculator", 77, 77, "Calculator"),  # Copy constructor
        ("Calculator", 78, 78, "Calculator"),  # Copy constructor
        ("~Calculator", 81, 81, "Calculator"),  # Destructor
        ("operator=", 84, 84, "Calculator"),
        ("operator=", 85, 85, "Calculator"),
        ("getValue", 88, 88, "Calculator"),
        ("setValue", 89, 89, "Calculator"),
        ("reset", 90, 90, "Calculator"),
        ("isZero", 93, 93, "Calculator"),
        ("isPositive", 94, 94, "Calculator"),
        ("toString", 95, 95, "Calculator"),
        ("createZero", 98, 98, "Calculator"),
        ("createFromString", 99, 99, "Calculator"),
        ("isValidValue", 100, 100, "Calculator"),
        ("operator+", 103, 103, "Calculator"),
        ("operator-", 104, 104, "Calculator"),
        ("operator*", 105, 105, "Calculator"),
        ("operator/", 106, 106, "Calculator"),
        ("operator+=", 108, 108, "Calculator"),
        ("operator-=", 109, 109, "Calculator"),
        ("operator*=", 110, 110, "Calculator"),
        ("operator*=", 111, 111, "Calculator"),
        ("operator++", 113, 113, "Calculator"),
        ("operator++", 114, 114, "Calculator"),
        ("operator-", 116, 116, "Calculator"),
        ("operator+", 117, 117, "Calculator"),
        ("operator[]", 127, 127, "Calculator"),  # Array subscript operator
        # ("double", 131, 131, "Calculator"),  # Conversion operator to double #TODO: known failure case, can mark as xfail
        # ("int", 133, 133, "Calculator"),  # Conversion operator to int #TODO: known failure case, can mark as xfail
        ("Container", 143, 143, "Container"),  # Template class constructor
        ("Container", 144, 144, "Container"),  # Template class constructor
        ("Container", 145, 145, "Container"),  # Template class constructor
        ("Container", 146, 146, "Container"),  # Template class constructor
        ("~Container", 148, 148, "Container"),  # Template class constructor
        ("operator=", 150, 150, "Container"),  # Template class constructor
        ("get", 153, 153, "Container"),  # Template class method
        ("getPerimeter", 205, 205, "Shape"),
        ("clone", 211, 211, "Shape"),
        ("maximum<bool>", 236, 236, ""),
        ("importantFunction", 300, 300, ""),
    ],
)
def test_extract_function_declarations(
    function_declarations_cpp_code: str,
    expected_function_name: str,
    expected_start_line: int,
    expected_end_line: int,
    expected_parent_path: str,
) -> None:
    """Test extraction of C++ function declarations"""
    driver_tree = CppCDriverTree.from_code(function_declarations_cpp_code, "test.cpp")
    declarations = driver_tree.extract_function_declarations()

    extracted_declarations = [
        (decl.name, decl.start_line, decl.end_line, decl.fully_qualified_parent_path)
        for decl in declarations
    ]

    # Check if the expected function declaration is found
    matching_declarations = [
        (name, line, end_line, fully_qualified_parent_path)
        for name, line, end_line, fully_qualified_parent_path in extracted_declarations
        if name == expected_function_name and abs(line - expected_start_line) <= 3
    ]

    assert len(matching_declarations) > 0, (
        f"Expected function declaration '{expected_function_name}' around line {expected_start_line} "
        f"not found in extracted declarations: {extracted_declarations}"
    )

    # Verify the fully_qualified_parent_path for the matching function(s)
    for _name, line, _end_line, parent_path in matching_declarations:
        assert parent_path == expected_parent_path, (
            f"Function '{expected_function_name}' at line {line} has parent path '{parent_path}', "
            f"expected '{expected_parent_path}'"
        )


class TestCppSpecificFeatures:
    """Test C++-specific features that don't exist in C"""

    def test_namespace_extraction(self, namespaces_cpp_code: str) -> None:
        """Test that we can extract namespaces (C++ specific)"""
        driver_tree = CppCDriverTree.from_code(namespaces_cpp_code, "test.cpp")
        data_structures = driver_tree.extract_data_structure_definitions()

        namespace_names = [
            ds.name
            for ds in data_structures
            if ds.name in ["Math", "Network", "Graphics"]
        ]
        assert len(namespace_names) > 0, "Should extract namespace definitions"

    def test_class_extraction(self, classes_cpp_code: str) -> None:
        """Test that we can extract classes (C++ enhanced)"""
        driver_tree = CppCDriverTree.from_code(classes_cpp_code, "test.cpp")
        data_structures = driver_tree.extract_data_structure_definitions()

        class_names = [
            ds.name
            for ds in data_structures
            if ds.name in ["BasicClass", "Calculator", "Container"]
        ]
        assert len(class_names) > 0, "Should extract class definitions"

    def test_template_extraction(self, function_definitions_cpp_code: str) -> None:
        """Test that we can extract template functions"""
        driver_tree = CppCDriverTree.from_code(
            function_definitions_cpp_code, "test.cpp"
        )
        functions = driver_tree.extract_callable_definitions()

        # Should extract template functions like maximum, Container methods, etc.
        template_functions = [
            f.name for f in functions if f.name in ["maximum", "getData", "setData"]
        ]
        assert (
            len(template_functions) > 0
        ), "Should extract template function definitions"

    def test_operator_overload_extraction(
        self, function_definitions_cpp_code: str
    ) -> None:
        """Test that we can extract operator overloads"""
        driver_tree = CppCDriverTree.from_code(
            function_definitions_cpp_code, "test.cpp"
        )
        functions = driver_tree.extract_callable_definitions()

        operator_functions = [
            f.name for f in functions if f.name.startswith("operator")
        ]
        assert (
            len(operator_functions) > 0
        ), "Should extract operator overload definitions"

    def test_constructor_destructor_extraction(
        self, function_definitions_cpp_code: str
    ) -> None:
        """Test that we can extract constructors and destructors"""
        driver_tree = CppCDriverTree.from_code(
            function_definitions_cpp_code, "test.cpp"
        )
        functions = driver_tree.extract_callable_definitions()

        # Look for Calculator constructors
        calculator_constructors = [f.name for f in functions if f.name == "Calculator"]
        assert (
            len(calculator_constructors) >= 3
        ), "Should extract multiple Calculator constructors"

    def test_method_calls_extraction(self, function_calls_cpp_code: str) -> None:
        """Test that we can extract method calls"""
        driver_tree = CppCDriverTree.from_code(function_calls_cpp_code, "test.cpp")
        function_calls = driver_tree.extract_function_calls()

        # Should extract method calls like getValue, setValue, etc.
        method_calls = [
            call.name
            for call in function_calls
            if call.name in ["getValue", "setValue", "push_back", "size"]
        ]
        assert len(method_calls) > 0, "Should extract method calls"

    def test_enum_class_extraction(self, enums_cpp_code: str) -> None:
        """Test that we can extract enum classes (C++11 feature)"""
        driver_tree = CppCDriverTree.from_code(enums_cpp_code, "test.cpp")
        data_structures = driver_tree.extract_data_structure_definitions()

        # Should extract scoped enums like Priority, Direction, Grade
        enum_names = [
            ds.name
            for ds in data_structures
            if ds.name in ["Priority", "Direction", "Grade"]
        ]
        assert len(enum_names) > 0, "Should extract enum class definitions"


def test_no_local_variables_extracted() -> None:
    """Test that local variables are not extracted as global variables"""
    code = """
    int global_var = 42;

    void function() {
        int local_var = 10;
        static int static_local = 20;
    }

    int main() {
        int main_local = 30;
        return 0;
    }
    """

    driver_tree = CppCDriverTree.from_code(code, "test.cpp")
    variables = driver_tree.extract_variables()

    variable_names = [v.name for v in variables]

    # Should only extract global_var, not local variables
    assert "global_var" in variable_names, "Should extract global variable"
    assert "local_var" not in variable_names, "Should not extract local variable"
    assert (
        "static_local" not in variable_names
    ), "Should not extract static local variable"
    assert "main_local" not in variable_names, "Should not extract main local variable"


def test_cpp_vs_c_differences() -> None:
    """Test that C++ driver extracts C++ specific features that C driver cannot"""
    cpp_code = """
    namespace MyNamespace {
        class MyClass {
        public:
            MyClass() = default;
            virtual ~MyClass() = default;

            MyClass operator+(const MyClass& other) const;
            template<typename T>
            void templateMethod(T value);
        };

        enum class Color { RED, GREEN, BLUE };
    }

    template<typename T>
    T templateFunction(T a, T b) {
        return a + b;
    }
    """

    driver_tree = CppCDriverTree.from_code(cpp_code, "test.cpp")

    # Test data structures
    data_structures = driver_tree.extract_data_structure_definitions()
    structure_names = [ds.name for ds in data_structures]

    assert "MyNamespace" in structure_names, "Should extract namespace"
    assert "MyClass" in structure_names, "Should extract class"
    assert "Color" in structure_names, "Should extract enum class"

    # Test functions
    functions = driver_tree.extract_callable_definitions()
    function_names = [f.name for f in functions]

    assert "MyClass" in function_names, "Should extract constructor"
    assert "templateFunction" in function_names, "Should extract template function"
