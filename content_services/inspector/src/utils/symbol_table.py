from collections import defaultdict
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Self

from utils.lang_specialization.symbol_common import (
    RawTreeSitterSymbolData,
    ReifiedSymbol,
    SymbolKind,
)


def get_fully_qualified_name(sym: RawTreeSitterSymbolData, sep: str = "::") -> str:
    if sym.fully_qualified_parent_path and sym.name:
        return f"{sym.fully_qualified_parent_path}{sep}{sym.name}"
    return sym.name or ""  # TODO is this correct? What if name is None?


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
        # SymbolKind.VARIABLE,
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
                parent.start_byte < child.start_byte
                and child.end_byte <= parent.end_byte
            ) or (
                parent.start_byte <= child.start_byte
                and child.end_byte < parent.end_byte
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
    from utils.treesitter_driver import CppCDriverTree

    code_str = fpath.read_text(encoding="utf8")
    root_rel_path = to_root_relative(fpath, project_root)

    driver = CppCDriverTree.from_code(code_str, file_path=root_rel_path)

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
        cls,
        file_paths: list[Path],
        project_root: Path,
        parse_file_fn: Callable[
            [Path, Path],
            tuple[
                list[RawTreeSitterSymbolData],
                list[str],
                dict[RawTreeSitterSymbolData, list[RawTreeSitterSymbolData]],
            ],
        ] = parse_c_file,
        num_workers: int | None = None,
    ) -> Self:
        def parse_and_handle(abs_fpath: Path) -> tuple[Path, list, list, dict]:
            rel_fpath = to_root_relative(abs_fpath, project_root)
            try:
                symbols, includes, containment_map = parse_file_fn(
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
        cls,
        parsed: ParsedProject,
        num_workers: int | None,
        resolver_fn: Callable[
            [Path, str, set[Path]], Path | None
        ] = resolve_include_path,
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
                inc_path = resolver_fn(current, inc_str, project_files)
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
    is_declaration: bool
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
        cls,
        project_vis: ParsedProjectWithVisibility,
        sep: str = "::",
    ) -> Self:
        """
        Link usage -> definition across all files that are transitively visible.
        """
        # 1) Collect definitions and declarations by name
        definitions_by_fqn: dict[str, list[tuple[str, RawTreeSitterSymbolData]]] = {}
        definitions_by_name: dict[str, list[tuple[Path, RawTreeSitterSymbolData]]] = {}
        declarations_by_fqn: dict[str, list[tuple[str, RawTreeSitterSymbolData]]] = {}

        for fpath, raw_syms in project_vis.file_to_symbols.items():
            for rsym in raw_syms:
                if rsym.name is None:
                    continue
                fqn = get_fully_qualified_name(sym=rsym, sep=sep)
                if is_definition(rsym):
                    definitions_by_fqn.setdefault(fqn, []).append((fqn, rsym))
                    definitions_by_name.setdefault(rsym.name, []).append((fpath, rsym))
                elif is_declaration(rsym):
                    declarations_by_fqn.setdefault(fqn, []).append((fqn, rsym))
                # else it's a usage or something else

        # 2) If there's exactly 1 definition for a name, unify all declarations to it
        decl_to_def: dict[RawTreeSitterSymbolData, RawTreeSitterSymbolData] = {}
        for fqn, decl_list in declarations_by_fqn.items():
            def_list = definitions_by_fqn.get(fqn, [])
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
                fqn = get_fully_qualified_name(sym=rsym, sep=sep)

                if not is_definition(rsym) and not is_declaration(rsym) and rsym.name:
                    # Direct definitions in visible files
                    if rsym.symbol_kind == SymbolKind.CALL:
                        candidates = definitions_by_name.get(rsym.name, [])
                    else:
                        candidates = definitions_by_fqn.get(fqn, [])
                    vis_defs = [
                        (dfpath, dfsym)
                        for (dfpath, dfsym) in candidates
                        if dfpath in visible_with_self
                    ]
                    if len(vis_defs) >= 1:
                        # pick first or unify
                        dfpath, def_raw = vis_defs[
                            0
                        ]  # TODO: in C++ taking the first is not always correct due to namespace collisions
                        # This is true even for FQN though due overloading
                        def_symbol = LinkedSymbol(
                            raw=def_raw,
                            is_definition=True,
                            is_declaration=False,
                            definition=None,
                        )
                    else:
                        # No direct definition, check for declarations
                        decl_candidates = declarations_by_fqn.get(fqn, [])
                        vis_decls = [
                            (dpath, d_raw)
                            for (dpath, d_raw) in decl_candidates
                            if dpath in visible_with_self
                        ]
                        if len(vis_decls) >= 1:
                            # pick first for simplicity
                            _, decl_raw = vis_decls[0]
                            # see if we unified this decl to a known definition
                            maybe_def = decl_to_def.get(decl_raw)
                            if maybe_def is not None:
                                def_symbol = LinkedSymbol(
                                    raw=maybe_def,
                                    is_definition=True,
                                    is_declaration=False,
                                    definition=None,
                                )

                elif is_declaration(rsym) and rsym.name and rsym in decl_to_def:
                    def_symbol = LinkedSymbol(
                        raw=decl_to_def[rsym],
                        is_definition=True,
                        is_declaration=False,
                        definition=None,
                    )

                linked_syms.append(
                    LinkedSymbol(
                        raw=rsym,
                        is_definition=is_definition(rsym),
                        is_declaration=is_declaration(rsym),
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
      - A mapping from object FQNs to their member functions and variables for C++
    """

    file_to_symbols: dict[Path, list[ReifiedSymbol]]
    # fqn -> {"functions": [...], "variables": [...]} # TODO track member vars!
    # object_fqns_to_members: dict[str, dict[str, list[ReifiedSymbol]]] # TODO: not sure if needed anymore since we add children to the reified symbol

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

        # Track classes/structs/etc and their members
        obj_symbols: dict[str, ReifiedSymbol] = {}  # fqn -> ReifiedSymbol
        obj_members: dict[str, dict[str, list[ReifiedSymbol]]] = defaultdict(
            lambda: {"functions": [], "variables": []}
        )

        for _fpath, ls_list in linked_proj.linked_symbols.items():
            for lsym in ls_list:
                provisional_map[lsym] = ReifiedSymbol(
                    raw=lsym.raw,
                    is_definition=lsym.is_definition,
                    is_declaration=lsym.is_declaration,
                )

        # (2) Build adjacency from definition => usage
        def_to_usage: dict[LinkedSymbol, list[LinkedSymbol]] = {}
        def_to_decl: dict[LinkedSymbol, list[LinkedSymbol]] = {}
        for lsym in provisional_map:
            if not lsym.is_definition and lsym.definition is not None:
                def_ls = lsym.definition

                if is_declaration(lsym.raw):
                    def_to_decl.setdefault(def_ls, []).append(lsym)
                else:  # Usage
                    def_to_usage.setdefault(def_ls, []).append(lsym)

        # (3) Build a first pass final_map that sets .definition and .usages
        final_map: dict[LinkedSymbol, ReifiedSymbol] = {}
        for lsym, reified_sym in provisional_map.items():
            new_def = None
            if (not lsym.is_definition) and lsym.definition:
                new_def = provisional_map[lsym.definition]
            usage_list = [provisional_map[u] for u in def_to_usage.get(lsym, [])]
            decl_list = [provisional_map[d] for d in def_to_decl.get(lsym, [])]
            final_map[lsym] = replace(
                reified_sym,
                definition=new_def,
                usages=usage_list,
                declarations=decl_list,
            )

            # Track class/object definitions
            if lsym.is_definition and lsym.raw.symbol_kind == SymbolKind.DATA_STRUCTURE:
                fqn = get_fully_qualified_name(sym=lsym.raw)
                obj_symbols[fqn] = final_map[lsym]

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
                elif lsym.raw.symbol_kind == SymbolKind.DATA_STRUCTURE:
                    # Set inheritance
                    if lsym.raw.base_class_names is not None:
                        inherits_from: list[ReifiedSymbol] = []
                        for base_name in lsym.raw.base_class_names:
                            if base_name in obj_symbols:
                                base_sym = obj_symbols[base_name]
                                inherits_from.append(base_sym)
                            else:
                                # check if it's in the same parent as the current symbol
                                parent_fqn = (
                                    lsym.raw.fully_qualified_parent_path
                                    + lsym.raw.delimiter
                                    + base_name
                                )
                                if parent_fqn in obj_symbols:
                                    base_sym = obj_symbols[parent_fqn]
                                    inherits_from.append(base_sym)
                        if len(inherits_from):
                            old_reif = final_map[lsym]
                            final_map[lsym] = replace(
                                old_reif,
                                inheritance=inherits_from,
                            )

        # (5) Build object membership dicts
        for lsym, reified in final_map.items():
            if lsym.is_definition and lsym.raw.fully_qualified_parent_path:
                parent_fqn = lsym.raw.fully_qualified_parent_path

                # Check if this symbol belongs to a known class
                if parent_fqn in obj_symbols:
                    if lsym.raw.symbol_kind == SymbolKind.CALLABLE:
                        obj_members[parent_fqn]["functions"].append(reified)
                        parent_sym = obj_symbols[parent_fqn]
                        reified.parent = parent_sym
                        parent_sym.children.append(reified)
                    # Since we only pull globals, empty right now... TODO
                    elif lsym.raw.symbol_kind == SymbolKind.VARIABLE:
                        obj_members[parent_fqn]["variables"].append(reified)
                        parent_sym = obj_symbols[parent_fqn]
                        reified.parent = parent_sym
                        parent_sym.children.append(reified)

        # (6) Group them by file
        file_map: dict[Path, list[ReifiedSymbol]] = {}
        for fpath, ls_list in linked_proj.linked_symbols.items():
            file_map[fpath] = [final_map[ls] for ls in ls_list]

        return cls(
            file_to_symbols=file_map
        )  # , object_fqns_to_members=dict(obj_members))

    def get_definition_of(self, symbol: ReifiedSymbol) -> ReifiedSymbol | None:
        return symbol.definition

    def get_usages_of(self, symbol: ReifiedSymbol) -> list[ReifiedSymbol]:
        if not symbol.is_definition:
            return []
        return symbol.usages

    # def get_object_members(self, class_fqn: str) -> dict[str, list[ReifiedSymbol]]:
    #     return self.object_fqns_to_members.get(
    #         class_fqn, {"functions": [], "variables": []}
    #     )

    # def get_member_functions(self, class_fqn: str) -> list[ReifiedSymbol]:
    #     return self.object_fqns_to_members.get(class_fqn, {}).get("functions", [])

    # def get_member_variables(self, class_fqn: str) -> list[ReifiedSymbol]:
    #     return self.object_fqns_to_members.get(class_fqn, {}).get("variables", [])

    # def get_containing_class(self, symbol: ReifiedSymbol) -> ReifiedSymbol | None:
    #     if not symbol.raw.fully_qualified_parent_path:
    #         return None
    #     parent_fqn = symbol.raw.fully_qualified_parent_path

    #     for file_symbols in self.file_to_symbols.values():
    #         for sym in file_symbols:
    #             if (
    #                 sym.is_definition
    #                 and sym.raw.symbol_kind == SymbolKind.DATA_STRUCTURE
    #                 and get_fully_qualified_name(sym.raw) == parent_fqn
    #             ):
    #                 return sym
    #     return None

    def print_summary(self, files: list[Path] | None = None, sep: str = "::") -> None:
        RESET = "\033[0m"
        BLUE = "\033[94m"
        GREEN = "\033[92m"
        YELLOW = "\033[93m"
        # CYAN = "\033[96m"
        MAGENTA = "\033[95m"
        RED = "\033[91m"
        BOLD = "\033[1m"
        ORANGE = "\033[38;5;208m"

        targets = files if files else sorted(self.file_to_symbols.keys())

        for fpath in targets:
            reified_syms = self.file_to_symbols.get(fpath)
            if reified_syms is None:
                print(f"{YELLOW}No symbols found for {fpath}{RESET}")
                continue

            print(f"\n{BOLD}{BLUE}File: {fpath}{RESET}")
            for sym in reified_syms:
                name = sym.raw.name
                lines = f"[lines {sym.raw.start_line}-{sym.raw.end_line}]"
                # sym_file_path = sym.raw.file_path

                # Show fully qualified name for C++ symbols
                fqn = get_fully_qualified_name(sym=sym.raw, sep=sep)
                name_display = fqn if sym.raw.fully_qualified_parent_path else name

                if sym.is_definition:
                    usage_count = len(sym.usages)
                    decl_count = len(sym.declarations)

                    # Special handling for classes/structs
                    if sym.raw.symbol_kind == SymbolKind.DATA_STRUCTURE:
                        members = sym.children
                        member_functions = [
                            m
                            for m in members
                            if m.raw.symbol_kind == SymbolKind.CALLABLE
                        ]
                        member_variables = [
                            m
                            for m in members
                            if m.raw.symbol_kind == SymbolKind.VARIABLE
                        ]
                        member_func_count = len(member_functions)
                        member_var_count = len(member_variables)
                        print(
                            f"{GREEN}  📦 CLASS/STRUCT: {BOLD}{name_display}{RESET}{GREEN} {lines} "
                            f"[{usage_count} usage(s), {decl_count} declaration(s)]{RESET}"
                        )

                        if member_func_count > 0 or member_var_count > 0:
                            print(
                                f"     {BOLD}Members:{RESET} {member_func_count} function(s), {member_var_count} variable(s)"
                            )

                        # Show member functions
                        if member_functions:
                            print(f"     {BOLD}Functions:{RESET}")
                            for member_func in member_functions:
                                mf_name = member_func.raw.name
                                mf_lines = f"[lines {member_func.raw.start_line}-{member_func.raw.end_line}]"
                                mf_usage_count = len(member_func.usages)
                                print(
                                    f"{RED}       🔧 {mf_name} {mf_lines} [{mf_usage_count} usage(s)]{RESET}"
                                )

                        # Show member variables
                        if member_variables:
                            print(f"     {BOLD}Variables:{RESET}")
                            for member_var in member_variables:
                                mv_name = member_var.raw.name
                                mv_lines = f"[lines {member_var.raw.start_line}-{member_var.raw.end_line}]"
                                mv_usage_count = len(member_var.usages)
                                print(
                                    f"{RED}       📌 {mv_name} {mv_lines} [{mv_usage_count} usage(s)]{RESET}"
                                )
                        if sym.inheritance:
                            print(
                                f"     {BOLD}Inheritance:{RESET} "
                                f"{', '.join(get_fully_qualified_name(i.raw, sep) for i in sym.inheritance)}"
                            )
                    else:
                        # Check if this is a member function
                        is_member = sym.raw.fully_qualified_parent_path is not None
                        icon = (
                            "🔧" if sym.raw.symbol_kind == SymbolKind.CALLABLE else "📍"
                        )
                        member_prefix = "MEMBER " if is_member else ""

                        print(
                            f"{GREEN}  {icon} {member_prefix}DEF: {BOLD}{name_display}{RESET}{GREEN} {lines} "
                            f"[{usage_count} usage(s), {decl_count} declaration(s)]{RESET}"
                        )

                        # Show the containing class if this is a member
                        if is_member:
                            containing = sym.parent
                            if containing:
                                print(
                                    f"     {BOLD}Member of:{RESET} {get_fully_qualified_name(containing.raw, sep)} [lines {containing.raw.start_line}-{containing.raw.end_line}] "
                                )

                    # Show declarations for this definition
                    if sym.declarations:
                        print(f"     {BOLD}Declarations:{RESET}")
                        for decl_sym in sym.declarations:
                            decl_name = get_fully_qualified_name(
                                sym=decl_sym.raw, sep=sep
                            )
                            decl_lines = (
                                f"[lines {decl_sym.raw.start_line}-"
                                f"{decl_sym.raw.end_line}]"
                            )
                            decl_file_path = decl_sym.raw.file_path
                            print(
                                f"{MAGENTA}       📄 {decl_name} {decl_lines} "
                                f"in {decl_file_path}{RESET}"
                            )

                    # If this is a CALLABLE definition, show the calls it makes
                    if sym.raw.symbol_kind == SymbolKind.CALLABLE and sym.calls:
                        print(f"     {BOLD}Calls {len(sym.calls)} function(s):{RESET}")
                        for called_func in sym.calls:
                            called_name = get_fully_qualified_name(
                                sym=called_func.raw, sep=sep
                            )
                            c_lines = (
                                f"[lines {called_func.raw.start_line}-"
                                f"{called_func.raw.end_line}]"
                            )
                            c_path = called_func.raw.file_path
                            print(
                                f"       ↪️  {ORANGE}{called_name} {c_lines} in {c_path}{RESET}"
                            )

                    # Show usages
                    if sym.usages:
                        print(f"     {BOLD}Used in:{RESET}")
                        for _i, usage_sym in enumerate(
                            sym.usages[:5]
                        ):  # Limit to first 5
                            # usage_name = get_fully_qualified_name(sym=usage_sym.raw, sep=sep)
                            usage_lines = (
                                f"[lines {usage_sym.raw.start_line}-"
                                f"{usage_sym.raw.end_line}]"
                            )
                            usage_file_path = usage_sym.raw.file_path
                            print(
                                f"{YELLOW}       🔗 {usage_lines} "
                                f"in {usage_file_path}{RESET}"
                            )
                        if len(sym.usages) > 5:
                            print(f"       ... and {len(sym.usages) - 5} more usage(s)")

                elif sym.is_declaration:
                    if sym.definition:
                        def_name = get_fully_qualified_name(
                            sym=sym.definition.raw, sep=sep
                        )
                        def_lines = (
                            f"[lines {sym.definition.raw.start_line}-"
                            f"{sym.definition.raw.end_line}]"
                        )
                        def_file_path = sym.definition.raw.file_path
                        print(
                            f"{MAGENTA}  📄 DECL: {BOLD}{name_display}{RESET}{MAGENTA} {lines} "
                            f"→ {def_name} {def_lines} in {def_file_path}{RESET}"
                        )
                    else:
                        print(
                            f"{MAGENTA}  📄 DECL: {BOLD}{name_display}{RESET}{MAGENTA} {lines} "
                            f"→ no definition found{RESET}"
                        )

                else:  # usage
                    if sym.definition:
                        def_name = get_fully_qualified_name(
                            sym=sym.definition.raw, sep=sep
                        )
                        def_lines = (
                            f"[lines {sym.definition.raw.start_line}-"
                            f"{sym.definition.raw.end_line}]"
                        )
                        def_file_path = sym.definition.raw.file_path
                        # print(
                        #     f"{CYAN}  🔗 USE: {BOLD}{name_display}{RESET}{CYAN} {lines} "
                        #     f"→ {def_name} {def_lines} in {def_file_path}{RESET}"
                        # )
                    # else:
                    #     print(
                    #         f"{CYAN}  🔗 USE: {BOLD}{name_display}{RESET}{CYAN} {lines} "
                    #         f"→ no definition found{RESET}"
                    #     )


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
        p.resolve()
        for p in project_root.rglob("*")
        if p.suffix.lower() in (".c", ".h", ".cpp", ".cc", ".cxx", ".hpp", ".hxx")
    ]


def main() -> None:
    # project_root = Path("/Users/andrewmark/Downloads/sqlite")
    project_root = Path("/Users/shaneghiotto/driver/uploaded_codebases/cpp_test3")

    file_paths = discover_c_and_h_files(project_root)

    index = build_c_project_index(file_paths, project_root)

    # focus_file = Path("sqlite/src/btree.c")  # Note this is project-relative
    # index.print_summary([focus_file])
    index.print_summary()


if __name__ == "__main__":
    main()
