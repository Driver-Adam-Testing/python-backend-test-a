import pathlib

import pytest

from .go_driver import GoDriverTree


@pytest.fixture(scope="module")
def imports_test_code() -> str:
    file_path = (
        pathlib.Path(__file__).parent
        / "treesitter_testcases"
        / "go"
        / "test_imports.go"
    )
    with open(file_path, encoding="utf-8") as f:
        return f.read()


def test_extract_imports_no_false_positives(imports_test_code: str) -> None:
    driver_tree = GoDriverTree.from_code(imports_test_code, "does_not_matter.go")
    imports = driver_tree.extract_imports()
    assert len(imports) == 19


@pytest.mark.parametrize(
    "expected_name, expected_im_path, expected_line_range, expected_alias, expected_dot, expected_blank",
    [
        ("fmt", "fmt", (5, 5), None, False, False),
        ("context", "context", (8, 11), None, False, False),
        ("json", "encoding/json", (8, 11), None, False, False),
        ("stdlog", "log", (14, 17), "stdlog", False, False),
        ("stdjson", "encoding/json", (14, 17), "stdjson", False, False),
        ("fmt", "fmt", (20, 23), None, True, False),
        ("math", "math", (20, 23), None, True, False),
        ("driver", "database/sql/driver", (26, 29), None, False, True),
        ("png", "image/png", (26, 29), None, False, True),
        ("pq", "github.com/lib/pq", (32, 42), None, False, True),
        ("mysql", "github.com/go-sql-driver/mysql", (32, 42), None, False, True),
        ("go-sqlite3", "github.com/mattn/go-sqlite3", (32, 42), None, False, True),
        ("gin", "github.com/gin-gonic/gin", (32, 42), None, False, False),
        ("mux", "github.com/gorilla/mux", (32, 42), None, False, False),
        ("v4", "github.com/labstack/echo/v4", (32, 42), None, False, False),
        ("config", "myproject/internal/config", (45, 48), None, False, False),
        ("database", "myproject/internal/database", (45, 48), None, False, False),
        ("cryptorand", "crypto/rand", (51, 54), "cryptorand", False, False),
        ("mathrand", "math/rand", (51, 54), "mathrand", False, False),
    ],
)
def test_extract_imports(
    imports_test_code: str,
    expected_name: str,
    expected_im_path: str,
    expected_line_range: tuple[int, int],
    expected_alias: str | None,
    expected_dot: bool,
    expected_blank: bool,
) -> None:
    driver_tree = GoDriverTree.from_code(imports_test_code, "does_not_matter.go")
    imports = driver_tree.extract_imports()
    extracted = [
        (
            im.name,
            im.bespoke_data.package_path,
            (im.start_line, im.end_line),
            im.bespoke_data.package_alias,
            im.bespoke_data.dot_import,
            im.bespoke_data.blank_import,
        )
        for im in imports
    ]

    assert (
        expected_name,
        expected_im_path,
        expected_line_range,
        expected_alias,
        expected_dot,
        expected_blank,
    ) in extracted, (
        f"Expected import ({expected_name}, {expected_im_path}, {expected_line_range}, {expected_alias}, {expected_dot}, {expected_blank}) "
        f"not found in extracted imports: {extracted}"
    )


@pytest.fixture(scope="module")
def data_structure_test_code() -> str:
    file_path = (
        pathlib.Path(__file__).parent
        / "treesitter_testcases"
        / "go"
        / "test_data_structures.go"
    )
    with open(file_path, encoding="utf-8") as f:
        return f.read()


def test_extract_data_structure_no_false_positives(
    data_structure_test_code: str,
) -> None:
    driver_tree = GoDriverTree.from_code(data_structure_test_code, "does_not_matter.go")
    data_structures = driver_tree.extract_data_structure_definitions()
    assert len(data_structures) == 23


@pytest.mark.parametrize(
    "expected_ds_name, expected_line_range, expected_kind, expected_exported, expected_ty_params",
    [
        ("SimpleStruct", (10, 13), "struct", True, None),
        ("simpleStructPrivate", (15, 18), "struct", False, None),
        ("ComplexStruct", (21, 31), "struct", True, None),
        ("BaseStruct", (34, 37), "struct", True, None),
        ("ExtendedStruct", (39, 42), "struct", True, None),
        ("AnonymousFieldStruct", (45, 49), "struct", True, None),
        ("TaggedStruct", (52, 62), "struct", True, None),
        ("EmptyStruct", (65, 65), "empty_struct", True, None),
        ("PointerStruct", (68, 74), "struct", True, None),
        ("FunctionStruct", (77, 82), "struct", True, None),
        ("ChannelStruct", (85, 89), "struct", True, None),
        ("InterfaceStruct", (92, 98), "struct", True, None),
        ("GenericStruct", (101, 105), "struct", True, "[T any]"),
        ("GenericConstrainedStruct", (107, 111), "struct", True, "[T comparable]"),
        (
            "NumericStruct",
            (114, 118),
            "struct",
            True,
            "[T ~int | ~int64 | ~float32 | ~float64]",
        ),
        ("NestedStructs", (121, 139), "struct", True, None),
        ("MultipleEmbedded", (142, 146), "struct", True, None),
        ("BitFieldStruct", (203, 205), "struct", True, None),
        ("UserID", (215, 215), "type_alias", True, None),
        ("JSONData", (216, 216), "type_alias", True, None),
        ("Temperature", (219, 219), "new_type", True, None),
        ("Distance", (220, 220), "new_type", True, None),
        ("Status", (221, 221), "new_type", True, None),
    ],
)
def test_extract_data_structure_defs(
    data_structure_test_code: str,
    expected_ds_name: str,
    expected_line_range: tuple[int, int],
    expected_kind: str,
    expected_exported: bool,
    expected_ty_params: str | None,
) -> None:
    driver_tree = GoDriverTree.from_code(data_structure_test_code, "does_not_matter.go")
    data_structures = driver_tree.extract_data_structure_definitions()
    extracted = [
        (
            ds.name,
            (ds.start_line, ds.end_line),
            str(ds.bespoke_data.kind),
            ds.bespoke_data.is_exported,
            ds.bespoke_data.ty_params,
        )
        for ds in data_structures
    ]

    assert (
        expected_ds_name,
        expected_line_range,
        expected_kind,
        expected_exported,
        expected_ty_params,
    ) in extracted, (
        f"Expected data structure ({expected_ds_name}, {expected_line_range}, {expected_kind}, {expected_ty_params}) "
        f"not found in extracted data_structures: {extracted}"
    )


@pytest.fixture(scope="module")
def callables_test_code() -> str:
    file_path = (
        pathlib.Path(__file__).parent
        / "treesitter_testcases"
        / "go"
        / "test_callables.go"
    )
    with open(file_path, encoding="utf-8") as f:
        return f.read()


def test_extract_callables_no_false_positives(callables_test_code: str) -> None:
    driver_tree = GoDriverTree.from_code(callables_test_code, "does_not_matter.go")
    callables = driver_tree.extract_callable_definitions()
    assert len(callables) == 22


@pytest.mark.parametrize(
    "expected_fn_name, expected_line_range, expected_kind, expected_exported, expected_ty_params, expected_rx_ty",
    [
        ("simpleFunction", (12, 14), "function", False, None, None),
        ("functionWithParams", (17, 19), "function", False, None, None),
        ("functionWithReturns", (22, 24), "function", False, None, None),
        ("namedReturns", (27, 31), "function", False, None, None),
        ("variadicFunction", (34, 40), "function", False, None, None),
        ("pointerFunction", (43, 47), "function", False, None, None),
        ("sliceMapFunction", (50, 54), "function", False, None, None),
        ("interfaceFunction", (57, 59), "function", False, None, None),
        ("channelFunction", (62, 67), "function", False, None, None),
        ("contextFunction", (70, 80), "function", False, None, None),
        ("closureExample", (83, 88), "function", False, None, None),
        ("Add", (96, 98), "method", True, None, "*Calculator"),
        ("GetValue", (101, 103), "method", True, None, "Calculator"),
        ("Push", (110, 112), "method", True, None, "*Stack[T]"),
        ("Pop", (114, 123), "method", True, None, "*Stack[T]"),
        ("GenericFunction", (126, 133), "function", True, "[T comparable]", None),
        (
            "NumericOperation",
            (136, 138),
            "function",
            True,
            "[T ~int | ~int64 | ~float64]",
            None,
        ),
        ("HigherOrderFunction", (141, 147), "function", True, None, None),
        ("factorial", (150, 155), "function", False, None, None),
        ("deferExample", (158, 170), "function", False, None, None),
        ("functionCallsExample", (173, 203), "function", False, None, None),
        ("main", (206, 208), "function", False, None, None),
    ],
)
def test_extract_callable_defs(
    callables_test_code: str,
    expected_fn_name: str,
    expected_line_range: tuple[int, int],
    expected_kind: str,
    expected_exported: bool,
    expected_ty_params: str | None,
    expected_rx_ty: str | None,
) -> None:
    driver_tree = GoDriverTree.from_code(callables_test_code, "does_not_matter.go")
    functions = driver_tree.extract_callable_definitions()
    extracted = [
        (
            f.name,
            (f.start_line, f.end_line),
            str(f.bespoke_data.kind),
            f.bespoke_data.is_exported,
            f.bespoke_data.ty_params,
            f.bespoke_data.rx_ty,
        )
        for f in functions
    ]

    assert (
        expected_fn_name,
        expected_line_range,
        expected_kind,
        expected_exported,
        expected_ty_params,
        expected_rx_ty,
    ) in extracted, (
        f"Expected function ({expected_fn_name}, {expected_line_range}, {expected_kind}, {expected_ty_params}, {expected_rx_ty}) "
        f"not found in extracted functions: {extracted}"
    )


@pytest.fixture(scope="module")
def calls_test_code() -> str:
    file_path = (
        pathlib.Path(__file__).parent / "treesitter_testcases" / "go" / "test_calls.go"
    )
    with open(file_path, encoding="utf-8") as f:
        return f.read()


def test_extract_calls_no_false_positives(calls_test_code: str) -> None:
    driver_tree = GoDriverTree.from_code(calls_test_code, "does_not_matter.go")
    calls = driver_tree.extract_function_calls()
    for call in calls:
        print(call.name)
    assert len(calls) == 58


@pytest.mark.parametrize(
    "expected_call_name, expected_line_range, expected_complete_call_site_name, expected_goroutine",
    [
        ("len", (40, 40), "len", False),
        ("make", (41, 41), "make", False),
        ("Printf", (42, 42), "fmt.Printf", False),
        ("Abs", (45, 45), "math.Abs", False),
        ("ToUpper", (46, 46), "strings.ToUpper", False),
        ("Printf", (47, 47), "fmt.Printf", False),
        ("Add", (54, 54), "calc.Add", False),
        ("Printf", (55, 55), "fmt.Printf", False),
        ("GetValue", (55, 55), "calc.GetValue", False),
        ("Increment", (59, 59), "counter.Increment", False),
        ("Increment", (60, 60), "counter.Increment", False),
        ("Printf", (61, 61), "fmt.Printf", False),
        ("Value", (61, 61), "counter.Value", False),
        ("Printf", (67, 67), "fmt.Printf", False),
        ("Join", (68, 68), "strings.Join", False),
        ("Printf", (69, 69), "fmt.Printf", False),
        ("divide", (72, 72), "divide", False),
        ("Printf", (73, 73), "fmt.Printf", False),
        ("sum", (82, 82), "sum", False),
        ("sum", (83, 83), "sum", False),
        ("sum", (85, 85), "sum", False),
        ("Printf", (86, 86), "fmt.Printf", False),
        ("Printf", (103, 103), "fmt.Printf", False),
        ("Printf", (110, 110), "fmt.Printf", False),
        ("scale", (110, 110), "scale", False),
        ("Max", (115, 115), "Max", False),
        ("Max", (116, 116), "Max", False),
        ("Printf", (117, 117), "fmt.Printf", False),
        ("Max", (120, 120), "Max[float64]", False),
        ("Printf", (121, 121), "fmt.Printf", False),
        ("Sprintf", (125, 125), "fmt.Sprintf", False),
        ("Sprintf", (125, 125), "fmt.Sprintf", False),
        ("close", (134, 134), "close", False),
        ("make", (139, 139), "make", False),
        ("sendValues", (142, 142), "sendValues", True),
        ("Printf", (146, 146), "fmt.Printf", False),
        ("make", (150, 150), "make", False),
        ("Sleep", (152, 152), "time.Sleep", False),
        ("Printf", (158, 158), "fmt.Printf", False),
        ("After", (159, 159), "time.After", False),
        ("Println", (160, 160), "fmt.Println", False),
        ("Sprintf", (167, 167), "fmt.Sprintf", False),
        ("len", (167, 167), "len", False),
        ("ToUpper", (167, 167), "strings.ToUpper", False),
        ("Println", (168, 168), "fmt.Println", False),
        ("Format", (171, 171), "time.Now().Add(1 * time.Hour).Format", False),
        ("Add", (171, 171), "time.Now().Add", False),
        ("Now", (171, 171), "time.Now", False),
        ("Printf", (172, 172), "fmt.Printf", False),
        ("basicCalls", (176, 176), "basicCalls", False),
        ("methodCalls", (178, 178), "methodCalls", False),
        ("multipleArgsReturns", (180, 180), "multipleArgsReturns", False),
        ("variadicCalls", (182, 182), "variadicCalls", False),
        ("anonymousCalls", (184, 184), "anonymousCalls", False),
        ("genericCalls", (186, 186), "genericCalls", False),
        ("goroutineCalls", (188, 188), "goroutineCalls", False),
        ("errorCalls", (190, 190), "errorCalls", False),
        ("nestedCalls", (192, 192), "nestedCalls", False),
    ],
)
def test_extract_calls(
    calls_test_code: str,
    expected_call_name: str,
    expected_line_range: tuple[int, int],
    expected_complete_call_site_name: str,
    expected_goroutine: bool,
) -> None:
    driver_tree = GoDriverTree.from_code(calls_test_code, "does_not_matter.go")
    calls = driver_tree.extract_function_calls()
    extracted = [
        (
            c.name,
            (c.start_line, c.end_line),
            c.bespoke_data.complete_call_site_name,
            c.bespoke_data.is_goroutine_invocation,
        )
        for c in calls
    ]

    assert (
        expected_call_name,
        expected_line_range,
        expected_complete_call_site_name,
        expected_goroutine,
    ) in extracted, (
        f"Expected call ({expected_call_name}, {expected_line_range}, {expected_complete_call_site_name}, {expected_goroutine}) "
        f"not found in extracted calls: {extracted}"
    )


@pytest.fixture(scope="module")
def globals_test_code() -> str:
    file_path = (
        pathlib.Path(__file__).parent
        / "treesitter_testcases"
        / "go"
        / "test_globals.go"
    )
    with open(file_path, encoding="utf-8") as f:
        return f.read()


def test_extract_globals_no_false_positives(globals_test_code: str) -> None:
    driver_tree = GoDriverTree.from_code(globals_test_code, "does_not_matter.go")
    globals_list = driver_tree.extract_package_globals()
    assert len(globals_list) == 22


@pytest.mark.parametrize(
    "expected_gbl_name, expected_line_range, expected_kind, expected_uses_iota, expected_components, expected_exported",
    [
        (
            "GlobalInt",
            (10, 10),
            "global_var",
            False,
            ["GlobalInt"],
            [True],
        ),
        (
            "GlobalString",
            (11, 11),
            "global_var",
            False,
            ["GlobalString"],
            [True],
        ),
        (
            "packageInt",
            (14, 14),
            "global_var",
            False,
            ["packageInt"],
            [False],
        ),
        (
            "packageBool",
            (15, 15),
            "global_var",
            False,
            ["packageBool"],
            [False],
        ),
        (
            "package_variable_declaration",
            (18, 23),
            "global_var_group",
            False,
            ["InferredInt", "InferredString", "InferredSlice", "InferredMap"],
            [True, True, True, True],
        ),
        (
            "package_variable_declaration",
            (26, 29),
            "global_var_group",
            False,
            ["packageInt", "packageString"],
            [False, False],
        ),
        (
            "package_variable_declaration",
            (32, 35),
            "global_var_group",
            False,
            ["GlobalNumber", "packageNumber"],
            [True, False],
        ),
        (
            "package_variable_declaration",
            (38, 43),
            "global_var_group",
            False,
            ["StringPtr", "PersonPtr", "IntChan", "BufferedChan"],
            [True, True, True, True],
        ),
        (
            "SimpleString",
            (46, 46),
            "global_const",
            False,
            ["SimpleString"],
            [True],
        ),
        (
            "SimpleBool",
            (47, 47),
            "global_const",
            False,
            ["SimpleBool"],
            [True],
        ),
        (
            "packageConstString",
            (50, 50),
            "global_const",
            False,
            ["packageConstString"],
            [False],
        ),
        (
            "packageConstInt",
            (51, 51),
            "global_const",
            False,
            ["packageConstInt"],
            [False],
        ),
        (
            "package_constant_declaration",
            (54, 59),
            "global_const_group",
            False,
            ["MaxUsers", "DefaultPort", "AppName", "Version"],
            [True, True, True, True],
        ),
        (
            "package_constant_declaration",
            (62, 65),
            "global_const_group",
            False,
            ["packageMaxUsers", "packageAppName"],
            [False, False],
        ),
        (
            "package_constant_declaration",
            (68, 71),
            "global_const_group",
            False,
            ["GlobalConstNumber", "packageConstNumber"],
            [True, False],
        ),
        (
            "package_constant_declaration",
            (74, 79),
            "global_const_group",
            True,
            ["Sunday", "Monday", "Tuesday", "Wednesday"],
            [True, True, True, True],
        ),
        (
            "package_constant_declaration",
            (82, 86),
            "global_const_group",
            True,
            ["FlagRead", "FlagWrite", "FlagExecute"],
            [True, True, True],
        ),
        (
            "package_constant_declaration",
            (89, 93),
            "global_const_group",
            False,
            ["TypedInt", "TypedFloat", "TypedString"],
            [True, True, True],
        ),
        (
            "package_constant_declaration",
            (98, 102),
            "global_const_group",
            False,
            ["StatusPending", "StatusActive", "StatusCompleted"],
            [True, True, True],
        ),
        (
            "package_variable_declaration",
            (110, 116),
            "global_var_group",
            False,
            ["DefaultPerson", "PersonList"],
            [True, True],
        ),
        (
            "package_constant_declaration",
            (119, 123),
            "global_const_group",
            False,
            ["DefaultTimeout", "MaxRetries", "BufferSize"],
            [True, True, True],
        ),
        (
            "package_constant_declaration",
            (126, 130),
            "global_const_group",
            False,
            ["Greeting", "Target", "message"],
            [True, True, False],
        ),
    ],
)
def test_extract_globals(
    globals_test_code: str,
    expected_gbl_name: str,
    expected_line_range: tuple[int, int],
    expected_kind: str,
    expected_uses_iota: bool,
    expected_components: list[str],
    expected_exported: list[bool],
) -> None:
    driver_tree = GoDriverTree.from_code(globals_test_code, "does_not_matter.go")
    globals_list = driver_tree.extract_package_globals()
    extracted = [
        (
            g.name,
            (g.start_line, g.end_line),
            str(g.bespoke_data.kind),
            g.bespoke_data.uses_iota,
            [c.name for c in g.bespoke_data.components],
            [c.is_exported for c in g.bespoke_data.components],
        )
        for g in globals_list
    ]

    assert (
        expected_gbl_name,
        expected_line_range,
        expected_kind,
        expected_uses_iota,
        expected_components,
        expected_exported,
    ) in extracted, (
        f"Expected global ({expected_gbl_name}, {expected_line_range}, {expected_kind}, {expected_uses_iota}, {expected_components}, {expected_exported}) "
        f"not found in extracted functions: {extracted}"
    )


@pytest.fixture(scope="module")
def interfaces_test_code() -> str:
    file_path = (
        pathlib.Path(__file__).parent
        / "treesitter_testcases"
        / "go"
        / "test_interfaces.go"
    )
    with open(file_path, encoding="utf-8") as f:
        return f.read()


def test_extract_interfaces_no_false_positives(interfaces_test_code: str) -> None:
    driver_tree = GoDriverTree.from_code(interfaces_test_code, "does_not_matter.go")
    interfaces = driver_tree.extract_interfaces()
    assert len(interfaces) == 19


@pytest.mark.parametrize(
    "expected_ifc_name, expected_line_range, expected_exported, expected_ty_params, expected_method_elems, expected_interface_elems",
    [
        ("SimpleInterface", (11, 13), True, None, ["DoSomething"], []),
        (
            "complexPrivateInterface",
            (16, 20),
            False,
            None,
            ["Read", "Write", "Close"],
            [],
        ),
        (
            "ProcessorInterface",
            (23, 27),
            True,
            None,
            ["Process", "Validate", "Configure"],
            [],
        ),
        ("anyInterface", (30, 30), False, None, [], []),
        ("AnyInterface", (31, 31), True, None, [], []),
        ("ReadWriter", (34, 37), True, None, [], ["io.Reader", "io.Writer"]),
        (
            "ReadWriteCloser",
            (39, 43),
            True,
            None,
            [],
            ["io.Reader", "io.Writer", "io.Closer"],
        ),
        (
            "ExtendedInterface",
            (46, 50),
            True,
            None,
            ["Flush", "Sync"],
            ["ReadWriteCloser"],
        ),
        ("GenericInterface", (53, 56), True, "[T any]", ["Process", "Compare"], []),
        (
            "ComparableInterface",
            (59, 62),
            True,
            "[T comparable]",
            ["Equal", "Less"],
            [],
        ),
        (
            "NumericInterface",
            (65, 70),
            True,
            "[T ~int | ~int64 | ~float32 | ~float64]",
            ["Add", "Subtract", "Multiply", "Divide"],
            [],
        ),
        ("Stringer", (73, 75), True, None, ["String"], []),
        ("GoStringer", (77, 79), True, None, ["GoString"], []),
        (
            "FormatterInterface",
            (81, 85),
            True,
            None,
            ["Format"],
            ["Stringer", "GoStringer"],
        ),
        ("VariadicInterface", (88, 91), True, None, ["Process", "Combine"], []),
        ("ChannelInterface", (94, 98), True, None, ["Send", "Receive", "Close"], []),
        (
            "ContextLikeInterface",
            (101, 106),
            True,
            None,
            ["Deadline", "Done", "Err", "Value"],
            [],
        ),
        ("EventHandler", (109, 113), True, None, ["OnStart", "OnStop", "OnEvent"], []),
        (
            "Repository",
            (116, 122),
            True,
            "[T any]",
            ["Create", "GetByID", "Update", "Delete", "List"],
            [],
        ),
    ],
)
def test_extract_interfaces(
    interfaces_test_code: str,
    expected_ifc_name: str,
    expected_line_range: tuple[int, int],
    expected_exported: bool,
    expected_ty_params: str | None,
    expected_method_elems: list[str],
    expected_interface_elems: list[str],
) -> None:
    driver_tree = GoDriverTree.from_code(interfaces_test_code, "does_not_matter.go")
    interfaces_list = driver_tree.extract_interfaces()
    extracted = [
        (
            ifc.name,
            (ifc.start_line, ifc.end_line),
            ifc.bespoke_data.is_exported,
            ifc.bespoke_data.ty_params,
            list(ifc.bespoke_data.methods),
            list(ifc.bespoke_data.interfaces),
        )
        for ifc in interfaces_list
    ]

    assert (
        expected_ifc_name,
        expected_line_range,
        expected_exported,
        expected_ty_params,
        expected_method_elems,
        expected_interface_elems,
    ) in extracted, (
        f"Expected interface ({expected_ifc_name}, {expected_line_range}, {expected_exported}, {expected_ty_params}, {expected_method_elems}, {expected_interface_elems}) "
        f"not found in extracted interface: {extracted}"
    )
