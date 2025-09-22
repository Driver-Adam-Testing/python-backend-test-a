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
            str(im.bespoke_data.package_alias)
            if im.bespoke_data.package_alias
            else None,
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
            str(ds.bespoke_data.kind) if ds.bespoke_data.kind else None,
            ds.bespoke_data.is_exported,
            str(ds.bespoke_data.ty_params) if ds.bespoke_data.ty_params else None,
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
            str(f.bespoke_data.kind) if f.bespoke_data.kind else None,
            f.bespoke_data.is_exported,
            str(f.bespoke_data.ty_params) if f.bespoke_data.ty_params else None,
            str(f.bespoke_data.rx_ty) if f.bespoke_data.rx_ty else None,
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
