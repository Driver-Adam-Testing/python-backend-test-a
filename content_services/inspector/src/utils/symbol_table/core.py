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

from .base import ImportResolver, SymbolParser
from .utils import get_fully_qualified_name, is_declaration, is_definition


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
        parser: SymbolParser,
        num_workers: int | None = None,
    ) -> Self:
        def parse_and_handle(abs_fpath: Path) -> tuple[Path, list, list, dict]:
            from .utils import to_root_relative

            rel_fpath = to_root_relative(abs_fpath, project_root)
            try:
                symbols, includes, containment_map = parser.parse_file(
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
        resolver: ImportResolver,
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
                inc_path = resolver.resolve_import(current, inc_str, project_files)
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
    is_base_class: bool = False
    base_name: str | None = None
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
                        # TODO: this works for C, but C++ may have issues with namespaces that limit this
                        decl_candidates = declarations_by_fqn.get(rsym.name, [])
                        vis_decls = [
                            (dpath, d_raw)
                            for (dpath, d_raw) in decl_candidates
                            if d_raw.file_path in visible_with_self
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
                elif (
                    is_definition(rsym)
                    and rsym.symbol_kind == SymbolKind.DATA_STRUCTURE
                ):
                    # For DATA_STRUCTURE, we look for base classes
                    if (
                        rsym.base_class_names is not None
                        and len(rsym.base_class_names) > 0
                    ):
                        for base_name in rsym.base_class_names:
                            candidates = definitions_by_name.get(base_name, [])
                            fqn_candidates = definitions_by_fqn.get(base_name, [])
                            for fqn_candidate in fqn_candidates:
                                if fqn_candidate not in candidates:
                                    candidates.append(fqn_candidate)
                            vis_defs = [
                                (dfpath, dfsym)
                                for (dfpath, dfsym) in candidates
                                if dfpath in visible_with_self
                            ]
                            if len(vis_defs) >= 1:
                                # pick first or unify
                                dfpath, def_raw = vis_defs[0]
                                # TODO: hack. Better way is to extract base classes in DriverTree classes
                                # and use other symbol table mechanics to link them
                                linked_syms.append(
                                    LinkedSymbol(
                                        raw=def_raw,
                                        is_definition=False,
                                        is_declaration=False,
                                        is_base_class=True,
                                        base_name=base_name,
                                        definition=None,
                                    )
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
                        for base_class in lsym.raw.base_class_names:
                            # Find a matching linked symbol
                            for base_ls in ls_list:
                                if (
                                    base_ls.is_base_class
                                    and base_ls.base_name == base_class
                                ):
                                    # We found a base class in the same file
                                    inherits_from.append(final_map[base_ls])
                                    break
                        if len(inherits_from):
                            old_reif = final_map[lsym]
                            final_map[lsym] = replace(
                                old_reif,
                                inherits_from=inherits_from,
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

        return cls(file_to_symbols=file_map)
