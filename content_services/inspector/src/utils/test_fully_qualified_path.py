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
