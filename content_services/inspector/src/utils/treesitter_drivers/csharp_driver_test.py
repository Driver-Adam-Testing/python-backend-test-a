import pathlib

import pytest

from .csharp_driver import CSharpDriverTree


@pytest.fixture(scope="module")
def namespace_test_code() -> str:
    file_path = (
        pathlib.Path(__file__).parent
        / "treesitter_testcases"
        / "csharp"
        / "test_namespaces.cs"
    )
    with open(file_path, encoding="utf-8") as f:
        return f.read()


def test_extract_namespace_decls_no_false_positives(namespace_test_code: str) -> None:
    driver_tree = CSharpDriverTree.from_code(namespace_test_code, "does_not_matter.cs")
    namespaces = driver_tree.extract_namespace_declarations()
    assert len(namespaces) == 5


@pytest.mark.parametrize(
    "expected_namespace_name, expected_line_range, expected_kind",
    [
        ("Com.Example.Traditional", (15, 47), "namespace_block_scope_declaration"),
        ("Nested", (26, 46), "namespace_block_scope_declaration"),
        ("DeeplyNested", (36, 45), "namespace_block_scope_declaration"),
        ("Com.Example.FileScoped", (50, 50), "namespace_file_scope_declaration"),
        ("FileScopedNoSeparator", (123, 123), "namespace_file_scope_declaration"),
    ],
)
def test_extract_namespaces(
    namespace_test_code: str,
    expected_namespace_name: str,
    expected_line_range: tuple[int, int],
    expected_kind: str,
) -> None:
    driver_tree = CSharpDriverTree.from_code(namespace_test_code, "does_not_matter.cs")
    namespaces = driver_tree.extract_namespace_declarations()
    extracted = [
        (
            im.name,
            (im.start_line, im.end_line),
            im.bespoke_data.scoping_kind.value,
        )
        for im in namespaces
    ]

    assert (
        expected_namespace_name,
        expected_line_range,
        expected_kind,
    ) in extracted, (
        f"Expected namespace ({expected_namespace_name}. {expected_line_range}, {expected_kind}) "
        f"not found in extracted `namespace` declarations: {extracted}"
    )


@pytest.fixture(scope="module")
def using_test_code() -> str:
    file_path = (
        pathlib.Path(__file__).parent
        / "treesitter_testcases"
        / "csharp"
        / "test_usings.cs"
    )
    with open(file_path, encoding="utf-8") as f:
        return f.read()


def test_extract_using_imports_no_false_positives(using_test_code: str) -> None:
    driver_tree = CSharpDriverTree.from_code(using_test_code, "does_not_matter.cs")
    imports = driver_tree.extract_using_imports()
    assert len(imports) == 12


@pytest.mark.parametrize(
    "expected_using_name, expected_line_range, expected_kind, expected_alias_name",
    [
        ("System", (2, 2), "local_using", None),
        ("System.Collections.Generic", (3, 3), "local_using", None),
        ("System.Linq", (4, 4), "local_using", None),
        ("System.Collections.Generic.Dictionary", (7, 7), "local_using", "Dict"),
        ("System.Text.StringBuilder", (8, 8), "local_using", "StringBuilder"),
        ("System", (9, 9), "local_using", "Sys"),
        ("System.Math", (12, 12), "local_using", None),
        ("System.Console", (13, 13), "local_using", None),
        ("System.Threading.Tasks", (16, 16), "global_using", None),
        (
            "System.Collections.Concurrent.ConcurrentDictionary",
            (19, 19),
            "local_using",
            "MyAlias",
        ),
        ("global::System.Text.Json", (22, 22), "local_using", None),
        (
            "global::System.Text.Json.JsonSerializer",
            (23, 23),
            "local_using",
            "JsonSerializer",
        ),
    ],
)
def test_extract_using_imports(
    using_test_code: str,
    expected_using_name: str,
    expected_line_range: tuple[int, int],
    expected_kind: str,
    expected_alias_name: str | None,
) -> None:
    driver_tree = CSharpDriverTree.from_code(using_test_code, "does_not_matter.cs")
    using_imports = driver_tree.extract_using_imports()
    extracted = [
        (
            im.name,
            (im.start_line, im.end_line),
            im.bespoke_data.scoping_kind.value,
            im.bespoke_data.alias_name,
        )
        for im in using_imports
    ]

    assert (
        expected_using_name,
        expected_line_range,
        expected_kind,
        expected_alias_name,
    ) in extracted, (
        f"Expected import ({expected_using_name}. {expected_line_range}, {expected_kind}, {expected_alias_name}) "
        f"not found in extracted `using` imports: {extracted}"
    )


@pytest.fixture(scope="module")
def interface_test_code() -> str:
    file_path = (
        pathlib.Path(__file__).parent
        / "treesitter_testcases"
        / "csharp"
        / "test_interfaces.cs"
    )
    with open(file_path, encoding="utf-8") as f:
        return f.read()


def test_extract_interfaces_no_false_positives(interface_test_code: str) -> None:
    driver_tree = CSharpDriverTree.from_code(interface_test_code, "does_not_matter.cs")
    interfaces = driver_tree.extract_interfaces()
    assert len(interfaces) == 25


@pytest.mark.parametrize(
    "expected_interface_name, expected_line_range, expected_modifiers, expected_type_params, expected_base_names",
    [
        ("IDrawable", (9, 22), {"public"}, set(), set()),
        ("IRepository", (25, 32), {"public"}, {"T"}, set()),
        ("IResizable", (35, 47), {"public"}, set(), {"IDrawable"}),
        ("IResizeListener", (43, 46), set(), set(), set()),
        ("ICalculator", (50, 67), {"public"}, set(), set()),
        ("IAdvancedDrawable", (70, 74), {"public"}, set(), {"IDrawable", "IResizable"}),
        ("IComparable", (77, 80), {"public"}, {"in T"}, set()),
        ("IProducer", (83, 87), {"public"}, {"out T"}, set()),
        ("IConsumer", (90, 94), {"public"}, {"in T"}, set()),
        ("IIndexable", (97, 101), {"public"}, {"T"}, set()),
        ("IProcessor", (104, 107), {"public"}, {"TInput", "TOutput"}, set()),
        ("IInternalService", (110, 114), {"internal"}, set(), set()),
        ("IPartialInterface", (117, 121), {"public", "partial"}, set(), set()),
        ("IPartialInterface", (123, 127), {"public", "partial"}, set(), set()),
        ("IUnsafeOperations", (130, 134), {"public", "unsafe"}, set(), set()),
        ("IOuterInterface", (137, 152), {"public"}, set(), set()),
        ("IPrivateNested", (142, 145), {"private"}, set(), set()),
        ("IProtectedNested", (148, 151), {"protected"}, set(), set()),
        ("IPublicNested", (158, 161), {"public"}, set(), set()),
        ("IInternalNested", (164, 167), {"internal"}, set(), set()),
        (
            "IProtectedInternalNested",
            (170, 173),
            {"protected", "internal"},
            set(),
            set(),
        ),
        ("IPrivateProtectedNested", (176, 179), {"private", "protected"}, set(), set()),
        ("IComplexInterface", (183, 198), {"internal", "partial"}, set(), set()),
        ("INestedInPartial", (188, 197), {"public"}, set(), set()),
        ("IDeeplyNested", (193, 196), {"private"}, set(), set()),
    ],
)
def test_extract_interfaces(
    interface_test_code: str,
    expected_interface_name: str,
    expected_line_range: tuple[int, int],
    expected_modifiers: set[str],
    expected_type_params: set[str],
    expected_base_names: set[str],
) -> None:
    driver_tree = CSharpDriverTree.from_code(interface_test_code, "does_not_matter.cs")
    interfaces = driver_tree.extract_interfaces()
    extracted = []
    for ifc in interfaces:
        name = ifc.name
        line_range = (ifc.start_line, ifc.end_line)
        modifiers = {v.value for v in ifc.bespoke_data.modifiers}
        type_params = set(ifc.bespoke_data.type_params)
        base_names = set(ifc.bespoke_data.base_names)
        extracted.append((name, line_range, modifiers, type_params, base_names))

    assert (
        expected_interface_name,
        expected_line_range,
        expected_modifiers,
        expected_type_params,
        expected_base_names,
    ) in extracted, (
        f"Expected interface ({expected_interface_name}, {expected_line_range}, {expected_modifiers}, {expected_type_params}, {expected_base_names}) "
        f"not found in extracted interfaces: {extracted}"
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
    assert len(klasses) == 11


@pytest.mark.parametrize(
    "expected_class_name, expected_line_range, expected_modifiers, expected_kind",
    [
        ("SimpleClass", (8, 38), {"public"}, "standard"),
        ("InnerClass", (29, 37), {"public", "static"}, "standard"),
        ("AbstractClass", (41, 49), {"public", "abstract"}, "standard"),
        ("ConcreteClass", (52, 68), {"public"}, "standard"),
        ("GenericClass", (71, 84), {"public"}, "standard"),
        ("PartialClass", (87, 96), {"public", "partial"}, "standard"),
        ("StaticUtilities", (99, 105), {"public", "static"}, "standard"),
        ("SealedClass", (108, 114), {"public", "sealed"}, "standard"),
        ("PersonRecord", (117, 117), {"public"}, "record"),
        ("PersonRecordWithProps", (120, 125), {"public"}, "record"),
        ("AttributedClass", (128, 151), {"public"}, "standard"),
    ],
)
def test_extract_classes(
    class_test_code: str,
    expected_class_name: str,
    expected_line_range: tuple[int, int],
    expected_modifiers: set[str],
    expected_kind: str,
) -> None:
    driver_tree = CSharpDriverTree.from_code(class_test_code, "does_not_matter.cs")
    klasses = driver_tree.extract_class_definitions()
    extracted = []
    for k in klasses:
        name = k.name
        line_range = (k.start_line, k.end_line)
        modifiers = {v.value for v in k.bespoke_data.modifiers}
        class_kind = k.bespoke_data.kind
        extracted.append((name, line_range, modifiers, class_kind))

    assert (
        expected_class_name,
        expected_line_range,
        expected_modifiers,
        expected_kind,
    ) in extracted, (
        f"Expected class ({expected_class_name}, {expected_line_range}, {expected_modifiers}, {expected_kind}) "
        f"not found in extracted classes: {extracted}"
    )


@pytest.mark.parametrize(
    "expected_class_name, expected_bases",
    [
        ("ConcreteClass", ("AbstractClass", "IComparable")),
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
    assert len(method_likes) == 31


@pytest.mark.parametrize(
    "expected_method_name, expected_line_range, expected_kind, expected_modifiers, expected_return_ty",
    [
        ("MethodExamples", (11, 13), "constructor", {"public"}, None),
        ("MethodExamples", (16, 20), "constructor", {"public"}, None),
        ("Name", (23, 23), "property", {"public"}, None),
        ("Value", (24, 24), "property", {"public"}, None),
        ("CreatedAt", (27, 27), "property", {"public"}, None),
        ("Description", (31, 35), "property", {"public"}, None),
        ("StaticMethod", (38, 41), "method", {"static", "public"}, None),
        ("ProcessData", (44, 52), "method", {"public"}, None),
        ("PrivateHelper", (55, 58), "method", {"private"}, None),
        ("CreateList", (61, 64), "method", {"public"}, None),
        ("ToString", (67, 70), "method", {"public", "override"}, None),
        ("VirtualMethod", (73, 76), "method", {"public", "virtual"}, None),
        ("AbstractMethod", (79, 79), "method", {"public", "abstract"}, None),
        ("AsyncMethod", (82, 86), "method", {"public", "async"}, None),
        ("TryGetValue", (89, 93), "method", {"public"}, None),
        ("ModifyValue", (96, 99), "method", {"public"}, None),
        ("ProcessReadOnly", (102, 105), "method", {"public"}, None),
        ("Reverse", (108, 108), "method", {"public", "static"}, None),
        ("+", (111, 114), "operator_overload", {"public", "static"}, "MethodExamples"),
        (
            "string",
            (117, 120),
            "conversion_operator_declaration",
            {"public", "static", "implicit"},
            None,
        ),
        (
            "int",
            (123, 126),
            "conversion_operator_declaration",
            {"public", "static", "explicit"},
            None,
        ),
        (
            "~MethodExamples",
            (129, 132),
            "destructor",
            set(),
            None,
        ),
        ("ValueChanged", (135, 135), "event_field_like", {"public"}, "Action"),
        ("GetDisplayName", (138, 138), "method", {"public"}, None),
        ("CalculateComplex", (141, 149), "method", {"public"}, None),
        ("LocalHelper", (143, 146), "local_function", set(), None),
        ("Reverse", (155, 163), "method", {"public", "static"}, None),
        ("IsNullOrWhiteSpace", (165, 168), "method", {"public", "static"}, None),
        ("[string key]", (177, 181), "indexer", {"public"}, "object"),
        ("DataChanged", (184, 184), "event_field_like", {"public"}, "EventHandler"),
        (
            "StatusChanged",
            (188, 192),
            "event_property_like",
            {"public"},
            "EventHandler",
        ),
    ],
)
def test_extract_method_likes(
    method_test_code: str,
    expected_method_name: str,
    expected_line_range: tuple[int, int],
    expected_kind: str,
    expected_modifiers: set[str],
    expected_return_ty: str,
) -> None:
    driver_tree = CSharpDriverTree.from_code(method_test_code, "does_not_matter.cs")
    method_likes = driver_tree.extract_method_like_definitions()
    extracted = []
    for m in method_likes:
        name = m.name
        line_range = (m.start_line, m.end_line)
        callable_kind = m.bespoke_data.kind.value
        modifiers = {v.value for v in m.bespoke_data.modifiers}
        return_ty = m.bespoke_data.return_ty
        extracted.append((name, line_range, callable_kind, modifiers, return_ty))

    assert (
        expected_method_name,
        expected_line_range,
        expected_kind,
        expected_modifiers,
        expected_return_ty,
    ) in extracted, (
        f"Expected method-like ({expected_method_name}, {expected_line_range}, {expected_kind}, {expected_modifiers}, {expected_return_ty}) "
        f"not found in extracted method-likes: {extracted}"
    )


@pytest.fixture(scope="module")
def enum_test_code() -> str:
    file_path = (
        pathlib.Path(__file__).parent
        / "treesitter_testcases"
        / "csharp"
        / "test_enums.cs"
    )
    with open(file_path, encoding="utf-8") as f:
        return f.read()


def test_extract_enums_no_false_positives(enum_test_code: str) -> None:
    driver_tree = CSharpDriverTree.from_code(enum_test_code, "does_not_matter.cs")
    enums = driver_tree.extract_enum_definitions()
    assert len(enums) == 10


@pytest.mark.parametrize(
    "expected_enum_name, expected_line_range, expected_modifiers, expected_underlying_ty",
    [
        ("Color", (7, 12), {"public"}, "default"),
        ("Status", (15, 22), {"public"}, "default"),
        ("Priority", (25, 31), {"public"}, "byte"),
        ("FileAccess", (34, 43), {"public"}, "default"),
        ("LogLevel", (46, 54), {"public"}, "default"),
        ("DayOfWeek", (57, 66), {"public"}, "default"),
        ("HttpStatusCode", (69, 91), {"public"}, "default"),
        ("Permission", (94, 105), {"public"}, "long"),
        ("SecurityLevel", (111, 118), {"protected", "internal"}, "default"),
        ("Operation", (178, 184), {"public"}, "default"),
    ],
)
def test_extract_enums(
    enum_test_code: str,
    expected_enum_name: str,
    expected_line_range: tuple[int, int],
    expected_modifiers: set[str],
    expected_underlying_ty: str,
) -> None:
    driver_tree = CSharpDriverTree.from_code(enum_test_code, "does_not_matter.cs")
    enums = driver_tree.extract_enum_definitions()
    extracted = []
    for e in enums:
        name = e.name
        line_range = (e.start_line, e.end_line)
        modifiers = {v.value for v in e.bespoke_data.modifiers}
        ty = e.bespoke_data.underlying_ty
        extracted.append((name, line_range, modifiers, ty))

    assert (
        expected_enum_name,
        expected_line_range,
        expected_modifiers,
        expected_underlying_ty,
    ) in extracted, (
        f"Expected enum ({expected_enum_name}, {expected_line_range}, {expected_modifiers}, {expected_underlying_ty}) "
        f"not found in extracted enums: {extracted}"
    )


@pytest.mark.parametrize(
    "expected_enum_name, expected_line_range, expected_interfaces",
    [
        ("Operation", (178, 184), ("IComparable",)),
    ],
)
def test_extract_enum_interfaces(
    enum_test_code: str,
    expected_line_range: tuple[int, int],
    expected_enum_name: str,
    expected_interfaces: list[str],
) -> None:
    driver_tree = CSharpDriverTree.from_code(enum_test_code, "does_not_matter.cs")
    enums = driver_tree.extract_enum_definitions()
    extracted = [
        (e.name, (e.start_line, e.end_line), e.base_class_names) for e in enums
    ]

    assert (
        expected_enum_name,
        expected_line_range,
        expected_interfaces,
    ) in extracted, (
        f"Expected interfaces: ({expected_interfaces}) for enum ({expected_enum_name}) "
        f"but not found in extracted enums: {extracted}"
    )


@pytest.fixture(scope="module")
def struct_test_code() -> str:
    file_path = (
        pathlib.Path(__file__).parent
        / "treesitter_testcases"
        / "csharp"
        / "test_structs.cs"
    )
    with open(file_path, encoding="utf-8") as f:
        return f.read()


def test_extract_structs_no_false_positives(struct_test_code: str) -> None:
    driver_tree = CSharpDriverTree.from_code(struct_test_code, "does_not_matter.cs")
    structs = driver_tree.extract_struct_definitions()
    assert len(structs) == 12


@pytest.mark.parametrize(
    "expected_struct_name, expected_line_range, expected_modifiers, expected_kind",
    [
        ("Point", (8, 23), {"public"}, "struct"),
        ("Rectangle", (26, 42), {"public"}, "struct"),
        ("ImmutablePoint", (45, 66), {"public", "readonly"}, "struct"),
        ("StackOnlyStruct", (69, 85), {"public", "ref"}, "struct"),
        ("GenericPair", (88, 104), {"public"}, "struct"),
        ("Complex", (107, 178), {"public"}, "struct"),
        ("Container", (181, 215), {"public"}, "struct"),
        ("Metadata", (199, 204), {"public"}, "struct"),
        ("MathConstants", (218, 244), {"public"}, "struct"),
        ("PersonInfo", (247, 256), {"public"}, "record_struct"),
        ("ImmutablePersonInfo", (259, 263), {"public", "readonly"}, "record_struct"),
        (
            "MultiModifierStruct",
            (272, 284),
            {"private", "protected", "readonly", "ref"},
            "struct",
        ),
    ],
)
def test_extract_structs(
    struct_test_code: str,
    expected_struct_name: str,
    expected_line_range: tuple[int, int],
    expected_modifiers: set[str],
    expected_kind: str,
) -> None:
    driver_tree = CSharpDriverTree.from_code(struct_test_code, "does_not_matter.cs")
    structs = driver_tree.extract_struct_definitions()
    extracted = []
    for s in structs:
        name = s.name
        line_range = (s.start_line, s.end_line)
        modifiers = {v.value for v in s.bespoke_data.modifiers}
        kind = s.bespoke_data.kind
        extracted.append((name, line_range, modifiers, kind))

    assert (
        expected_struct_name,
        expected_line_range,
        expected_modifiers,
        expected_kind,
    ) in extracted, (
        f"Expected struct ({expected_struct_name}, {expected_line_range}, {expected_modifiers}, {expected_kind}) "
        f"not found in extracted structs: {extracted}"
    )


@pytest.mark.parametrize(
    "expected_struct_name, expected_line_range, expected_interfaces",
    [
        ("Complex", (107, 178), ("IEquatable", "IComparable")),
    ],
)
def test_extract_struct_interfaces(
    struct_test_code: str,
    expected_line_range: tuple[int, int],
    expected_struct_name: str,
    expected_interfaces: list[str],
) -> None:
    driver_tree = CSharpDriverTree.from_code(struct_test_code, "does_not_matter.cs")
    structs = driver_tree.extract_struct_definitions()
    extracted = [
        (s.name, (s.start_line, s.end_line), s.base_class_names) for s in structs
    ]

    assert (
        expected_struct_name,
        expected_line_range,
        expected_interfaces,
    ) in extracted, (
        f"Expected interfaces: ({expected_interfaces}) for struct ({expected_struct_name}) "
        f"but not found in extracted structs: {extracted}"
    )
