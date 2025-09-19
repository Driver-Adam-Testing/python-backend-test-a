import pathlib

import pytest

from .go_driver import GoDriverTree


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
def test_extract_function_defs(
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
