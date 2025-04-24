from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Self

from utils.lang_specialization.symbol_common import (
    RawTreeSitterSymbolData,
    ReifiedSymbol,
    SymbolKind,
)


def to_root_relative(fpath: Path, project_root: Path) -> Path:
    """Convert /abs/path/to/root/foo.c -> root/foo.c"""
    # TODO move to util file
    return Path(project_root.name) / fpath.relative_to(project_root)


def is_definition(sym: RawTreeSitterSymbolData) -> bool:
    """
    Simple heuristic for whether a raw symbol is considered a 'definition'
    (as opposed to a usage or forward declaration).
    """
    return sym.symbol_kind in {
        SymbolKind.VARIABLE,
        SymbolKind.CALLABLE,
        SymbolKind.DATA_STRUCTURE,
    }


def is_declaration(sym: RawTreeSitterSymbolData) -> bool:
    return sym.symbol_kind == SymbolKind.CALLABLE_DECLARATION


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
                parent.start_byte <= child.start_byte
                and child.end_byte <= parent.end_byte
            ):
                child_map[parent].append(child)
    return dict(child_map)


def parse_c_file(
    fpath: Path,
    project_root: Path,
) -> tuple[
    list[RawTreeSitterSymbolData],
    list[str],
    dict[RawTreeSitterSymbolData, list[RawTreeSitterSymbolData]],
]:
    from utils.treesitter_driver import CDriverTree

    code_str = fpath.read_text(encoding="utf8")
    root_rel_path = to_root_relative(fpath, project_root)

    driver = CDriverTree.from_code(code_str, file_path=root_rel_path)

    all_syms = driver.extract_all_symbols()
    containment_map = build_containment_map(all_syms)

    includes: list[str] = []
    non_import_symbols: list[RawTreeSitterSymbolData] = []

    for sym in all_syms:
        if sym.symbol_kind == SymbolKind.IMPORT and sym.name is not None:
            includes.append(sym.name)
        else:
            non_import_symbols.append(sym)

    return non_import_symbols, includes, containment_map


@dataclass(frozen=True)
class ParsedProject:
    file_to_symbols: dict[Path, list[RawTreeSitterSymbolData]]
    includes_map: dict[Path, list[str]]
    file_to_containment_map: dict[
        Path, dict[RawTreeSitterSymbolData, list[RawTreeSitterSymbolData]]
    ]

    @classmethod
    def from_files(
        cls, file_paths: list[Path], project_root: Path, num_workers: int | None = None
    ) -> Self:
        def parse_and_handle(abs_fpath: Path) -> tuple[Path, list, list, dict]:
            rel_fpath = to_root_relative(abs_fpath, project_root)
            try:
                symbols, includes, containment_map = parse_c_file(
                    abs_fpath, project_root
                )
                print(f"Parsing {rel_fpath}... done.")
            except Exception as e:
                print(f"Parsing {rel_fpath}... failed: {e}")
                symbols, includes, containment_map = [], [], {}
            return rel_fpath, symbols, includes, containment_map

        file_to_syms = {}
        raw_includes = {}
        file_to_containment_map = {}

        if num_workers is None or num_workers == 1:
            # Serial processing
            total = len(file_paths)
            for i, abs_fpath in enumerate(file_paths, 1):
                print(f"[{i}/{total}]", end=" ")
                rel_fpath, symbols, includes, containment_map = parse_and_handle(
                    abs_fpath
                )
                file_to_syms[rel_fpath] = symbols
                raw_includes[rel_fpath] = includes
                file_to_containment_map[rel_fpath] = containment_map
        else:
            # Parallel processing
            with ThreadPoolExecutor(max_workers=num_workers) as executor:
                future_to_path = {
                    executor.submit(parse_and_handle, fp): fp for fp in file_paths
                }
                for i, future in enumerate(as_completed(future_to_path), 1):
                    rel_fpath, symbols, includes, containment_map = future.result()
                    print(f"[{i}/{len(file_paths)}] Parsed {rel_fpath}")
                    file_to_syms[rel_fpath] = symbols
                    raw_includes[rel_fpath] = includes
                    file_to_containment_map[rel_fpath] = containment_map

        return cls(
            file_to_symbols=file_to_syms,
            includes_map=raw_includes,
            file_to_containment_map=file_to_containment_map,
        )


def resolve_include_path(
    current_file: Path, include_str: str, project_files: set[Path]
) -> Path | None:
    """
    Minimal attempt: if `current_file.parent/include_str` is in the project, return it.
    Otherwise, look for a file in project_files that ends with include_str as a fallback.
    If collisions happen, pick the first or None.
    """
    # 1) Direct local path approach
    candidate = (current_file.parent / include_str).resolve()
    if candidate in project_files:
        return candidate

    # 2) Fallback: see which project files end with include_str
    #    e.g. "foo/bar.h" might match ".../some/path/foo/bar.h"
    possible_matches = [pf for pf in project_files if str(pf).endswith(include_str)]
    if not possible_matches:
        return None
    if len(possible_matches) == 1:
        return possible_matches[0]

    # If multiple matches remain, pick one. Crudely, we just pick the first.
    return possible_matches[0]


@dataclass(frozen=True)
class ParsedProjectWithVisibility:
    """
    - Same data as ParsedProject
    - Add a visibility_map that tells you which files are transitively visible from each file.
    """

    file_to_symbols: dict[Path, list[RawTreeSitterSymbolData]]
    includes_map: dict[Path, list[str]]
    visibility_map: dict[Path, set[Path]]

    @classmethod
    def from_parsed_project(
        cls, parsed: ParsedProject, num_workers: int | None
    ) -> Self:
        """
        Build a map from each file -> all files it can 'see' transitively.
        Only links includes that are in parsed.file_to_symbols (our project).
        """
        file_to_symbols = parsed.file_to_symbols
        includes_map = parsed.includes_map
        project_files = set(file_to_symbols.keys())

        visibility_map: dict[Path, set[Path]] = {}

        def dfs(current: Path, visited: set[Path]) -> None:
            for inc_str in includes_map.get(current, []):
                inc_path = resolve_include_path(current, inc_str, project_files)
                if inc_path and inc_path not in visited:
                    visited.add(inc_path)
                    dfs(inc_path, visited)

        def compute_visited(fpath: Path) -> set[Path]:
            visited: set[Path] = {fpath}
            dfs(fpath, visited)
            return visited

        # For each file, do a DFS of includes:
        if num_workers is None or num_workers == 1:
            # Serial processing
            for fpath in file_to_symbols:
                print(f"Resolving visibility for {fpath}...", flush=True)
                visited = compute_visited(fpath)
                visibility_map[fpath] = visited
        else:
            # Parallel processing
            with ThreadPoolExecutor(max_workers=num_workers) as executor:
                future_to_path = {
                    executor.submit(compute_visited, fp): fp for fp in file_to_symbols
                }
                for i, future in enumerate(as_completed(future_to_path), 1):
                    visited = future.result()
                    print(f"[{i}/{len(file_to_symbols)}]")
                    visibility_map[future_to_path[future]] = visited

        return cls(
            file_to_symbols=file_to_symbols,
            includes_map=includes_map,
            visibility_map=visibility_map,
        )


@dataclass(frozen=True)
class LinkedSymbol:
    """
    Extends RawTreeSitterSymbolData with a pointer to a definition
    if this is a usage (definition=None if it is itself a definition).
    """

    raw: RawTreeSitterSymbolData
    is_definition: bool
    definition: Self | None = None


@dataclass(frozen=True)
class LinkedProject:
    """
    Results in
    - A dictionary from file -> list of LinkedSymbol
    - Carries forward the same visibility_map
    """

    linked_symbols: dict[Path, list[LinkedSymbol]]
    visibility_map: dict[Path, set[Path]]

    @classmethod
    def from_parsed_project_with_visibility(
        cls, project_vis: ParsedProjectWithVisibility
    ) -> Self:
        """
        Link usage -> definition across all files that are transitively visible.
        """
        # 1) Collect definitions and declarations by name
        definitions_by_name: dict[str, list[tuple[Path, RawTreeSitterSymbolData]]] = {}
        declarations_by_name: dict[str, list[tuple[Path, RawTreeSitterSymbolData]]] = {}

        for fpath, raw_syms in project_vis.file_to_symbols.items():
            for rsym in raw_syms:
                if rsym.name is None:
                    continue
                if is_definition(rsym):
                    definitions_by_name.setdefault(rsym.name, []).append((fpath, rsym))
                elif is_declaration(rsym):
                    declarations_by_name.setdefault(rsym.name, []).append((fpath, rsym))
                # else it's a usage or something else

        # 2) If there's exactly 1 definition for a name, unify all declarations to it
        decl_to_def: dict[RawTreeSitterSymbolData, RawTreeSitterSymbolData] = {}
        for name, decl_list in declarations_by_name.items():
            def_list = definitions_by_name.get(name, [])
            if len(def_list) == 1:
                (def_fpath, def_sym) = def_list[0]
                for _decl_fpath, decl_sym in decl_list:
                    decl_to_def[decl_sym] = def_sym

        # 3) For each symbol, link usage->definition if visible
        linked_map: dict[Path, list[LinkedSymbol]] = {}
        for fpath, raw_syms in project_vis.file_to_symbols.items():
            visible_files = project_vis.visibility_map.get(fpath, set())
            visible_with_self = {fpath, *visible_files}

            linked_syms: list[LinkedSymbol] = []
            for rsym in raw_syms:
                def_symbol: LinkedSymbol | None = None

                if not is_definition(rsym) and rsym.name:
                    # Direct definitions in visible files
                    candidates = definitions_by_name.get(rsym.name, [])
                    vis_defs = [
                        (dfpath, dfsym)
                        for (dfpath, dfsym) in candidates
                        if dfpath in visible_with_self
                    ]
                    if len(vis_defs) >= 1:
                        # pick first or unify
                        dfpath, def_raw = vis_defs[0]
                        def_symbol = LinkedSymbol(def_raw, True, None)
                    else:
                        # fallback to a declaration if found
                        decl_candidates = declarations_by_name.get(rsym.name, [])
                        vis_decls = [
                            (dpath, draw)
                            for (dpath, draw) in decl_candidates
                            if dpath in visible_with_self
                        ]
                        if len(vis_decls) >= 1:
                            # pick first for simplicity
                            (dpath, decl_raw) = vis_decls[0]
                            # see if we unified this decl to a known definition
                            maybe_def = decl_to_def.get(decl_raw)
                            if maybe_def is not None:
                                def_symbol = LinkedSymbol(maybe_def, True, None)

                linked_syms.append(
                    LinkedSymbol(
                        raw=rsym,
                        is_definition=is_definition(rsym),
                        definition=def_symbol,
                    )
                )
            linked_map[fpath] = linked_syms

        return cls(linked_symbols=linked_map, visibility_map=project_vis.visibility_map)


@dataclass(frozen=True)
class ReifiedProjectIndex:
    """
    Final result:
      - A dictionary from file -> reified symbols (fully linked in both directions).
    """

    file_to_symbols: dict[Path, list[ReifiedSymbol]]

    @classmethod
    def from_linked_project(
        cls,
        linked_proj: LinkedProject,
        file_to_containment_map: dict[
            Path, dict[RawTreeSitterSymbolData, list[RawTreeSitterSymbolData]]
        ],
    ) -> Self:
        # (1) Create provisional ReifiedSymbols
        provisional_map: dict[LinkedSymbol, ReifiedSymbol] = {}
        for _fpath, ls_list in linked_proj.linked_symbols.items():
            for lsym in ls_list:
                provisional_map[lsym] = ReifiedSymbol(
                    raw=lsym.raw, is_definition=lsym.is_definition
                )

        # (2) Build adjacency from definition => usage
        def_to_usage: dict[LinkedSymbol, list[LinkedSymbol]] = {}
        for lsym in provisional_map:
            if not lsym.is_definition and lsym.definition is not None:
                def_ls = lsym.definition
                def_to_usage.setdefault(def_ls, []).append(lsym)

        # (3) Build a first pass final_map that sets .definition and .usages
        final_map: dict[LinkedSymbol, ReifiedSymbol] = {}
        for lsym, reified_sym in provisional_map.items():
            new_def = None
            if (not lsym.is_definition) and lsym.definition:
                new_def = provisional_map[lsym.definition]
            usage_list = [provisional_map[u] for u in def_to_usage.get(lsym, [])]
            final_map[lsym] = replace(
                reified_sym, definition=new_def, usages=usage_list
            )

        # (4) For function definitions, gather calls from the containment map
        raw_to_linked: dict[RawTreeSitterSymbolData, LinkedSymbol] = {}
        for lsym in final_map:
            raw_to_linked[lsym.raw] = lsym

        for fpath, ls_list in linked_proj.linked_symbols.items():
            containment_map = file_to_containment_map.get(fpath, {})
            for lsym in ls_list:
                if lsym.is_definition and lsym.raw.symbol_kind == SymbolKind.CALLABLE:
                    children = containment_map.get(lsym.raw, [])
                    calls_made: list[ReifiedSymbol] = []
                    for child_raw in children:
                        if child_raw.symbol_kind == SymbolKind.CALL:
                            child_linked_sym = raw_to_linked[child_raw]
                            if child_linked_sym.definition is not None:
                                called_func_reif = final_map[
                                    child_linked_sym.definition
                                ]
                                calls_made.append(called_func_reif)

                    old_reif = final_map[lsym]
                    final_map[lsym] = replace(old_reif, calls=calls_made)

        # (5) Group them by file
        file_map: dict[Path, list[ReifiedSymbol]] = {}
        for fpath, ls_list in linked_proj.linked_symbols.items():
            file_map[fpath] = [final_map[ls] for ls in ls_list]

        return cls(file_to_symbols=file_map)

    def get_definition_of(self, symbol: ReifiedSymbol) -> ReifiedSymbol | None:
        return symbol.definition

    def get_usages_of(self, symbol: ReifiedSymbol) -> list[ReifiedSymbol]:
        if not symbol.is_definition:
            return []
        return symbol.usages

    def print_summary(self, files: list[Path] | None = None) -> None:
        RESET = "\033[0m"
        BLUE = "\033[94m"
        GREEN = "\033[92m"
        YELLOW = "\033[93m"
        CYAN = "\033[96m"

        targets = files if files else sorted(self.file_to_symbols.keys())

        for fpath in targets:
            reified_syms = self.file_to_symbols.get(fpath)
            if reified_syms is None:
                print(f"{YELLOW}No symbols found for {fpath}{RESET}")
                continue

            print(f"{BLUE}File: {fpath}{RESET}")
            for sym in reified_syms:
                name = sym.raw.name
                lines = f"[lines {sym.raw.start_line}-{sym.raw.end_line}]"
                sym_file_path = sym.raw.file_path

                if sym.is_definition:
                    usage_count = len(sym.usages)
                    print(
                        f"{GREEN}  DEF: {name} {lines} in {sym_file_path} "
                        f"has {usage_count} usage(s){RESET}"
                    )

                    # If this is a CALLABLE definition, show the calls it makes
                    if sym.raw.symbol_kind == SymbolKind.CALLABLE and sym.calls:
                        print(f"    Calls {len(sym.calls)} function(s):")
                        for called_func in sym.calls:
                            called_name = called_func.raw.name
                            c_lines = (
                                f"[lines {called_func.raw.start_line}-"
                                f"{called_func.raw.end_line}]"
                            )
                            c_path = called_func.raw.file_path
                            print(f"      -> {called_name} {c_lines} in {c_path}")

                    # Show usages
                    for usage_sym in sym.usages:
                        usage_name = usage_sym.raw.name
                        usage_lines = (
                            f"[lines {usage_sym.raw.start_line}-"
                            f"{usage_sym.raw.end_line}]"
                        )
                        usage_file_path = usage_sym.raw.file_path
                        print(
                            f"{YELLOW}    USAGE: {usage_name} {usage_lines} "
                            f"in {usage_file_path}{RESET}"
                        )
                else:
                    # usage symbol
                    if sym.definition:
                        def_name = sym.definition.raw.name
                        def_lines = (
                            f"[lines {sym.definition.raw.start_line}-"
                            f"{sym.definition.raw.end_line}]"
                        )
                        def_file_path = sym.definition.raw.file_path
                        print(
                            f"{CYAN}  USE: {name} {lines} in {sym_file_path} "
                            f"-> definition: {def_name} {def_lines} "
                            f"in {def_file_path}{RESET}"
                        )
                    else:
                        print(
                            f"{CYAN}  USE: {name} {lines} in {sym_file_path} "
                            "-> definition: None"
                            f"{RESET}"
                        )


def build_c_project_index(
    file_paths: list[Path], project_root: Path
) -> ReifiedProjectIndex:
    """
    Orchestrate the 4 passes:
      1) Parse each file
      2) Determine transitive visibility among those files
      3) Link usage -> definition
      4) definition -> usage
    """
    print("==> Parsing files...")
    parsed = ParsedProject.from_files(file_paths, project_root, num_workers=8)
    print("==> Resolving includes and visibility...")
    project_vis = ParsedProjectWithVisibility.from_parsed_project(parsed, num_workers=8)
    print("==> Linking symbols...")
    linked = LinkedProject.from_parsed_project_with_visibility(project_vis)
    print("==> Reifying symbol graph...")
    reified = ReifiedProjectIndex.from_linked_project(
        linked, parsed.file_to_containment_map
    )
    print("==> Done building index.")
    return reified


def discover_c_and_h_files(project_root: Path) -> list[Path]:
    return [
        p.resolve() for p in project_root.rglob("*") if p.suffix.lower() in (".c", ".h")
    ]


def main() -> None:
    # project_root = Path("/Users/andrewmark/Downloads/sqlite")
    project_root = Path("/Users/andrewmark/projects/c_test_3")

    file_paths = discover_c_and_h_files(project_root)

    index = build_c_project_index(file_paths, project_root)

    # focus_file = Path("sqlite/src/btree.c")  # Note this is project-relative
    # index.print_summary([focus_file])
    index.print_summary()


if __name__ == "__main__":
    main()
