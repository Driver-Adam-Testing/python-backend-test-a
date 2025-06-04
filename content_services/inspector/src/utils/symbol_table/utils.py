import textwrap
from collections import defaultdict
from pathlib import Path

from utils.lang_specialization.symbol_common import RawTreeSitterSymbolData, SymbolKind
from utils.models import ChatOpenAI


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
        SymbolKind.INTERFACE,
    }


def is_declaration(sym: RawTreeSitterSymbolData) -> bool:
    return sym.symbol_kind == SymbolKind.CALLABLE_DECLARATION


def is_data_structure(sym: RawTreeSitterSymbolData) -> bool:
    return (
        sym.symbol_kind == SymbolKind.DATA_STRUCTURE
        or sym.symbol_kind == SymbolKind.CLASS
        or sym.symbol_kind == SymbolKind.INTERFACE
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


def disambiguate_call_w_llm(
    candidates: list[Path, RawTreeSitterSymbolData],
    call_symbol: RawTreeSitterSymbolData,
    calling_symbol: RawTreeSitterSymbolData,
) -> int | None:
    """
    Use the LLM to disambiguate which candidate is the correct one for a call.
    Returns the index of the correct candidate.
    """
    print("Disambiguating call with LLM...")
    print(f"Call symbol: {call_symbol.name} in {call_symbol.file_path}")
    system_prompt = textwrap.dedent("""\
        You are a software engineering expert that disambiguates function calls when there are multiple candidates.

        You will be presented with the code of a function, the specific call within that function, and a list of candidate functions that could be the target of the call.
        Your task is to determine which candidate function is the correct one for the call.

        The candidates are functions that are defined in the same file or imported from other files.

        You will be given the candidates in the form:
        Candidate <Candidate Number>:
        <Candidate Name> at <Fully Qualified Parent Path>
        <Candidate Code>
        You only respond with a single integer to indicate the index of the correct candidate, starting from 0.
    """)

    user_prompt = (
        f"Here is a function in {calling_symbol.file_path}:\n"
        f"{calling_symbol.symbol_code}\n\n"
        "Disambiguate the source of the following call:\n"
        f"{call_symbol.symbol_code}\n\n"
        "Call candidates to disambiguate:\n"
    )
    for idx, (_, candidate_symbol) in enumerate(candidates):
        user_prompt += (
            f"Candidate {idx}:\n"
            f"{candidate_symbol.name} at {candidate_symbol.fully_qualified_parent_path}\n"
            f"{candidate_symbol.symbol_code}\n\n"
        )

    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0.0,
        request_timeout=60,
    )
    candidate_idx_raw = llm.generate_response(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
    )
    try:
        candidate_idx = int(candidate_idx_raw.strip())
    except ValueError:
        print("Failed to parse an integer from LLM response:", candidate_idx_raw)
        return None

    return candidate_idx
