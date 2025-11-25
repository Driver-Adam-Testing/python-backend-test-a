import textwrap
import threading
from collections import defaultdict
from pathlib import Path

from shared.agent.chat_openai import ChatOpenAI
from shared.inspector.utils.lang_specialization.symbol_common import (
    RawTreeSitterSymbolData,
    SymbolKind,
)

_disambiguation_cache: dict = {}

# Just to be safe, in case we start trying to multithread this
_cache_lock = threading.Lock()


def _get_cache_key(
    candidates: list[tuple[Path, RawTreeSitterSymbolData]],
    call_symbol: RawTreeSitterSymbolData,
    calling_symbol: RawTreeSitterSymbolData,
) -> tuple[str, str, str | None, frozenset[tuple[str, str | None]]]:
    return (
        call_symbol.name,
        calling_symbol.name,
        calling_symbol.fully_qualified_parent_path,
        frozenset(
            (cand.name, cand.fully_qualified_parent_path) for _, cand in candidates
        ),
    )


def _build_candidate_map(
    candidates: list[tuple[Path, RawTreeSitterSymbolData]],
) -> dict[tuple[str, str | None], int]:
    """
    This allows us to convert cached identities back to indices efficiently
    """
    return {
        (cand.name, cand.fully_qualified_parent_path): idx
        for idx, (_, cand) in enumerate(candidates)
    }


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


def disambiguate_call(
    candidates: list[tuple[Path, RawTreeSitterSymbolData]],
    call_symbol: RawTreeSitterSymbolData,
    calling_symbol: RawTreeSitterSymbolData,
) -> tuple[int | None, bool]:
    """
    Use LLM (or cached result) to disambiguate which candidate is the correct one for a call.
    Returns (index of the correct candidate, whether LLM was called).
    """

    cache_key = _get_cache_key(candidates, call_symbol, calling_symbol)
    cached_identity = None

    with _cache_lock:
        if cache_key in _disambiguation_cache:
            cached_identity = _disambiguation_cache[cache_key]
            if cached_identity is None:
                return None, False

    # If we have a cached result, check if it applies to current candidates
    # We have a cached result, but candidates might be in different order now,
    # so we map back
    if cached_identity is not None:
        candidate_map = _build_candidate_map(candidates)
        if cached_identity in candidate_map:
            print(f"[CACHE] Hit for call '{call_symbol.name}' -> {cached_identity}")
            return candidate_map[cached_identity], False
        else:
            print(
                f"Warning: Cached candidate {cached_identity} not found in current candidates"
            )

    # Cache miss - proceed with LLM
    print(
        f"[LLM] Disambiguating call '{call_symbol.name}' with {len(candidates)} candidates in {call_symbol.file_path}"
    )
    system_prompt = textwrap.dedent("""\
        You are a software engineering expert that disambiguates function calls when there are multiple candidates.

        You will be presented with the code of a function, the specific call within that function, and a list of candidate functions that could be the target of the call.
        Your task is to determine which candidate function is the correct one for the call.

        The candidates are functions that are defined in the same file or imported from other files.

        You will be given the candidates in the form:
        Candidate <Candidate Number>:
        <Candidate Name> at <Fully Qualified Parent Path>
        <Candidate Code>

        It is possible that NO candidate provided is the correct one, in which case you should return a sentence describing why no candidate matched.

        In the case that a candidate does match, you only respond with a single integer to indicate the index of the correct candidate, starting from 0.
    """)

    # TODO: would be great to get the includes added to the user prompt as well
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
        candidate_idx = None

    # Cache the result
    # Cache value is the identity of chosen function (name, fully_qualified_parent_path) or None
    #   - None means LLM failed - not sure how likely or if we want to cache this
    #   - Identity allows us to find the function regardless of candidate ordering

    if candidate_idx is not None and 0 <= candidate_idx < len(candidates):
        chosen_candidate = candidates[candidate_idx][1]
        cached_value = (
            chosen_candidate.name,
            chosen_candidate.fully_qualified_parent_path,
        )
    else:
        cached_value = None

    with _cache_lock:
        _disambiguation_cache[cache_key] = cached_value

    return candidate_idx, True
