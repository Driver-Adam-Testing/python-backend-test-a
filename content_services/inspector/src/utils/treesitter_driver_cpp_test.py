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
    "expected_function_name, expected_start_line",
    [
        # Basic functions
        ("add", 4),
        ("printMessage", 8),
        ("multiply", 13),
        ("divide", 18),
        ("maximum", 23),
        ("fibonacci", 28),
        ("square", 33),
        ("swap", 38),
        ("processVector", 44),
        # Namespace functions
        ("calculateArea", 49),
        ("complexCalculation", 54),
        # Class constructors and methods
        ("Calculator", 62),  # Default constructor
        ("Calculator", 65),  # Parameterized constructor
        ("Calculator", 68),  # Copy constructor
        ("Calculator", 71),  # Move constructor
        ("getValue", 83),
        ("setValue", 87),
        ("operator+", 91),
        ("operator-", 95),
        ("operator*", 99),
        ("operator/", 103),
        ("operator-", 107),  # Unary minus
        ("operator++", 111),  # Pre-increment
        ("operator++", 116),  # Post-increment
        ("operator==", 122),
        ("operator!=", 126),
        ("operator<", 130),
        ("operator()", 134),
        ("operator[]", 138),
        ("createZero", 142),
        # Template class methods
        ("Container", 148),
        ("getData", 152),
        ("setData", 156),
        ("convertAndSet", 160),
        # Inheritance
        ("calculateArea", 177),  # Circle::calculateArea
        ("draw", 181),  # Circle::draw
        ("calculateArea", 195),  # Rectangle::calculateArea
        ("draw", 199),  # Rectangle::draw
        # Lambda demonstrations
        ("demonstrateLambdas", 208),
        # Friend functions
        ("operator+", 238),  # Point friend operator
        ("operator<<", 242),  # Point friend ostream operator
        # Main function
        ("main", 248),
    ],
)
def test_extract_function_definitions(
    function_definitions_cpp_code: str,
    expected_function_name: str,
    expected_start_line: int,
) -> None:
    """Test extraction of C++ function definitions"""
    driver_tree = CppCDriverTree.from_code(function_definitions_cpp_code, "test.cpp")
    functions = driver_tree.extract_callable_definitions()

    extracted_functions = [(f.name, f.start_line) for f in functions]

    # Check if the expected function is found
    matching_functions = [
        (name, line)
        for name, line in extracted_functions
        if name == expected_function_name and abs(line - expected_start_line) <= 2
    ]

    assert len(matching_functions) > 0, (
        f"Expected function '{expected_function_name}' around line {expected_start_line} "
        f"not found in extracted functions: {extracted_functions}"
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
        ("Container", 154, 164),  # Template specialization
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
    data_structures = driver_tree.extract_class_definitions()

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
    "expected_variable_name, expected_start_line",
    [
        # Basic global variables
        ("global_int", 8),
        ("global_double", 9),
        ("global_string", 10),
        ("global_flag", 11),
        # Const and constexpr variables
        ("CONST_VALUE", 14),
        ("CONSTEXPR_PI", 15),
        ("CONST_STRING", 16),
        # Static variables
        ("static_counter", 19),
        ("static_message", 20),
        # Pointer variables
        ("int_pointer", 26),
        ("const_int_pointer", 27),
        ("pointer_to_const", 28),
        ("const_pointer_to_const", 29),
        # Reference variables
        ("int_reference", 32),
        ("const_reference", 33),
        # Auto variables
        ("auto_int", 36),
        ("auto_double", 37),
        ("auto_string", 38),
        ("auto_vector", 39),
        # Array variables
        ("global_array", 46),
        ("matrix", 47),
        ("string_array", 48),
        # Container variables
        ("global_vector", 51),
        ("string_vector", 52),
        # Smart pointers
        ("unique_int_ptr", 55),
        ("shared_string_ptr", 56),
        ("weak_string_ptr", 57),
        # Thread variables
        ("atomic_counter", 60),
        ("thread_local_var", 61),
        # Function pointers and lambdas
        ("function_pointer", 64),
        ("lambda_var", 65),
        # Various other variable types
        ("retry_count", 80),
        ("global_buffer", 79),
        ("current_color", 129),
        ("origin", 136),
        ("destination", 137),
        ("times_two", 145),
        ("times_three", 146),
        ("global_flags", 160),
        ("global_data", 168),
        ("key_value_pairs", 171),
        ("matrix_vector", 177),
        ("INLINE_VERSION", 188),
        ("inline_counter", 189),
    ],
)
def test_extract_variables(
    variables_cpp_code: str,
    expected_variable_name: str,
    expected_start_line: int,
) -> None:
    """Test extraction of C++ global variables"""
    driver_tree = CppCDriverTree.from_code(variables_cpp_code, "test.cpp")
    variables = driver_tree.extract_variables()

    extracted_variables = [(v.name, v.start_line) for v in variables]

    # Check if the expected variable is found
    matching_variables = [
        (name, line)
        for name, line in extracted_variables
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
    "expected_function_call_name, expected_start_line",
    [
        # Basic function calls
        ("add", 93),
        ("multiply", 94),
        ("printMessage", 95),
        # Template function calls
        ("maximum", 98),
        ("maximum", 99),
        ("maximum", 100),
        # Namespace qualified calls
        ("square", 103),
        ("power", 104),
        ("logarithm", 105),
        # Member function calls
        ("getValue", 109),
        ("setValue", 110),
        # Method chaining
        ("add", 113),
        ("multiply", 113),
        ("add", 113),
        # Static method calls
        ("createZero", 116),
        ("createOne", 117),
        # Constructor calls
        ("Calculator", 134),
        ("Calculator", 135),
        ("Calculator", 136),
        # Template class method calls
        ("get", 139),
        ("set", 140),
        ("convertFrom", 141),
        ("get", 144),
        ("convertFrom", 145),
        # STL function calls
        ("sort", 150),
        ("find", 151),
        ("count_if", 152),
        ("push_back", 155),
        ("pop_back", 156),
        ("size", 157),
        ("empty", 158),
        # Lambda calls
        ("lambda_add", 171),
        ("capture_lambda", 175),
        # Function object calls
        ("func_obj", 179),
        ("func_obj", 182),
        # Smart pointer method calls
        ("getValue", 194),
        ("setValue", 195),
        ("getValue", 198),
        # Type conversion calls
        ("static_cast", 202),
        ("static_cast", 203),
        # Various other calls
        ("makeUnique", 246),
        ("make_shared", 193),
        ("make_unique", 197),
    ],
)
def test_extract_function_calls(
    function_calls_cpp_code: str,
    expected_function_call_name: str,
    expected_start_line: int,
) -> None:
    """Test extraction of C++ function calls"""
    driver_tree = CppCDriverTree.from_code(function_calls_cpp_code, "test.cpp")
    function_calls = driver_tree.extract_function_calls()

    extracted_calls = [(call.name, call.start_line) for call in function_calls]

    # Check if the expected function call is found
    matching_calls = [
        (name, line)
        for name, line in extracted_calls
        if name == expected_function_call_name and abs(line - expected_start_line) <= 2
    ]

    assert len(matching_calls) > 0, (
        f"Expected function call '{expected_function_call_name}' around line {expected_start_line} "
        f"not found in extracted calls: {extracted_calls}"
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
    "expected_function_name, expected_start_line",
    [
        # Basic function declarations
        ("add", 7),
        ("multiply", 8),
        ("printMessage", 9),
        ("concatenate", 10),
        # Function declarations with default parameters
        ("divide", 13),
        ("setupConnection", 14),
        # Function declarations with references
        ("processData", 17),
        ("swapValues", 18),
        ("processString", 19),
        # Rvalue reference functions
        ("processVector", 22),
        ("moveString", 23),
        # Template function declarations
        ("maximum", 26),
        ("addValues", 29),
        ("allOf", 32),
        ("callFunction", 35),
        # Constexpr functions
        ("factorial", 38),
        ("calculateCircleArea", 39),
        # Inline functions
        ("square", 42),
        ("cube", 43),
        # Noexcept functions
        ("safeFunction", 46),
        ("safeMath", 47),
        ("conditionalNoexcept", 48),
        # Auto return type functions
        ("detectType", 51),
        ("computeValue", 52),
        # Namespace function declarations
        ("sin", 56),
        ("cos", 57),
        ("pow", 58),
        ("integrate", 61),
        ("solve", 62),
        # Global operator overloads
        ("operator+", 268),
        ("operator-", 269),
        ("operator*", 270),
        ("operator/", 271),
        ("operator<<", 273),
        ("operator>>", 274),
        # Function pointer declarations
        ("applyBinaryFunction", 283),
        ("executeCallback", 284),
        ("processWithFunction", 285),
        # Variadic template functions
        ("print", 288),
        ("makeUnique", 291),
        ("invoke", 294),
    ],
)
def test_extract_function_declarations(
    function_declarations_cpp_code: str,
    expected_function_name: str,
    expected_start_line: int,
) -> None:
    """Test extraction of C++ function declarations"""
    driver_tree = CppCDriverTree.from_code(function_declarations_cpp_code, "test.cpp")
    declarations = driver_tree.extract_function_declarations()

    extracted_declarations = [(decl.name, decl.start_line) for decl in declarations]

    # Check if the expected function declaration is found
    matching_declarations = [
        (name, line)
        for name, line in extracted_declarations
        if name == expected_function_name and abs(line - expected_start_line) <= 3
    ]

    assert len(matching_declarations) > 0, (
        f"Expected function declaration '{expected_function_name}' around line {expected_start_line} "
        f"not found in extracted declarations: {extracted_declarations}"
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
