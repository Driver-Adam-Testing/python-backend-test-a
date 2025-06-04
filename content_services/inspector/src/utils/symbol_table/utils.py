from collections import defaultdict
from pathlib import Path

from utils.lang_specialization.symbol_common import RawTreeSitterSymbolData, SymbolKind


def get_fully_qualified_name(sym: RawTreeSitterSymbolData, sep: str = "::") -> str:
    if sym.fully_qualified_parent_path and sym.name:
        return f"{sym.fully_qualified_parent_path}{sym.delimiter}{sym.name}"
    return sym.name or ""


def to_root_relative(fpath: Path, project_root: Path) -> Path:
    """Convert /abs/path/to/root/foo.c -> root/foo.c"""
    return Path(project_root.name) / fpath.relative_to(project_root)


def is_definition(sym: RawTreeSitterSymbolData) -> bool:
    """
    Simple heuristic for whether a raw symbol is considered a 'definition'
    (as opposed to a usage or forward declaration).
    """
    return sym.symbol_kind in {
        SymbolKind.CALLABLE,
        SymbolKind.DATA_STRUCTURE,
        SymbolKind.CLASS,
    }


def is_declaration(sym: RawTreeSitterSymbolData) -> bool:
    return sym.symbol_kind == SymbolKind.CALLABLE_DECLARATION


def is_data_structure(sym: RawTreeSitterSymbolData) -> bool:
    return (
        sym.symbol_kind == SymbolKind.DATA_STRUCTURE
        or sym.symbol_kind == SymbolKind.CLASS
    )


def build_containment_map(
    symbols: list[RawTreeSitterSymbolData],
) -> dict[RawTreeSitterSymbolData, list[RawTreeSitterSymbolData]]:
    """
    Return a mapping of parent_symbol -> list of child_symbols
    where each child is fully within the parent's [start_byte, end_byte].
    """
    child_map: dict[RawTreeSitterSymbolData, list[RawTreeSitterSymbolData]] = (
        defaultdict(list)
    )

    # Compare all pairs (O(n^2) :(
    for parent in symbols:
        for child in symbols:
            if parent is child:
                continue
            if (
                parent.start_byte < child.start_byte
                and child.end_byte <= parent.end_byte
            ) or (
                parent.start_byte <= child.start_byte
                and child.end_byte < parent.end_byte
            ):
                child_map[parent].append(child)
    return dict(child_map)
