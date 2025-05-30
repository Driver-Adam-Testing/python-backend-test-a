from utils.treesitter_driver import CppCDriverTree


def test_fully_qualified_path_global_class() -> None:
    """Test that a global class has empty parent path."""
    code = """
class GlobalClass {
public:
    int x;
};
"""
    driver_tree = CppCDriverTree.from_code(code, "test.cpp")
    classes = driver_tree.extract_class_definitions()

    assert len(classes) == 1
    assert classes[0].name == "GlobalClass"
    assert classes[0].fully_qualified_parent_path == ""


def test_fully_qualified_path_namespace() -> None:
    """Test class inside namespace."""
    code = """
namespace MyNamespace {
    class InnerClass {
    public:
        int y;
    };
}
"""
    driver_tree = CppCDriverTree.from_code(code, "test.cpp")
    classes = driver_tree.extract_class_definitions()

    assert len(classes) == 1
    assert classes[0].name == "InnerClass"
    assert classes[0].fully_qualified_parent_path == "MyNamespace"


def test_fully_qualified_path_nested_namespaces() -> None:
    """Test class inside nested namespaces."""
    code = """
namespace Outer {
    namespace Inner {
        class NestedClass {
        public:
            int z;
        };
    }
}
"""
    driver_tree = CppCDriverTree.from_code(code, "test.cpp")
    classes = driver_tree.extract_class_definitions()

    assert len(classes) == 1
    assert classes[0].name == "NestedClass"
    assert classes[0].fully_qualified_parent_path == "Outer::Inner"


def test_fully_qualified_path_nested_classes() -> None:
    """Test nested classes inside a parent class."""
    code = """
class OuterClass {
public:
    class InnerClass {
    public:
        int a;
    };
};
"""
    driver_tree = CppCDriverTree.from_code(code, "test.cpp")
    classes = driver_tree.extract_class_definitions()

    # Should find both outer and inner classes
    assert len(classes) == 2

    # Find the classes by name
    outer_class = next(c for c in classes if c.name == "OuterClass")
    inner_class = next(c for c in classes if c.name == "InnerClass")

    assert outer_class.fully_qualified_parent_path == ""
    assert inner_class.fully_qualified_parent_path == "OuterClass"


def test_fully_qualified_path_namespace_and_nested_class() -> None:
    """Test class nested inside both namespace and class."""
    code = """
namespace MyNamespace {
    class OuterClass {
    public:
        class InnerClass {
        public:
            int value;
        };
    };
}
"""
    driver_tree = CppCDriverTree.from_code(code, "test.cpp")
    classes = driver_tree.extract_class_definitions()

    assert len(classes) == 2

    outer_class = next(c for c in classes if c.name == "OuterClass")
    inner_class = next(c for c in classes if c.name == "InnerClass")

    assert outer_class.fully_qualified_parent_path == "MyNamespace"
    assert inner_class.fully_qualified_parent_path == "MyNamespace::OuterClass"


def test_fully_qualified_path_mixed_structures() -> None:
    """Test class nested inside struct and enum."""
    code = """
namespace TestNamespace {
    struct OuterStruct {
        enum OuterEnum {
            VALUE1, VALUE2
        };

        class NestedClass {
        public:
            int data;
        };
    };
}
"""
    driver_tree = CppCDriverTree.from_code(code, "test.cpp")
    classes = driver_tree.extract_class_definitions()

    assert len(classes) == 1
    nested_class = classes[0]

    assert nested_class.name == "NestedClass"
    assert nested_class.fully_qualified_parent_path == "TestNamespace::OuterStruct"


def test_fully_qualified_path_deeply_nested() -> None:
    """Test deeply nested structure."""
    code = """
namespace Level1 {
    namespace Level2 {
        class Class1 {
        public:
            struct Struct1 {
                class Class2 {
                public:
                    int deeply_nested;
                };
            };
        };
    }
}
"""
    driver_tree = CppCDriverTree.from_code(code, "test.cpp")
    classes = driver_tree.extract_class_definitions()

    assert len(classes) == 2

    class1 = next(c for c in classes if c.name == "Class1")
    class2 = next(c for c in classes if c.name == "Class2")

    assert class1.fully_qualified_parent_path == "Level1::Level2"
    assert class2.fully_qualified_parent_path == "Level1::Level2::Class1::Struct1"


def test_fully_qualified_path_anonymous_namespace() -> None:
    """Test class inside anonymous namespace."""
    code = """
namespace {
    class AnonClass {
    public:
        int x;
    };
}
"""
    driver_tree = CppCDriverTree.from_code(code, "test.cpp")
    classes = driver_tree.extract_class_definitions()

    assert len(classes) == 1
    assert classes[0].name == "AnonClass"
    assert classes[0].fully_qualified_parent_path == "(anonymous)"


def test_fully_qualified_path_nested_anonymous_namespaces() -> None:
    """Test class inside nested anonymous namespaces."""
    code = """
namespace {
    namespace {
        class DeepAnonClass {
        public:
            int z;
        };
    }
}
"""
    driver_tree = CppCDriverTree.from_code(code, "test.cpp")
    classes = driver_tree.extract_class_definitions()

    assert len(classes) == 1
    assert classes[0].name == "DeepAnonClass"
    assert classes[0].fully_qualified_parent_path == "(anonymous)::(anonymous)"


def test_fully_qualified_path_mixed_named_and_anonymous() -> None:
    """Test class inside mix of named and anonymous namespaces."""
    code = """
namespace Named {
    namespace {
        class MixedClass {
        public:
            int value;
        };
    }
}

namespace {
    namespace Named2 {
        class AnotherMixedClass {
        public:
            int value2;
        };
    }
}
"""
    driver_tree = CppCDriverTree.from_code(code, "test.cpp")
    classes = driver_tree.extract_class_definitions()

    assert len(classes) == 2

    mixed_class = next(c for c in classes if c.name == "MixedClass")
    another_mixed_class = next(c for c in classes if c.name == "AnotherMixedClass")

    assert mixed_class.fully_qualified_parent_path == "Named::(anonymous)"
    assert another_mixed_class.fully_qualified_parent_path == "(anonymous)::Named2"


def test_fully_qualified_path_anonymous_with_nested_classes() -> None:
    """Test nested classes inside anonymous namespace."""
    code = """
namespace {
    class OuterAnonClass {
    public:
        class InnerAnonClass {
        public:
            int data;
        };
    };
}
"""
    driver_tree = CppCDriverTree.from_code(code, "test.cpp")
    classes = driver_tree.extract_class_definitions()

    assert len(classes) == 2

    outer_class = next(c for c in classes if c.name == "OuterAnonClass")
    inner_class = next(c for c in classes if c.name == "InnerAnonClass")

    assert outer_class.fully_qualified_parent_path == "(anonymous)"
    assert inner_class.fully_qualified_parent_path == "(anonymous)::OuterAnonClass"


def test_extract_function_calls_within_function_definition() -> None:
    """Test function calls contained within a function definition."""
    code = """
void helper_function() {
    // Helper function
}

int add(int a, int b) {
    return a + b;
}

void main_function() {
    helper_function();
    int result = add(5, 10);
}
"""
    driver_tree = CppCDriverTree.from_code(code, "test.cpp")
    function_calls = driver_tree.extract_function_calls()

    # Find the function calls within main_function
    calls_in_main = [
        call
        for call in function_calls
        if call.fully_qualified_parent_path == "main_function"
    ]

    assert len(calls_in_main) == 2

    # Verify the fully qualified parent path for each call
    helper_call = next(call for call in calls_in_main if call.name == "helper_function")
    add_call = next(call for call in calls_in_main if call.name == "add")

    assert helper_call.fully_qualified_parent_path == "main_function"
    assert add_call.fully_qualified_parent_path == "main_function"


def test_extract_function_calls_within_class_member_function() -> None:
    """Test function calls within a class member function definition."""
    code = """
void global_helper() {
    // Global helper function
}

class Calculator {
public:
    void setValue(int value) {
        this->value = value;
    }

    void processValue() {
        global_helper();
        setValue(42);
    }

private:
    int value;
};
"""
    driver_tree = CppCDriverTree.from_code(code, "test.cpp")
    function_calls = driver_tree.extract_function_calls()

    # Find the function calls within Calculator::processValue
    calls_in_process_value = [
        call
        for call in function_calls
        if call.fully_qualified_parent_path == "Calculator::processValue"
    ]

    assert len(calls_in_process_value) == 2

    # Verify the fully qualified parent path for each call
    global_helper_call = next(
        call for call in calls_in_process_value if call.name == "global_helper"
    )
    set_value_call = next(
        call for call in calls_in_process_value if call.name == "setValue"
    )

    assert global_helper_call.fully_qualified_parent_path == "Calculator::processValue"
    assert set_value_call.fully_qualified_parent_path == "Calculator::processValue"


# NOTE: not supporting class function calls due to issues with extracting the fully_qualified path
# def test_extract_class_member_function_calls_from_free_function() -> None:
#     """Test calling a class member function from within a free function."""
#     code = """
# class Calculator {
# public:
#     void setValue(int value) {
#         this->value = value;
#     }
#
#     int getValue() const {
#         return value;
#     }
#
# private:
#     int value;
# };
#
# void use_calculator() {
#     Calculator calc;
#     calc.setValue(100);
#     int result = calc.getValue();
# }
# """
#     driver_tree = CppCDriverTree.from_code(code, "test.cpp")
#     function_calls = driver_tree.extract_function_calls()
#
#     # Find the function calls within use_calculator
#     calls_in_use_calculator = [
#         call
#         for call in function_calls
#         if call.fully_qualified_parent_path == "use_calculator"
#     ]
#
#     assert len(calls_in_use_calculator) == 2
#
#     # Verify the fully qualified parent path for member function calls
#     set_value_call = next(
#         call for call in calls_in_use_calculator if call.name == "setValue"
#     )
#     get_value_call = next(
#         call for call in calls_in_use_calculator if call.name == "getValue"
#     )
#
#     assert set_value_call.fully_qualified_parent_path == "use_calculator"
#     assert get_value_call.fully_qualified_parent_path == "use_calculator"
