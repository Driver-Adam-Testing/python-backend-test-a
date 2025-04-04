from collections import defaultdict
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Self

from utils.lang_specialization.symbol_common import RawTreeSitterSymbolData, SymbolKind

RESET = "\033[0m"
BLUE = "\033[94m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"


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
) -> tuple[
    list[RawTreeSitterSymbolData],
    list[str],
    dict[RawTreeSitterSymbolData, list[RawTreeSitterSymbolData]],
]:
    from treesitter_driver import CDriverTree

    code_str = fpath.read_text(encoding="utf8")

    driver = CDriverTree.from_code(code_str, file_path=fpath)
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
    """
    Results in:
      - file_to_symbols: for each file, a list of raw symbols (excluding import symbols).
      - includes_map: for each file, a list of direct include strings.
    """

    file_to_symbols: dict[Path, list[RawTreeSitterSymbolData]]
    includes_map: dict[Path, list[str]]
    file_to_containment_map: dict[
        Path, dict[RawTreeSitterSymbolData, list[RawTreeSitterSymbolData]]
    ]

    @classmethod
    def from_files(cls, file_paths: list[Path]) -> Self:
        file_to_syms: dict[Path, list[RawTreeSitterSymbolData]] = {}
        raw_includes: dict[Path, list[str]] = {}
        file_to_containment_map: dict[
            Path, dict[RawTreeSitterSymbolData, list[RawTreeSitterSymbolData]]
        ] = {}

        total = len(file_paths)
        for i, fpath in enumerate(file_paths, 1):
            print(f"[{i}/{total}] Parsing {fpath}...", end="", flush=True)
            try:
                symbols, includes, containment_map = parse_c_file(fpath)
                print(" done.")
            except Exception as e:
                print(f" failed: {e}")
                symbols = []
                includes = []
                containment_map = {}
            file_to_syms[fpath] = symbols
            raw_includes[fpath] = includes
            file_to_containment_map[fpath] = containment_map

        return cls(
            file_to_symbols=file_to_syms,
            includes_map=raw_includes,
            file_to_containment_map=file_to_containment_map,
        )


def resolve_include_path(
    current_file: Path, include_str: str, user_include_dirs: set[Path]
) -> Path | None:
    candidate = (current_file.parent / include_str).resolve()
    if candidate.exists():
        return candidate

    for inc_dir in user_include_dirs:
        candidate = (inc_dir / include_str).resolve()
        if candidate.exists():
            return candidate
    return None


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
        cls, parsed: ParsedProject, user_include_dirs: set[Path] | None
    ) -> Self:
        visibility_map: dict[Path, set[Path]] = {}

        if user_include_dirs is None:
            user_include_dirs = set()

        def dfs(current: Path, visited: set[Path]) -> None:
            for inc_str in parsed.includes_map.get(current, []):
                inc_path = resolve_include_path(
                    current_file=current,
                    include_str=inc_str,
                    user_include_dirs=user_include_dirs,
                )
                if (
                    inc_path
                    and inc_path not in visited
                    and inc_path in parsed.file_to_symbols
                ):
                    visited.add(inc_path)
                    dfs(inc_path, visited)

        for fpath in parsed.file_to_symbols:
            print(f"Resolving visibility for {fpath}...", flush=True)
            visited: set[Path] = set()
            dfs(fpath.resolve(), visited)
            visibility_map[fpath] = visited

        return cls(
            file_to_symbols=parsed.file_to_symbols,
            includes_map=parsed.includes_map,
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
        # 1) Collect all definitions by name and also collect declarations by name
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

        decl_to_def: dict[RawTreeSitterSymbolData, RawTreeSitterSymbolData] = {}

        # For each name, if there's exactly 1 definition, unify all declarations with it.
        for name, decl_list in declarations_by_name.items():
            def_list = definitions_by_name.get(name, [])
            if len(def_list) == 1:  # exactly one definition
                (def_fpath, def_sym) = def_list[0]
                for _decl_fpath, decl_sym in decl_list:
                    # TODO: Optionally check if decl_fpath can "see" def_fpath in a more rigorous approach
                    decl_to_def[decl_sym] = def_sym

        # 2) For each symbol, if it's NOT a definition, link it to exactly one definition if found
        linked_map: dict[Path, list[LinkedSymbol]] = {}

        for fpath, raw_syms in project_vis.file_to_symbols.items():
            visible_files = project_vis.visibility_map.get(fpath, set())
            visible_with_self = {fpath, *visible_files}

            linked_syms: list[LinkedSymbol] = []
            for rsym in raw_syms:
                def_symbol: LinkedSymbol | None = None

                # If this symbol is a definition, we won't link it externally.
                if not is_definition(rsym) and rsym.name:
                    # 2a) direct definitions in visible files
                    candidates = definitions_by_name.get(rsym.name, [])
                    vis_defs = [
                        (dfpath, dfsym)
                        for (dfpath, dfsym) in candidates
                        if dfpath in visible_with_self
                    ]
                    if len(vis_defs) == 1:
                        dfpath, def_raw = vis_defs[0]
                        def_symbol = LinkedSymbol(def_raw, True, None)
                    elif len(vis_defs) > 1:
                        # ambiguous => pick first
                        dfpath, def_raw = vis_defs[0]
                        def_symbol = LinkedSymbol(def_raw, True, None)
                    else:
                        # 2b) fallback to a declaration if found
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
class ReifiedSymbol:
    """
    Extends LinkedSymbol with a list of usages (if this is a definition).
    """

    raw: RawTreeSitterSymbolData
    is_definition: bool
    definition: Self | None = None
    usages: list[Self] = field(default_factory=list)
    calls: list[Self] = field(default_factory=list)


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
        """
        Final pass. For each LinkedSymbol, produce a ReifiedSymbol and:
          1) Link usage -> definition
          2) Build definition -> usage adjacency
          3) For each function definition, gather calls from containment_map
        """

        # (1) Create provisional ReifiedSymbols that omit definition/usages/calls
        provisional_map: dict[LinkedSymbol, ReifiedSymbol] = {}
        for _fpath, ls_list in linked_proj.linked_symbols.items():
            for lsym in ls_list:
                provisional_map[lsym] = ReifiedSymbol(
                    raw=lsym.raw, is_definition=lsym.is_definition
                )

        # (2) Build adjacency from definition => usage
        def_to_usage: dict[LinkedSymbol, list[LinkedSymbol]] = {}
        for lsym in provisional_map:
            # If lsym is a usage, link it to its definition
            if not lsym.is_definition and lsym.definition is not None:
                def_ls = lsym.definition
                def_to_usage.setdefault(def_ls, []).append(lsym)

        # (3) Build a first pass 'final_map' that sets .definition and .usages
        final_map: dict[LinkedSymbol, ReifiedSymbol] = {}
        for lsym, reified_sym in provisional_map.items():
            new_def = None
            if (not lsym.is_definition) and lsym.definition:
                new_def = provisional_map[lsym.definition]

            usage_list = [provisional_map[u] for u in def_to_usage.get(lsym, [])]

            final_map[lsym] = replace(
                reified_sym, definition=new_def, usages=usage_list
            )

        # (4) For each function definition, find the calls it makes
        #     by looking at all children in the containment map that have symbol_kind=CALL.
        #     Then see if that CALL usage has a definition. If so, that's the called function.
        #     We'll need to map from RawTreeSitterSymbolData -> LinkedSymbol to find it.
        raw_to_linked: dict[RawTreeSitterSymbolData, LinkedSymbol] = {}
        for lsym in final_map:
            raw_to_linked[lsym.raw] = lsym

        for fpath, ls_list in linked_proj.linked_symbols.items():
            containment_map = file_to_containment_map.get(fpath, {})

            for lsym in ls_list:
                # If it's a function definition (e.g. 'CALLABLE'), gather its calls
                if lsym.is_definition and lsym.raw.symbol_kind == SymbolKind.CALLABLE:
                    # Which children are inside this function?
                    children = containment_map.get(lsym.raw, [])
                    calls_made: list[ReifiedSymbol] = []
                    for child_raw in children:
                        if child_raw.symbol_kind == SymbolKind.CALL:
                            # child_raw is a usage symbol
                            child_linked_sym = raw_to_linked[child_raw]
                            # If that call usage found a definition, that's the function it calls
                            if child_linked_sym.definition is not None:
                                called_func_reif = final_map[
                                    child_linked_sym.definition
                                ]
                                calls_made.append(called_func_reif)

                    # Update the reified symbol with calls
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

                    if sym.raw.symbol_kind == SymbolKind.CALLABLE and sym.calls:
                        print(f"    Calls {len(sym.calls)} function(s):")
                        for called_func in sym.calls:
                            called_name = called_func.raw.name
                            c_lines = f"[lines {called_func.raw.start_line}-{called_func.raw.end_line}]"
                            c_path = called_func.raw.file_path
                            print(f"      -> {called_name} {c_lines} in {c_path}")

                    for usage_sym in sym.usages:
                        usage_name = usage_sym.raw.name
                        usage_lines = f"[lines {usage_sym.raw.start_line}-{usage_sym.raw.end_line}]"
                        usage_file_path = usage_sym.raw.file_path
                        print(
                            f"{YELLOW}    USAGE: {usage_name} {usage_lines} "
                            f"in {usage_file_path}{RESET}"
                        )
                else:
                    # usage symbol
                    if sym.definition:
                        def_name = sym.definition.raw.name
                        def_lines = f"[lines {sym.definition.raw.start_line}-{sym.definition.raw.end_line}]"
                        def_file_path = sym.definition.raw.file_path
                        print(
                            f"{CYAN}  USE: {name} {lines} in {sym_file_path} "
                            f"-> definition: {def_name} {def_lines} in {def_file_path}{RESET}"
                        )
                    else:
                        print(
                            f"{CYAN}  USE: {name} {lines} in {sym_file_path} "
                            "-> definition: None"
                            f"{RESET}"
                        )


def build_c_project_index(
    file_paths: list[Path], user_include_dirs: set[Path] | None
) -> ReifiedProjectIndex:
    """
    Orchestrates all 4 symbol table build passes:
      1) Parse each file to get raw symbols (ParsedProject)
      2) Compute transitive visibility (ParsedProjectWithVisibility)
      3) Link usage -> definition (LinkedProject)
      4) Add definition -> usage (ReifiedProjectIndex)
    """
    print("==> Parsing files...")
    parsed = ParsedProject.from_files(file_paths)
    print("==> Resolving includes and visibility...")
    project_vis = ParsedProjectWithVisibility.from_parsed_project(
        parsed, user_include_dirs=user_include_dirs
    )
    print("==> Linking symbols...")
    linked = LinkedProject.from_parsed_project_with_visibility(project_vis)
    print("==> Reifying symbol graph...")
    reified = ReifiedProjectIndex.from_linked_project(
        linked, parsed.file_to_containment_map
    )
    print("==> Done building index.")
    return reified


def get_git_commit_hash(repo_path: Path) -> str:
    import subprocess

    return (
        subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo_path)
        .decode("utf-8")
        .strip()
    )


def main() -> None:
    import pickle
    import subprocess

    project_root = Path("/Users/andrewmark/projects/no-OS")
    # project_root = Path("/Users/andrewmark/projects/c_test")

    cache_dir = project_root / ".symbol_index_cache"
    cache_dir.mkdir(exist_ok=True)

    try:
        commit_hash = get_git_commit_hash(project_root)
    except subprocess.CalledProcessError:
        commit_hash = "unknown"

    cache_path = cache_dir / f"{commit_hash}.pkl"

    if cache_path.exists():
        print(f"Loading cached symbol index for commit {commit_hash}")
        with cache_path.open("rb") as f:
            index: ReifiedProjectIndex = pickle.load(f)
    else:
        file_paths = (
            list((project_root / "drivers/dac/ad5421").rglob("*.c"))
            + list((project_root / "drivers/dac/ad5421").rglob("*.h"))
            + list((project_root / "drivers/api").rglob("*.c"))
            + list((project_root / "util").rglob("*.c"))
            + list((project_root / "include").rglob("*.h"))
        )

        include_dirs = {project_root / "drivers/dac/ad5421", project_root / "include"}

        index = build_c_project_index(file_paths, user_include_dirs=include_dirs)

        print(f"Caching symbol index for commit {commit_hash}")
        with cache_path.open("wb") as f:
            pickle.dump(index, f)

    focus_files: list[Path] | None = [
        project_root / "drivers" / "dac" / "ad5421" / "ad5421.c"
    ]

    index.print_summary(focus_files)


if __name__ == "__main__":
    main()
