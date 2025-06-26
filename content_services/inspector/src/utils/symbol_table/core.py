from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, replace
from enum import StrEnum
from pathlib import Path
from typing import Self

from utils.lang_specialization.symbol_common import (
    RawTreeSitterSymbolData,
    ReifiedSymbol,
    SymbolKind,
)

from .base import ImportResolver, SymbolParser
from .comparison import TimingInfo, timer
from .utils import (
    disambiguate_call,
    get_fully_qualified_name,
    is_data_structure,
    is_declaration,
    is_definition,
)

MAX_LLM_CALLS_PER_FILE = 25


class VisibilityAlgorithm(StrEnum):
    """Algorithm choices for computing file visibility."""

    DFS = "dfs"  # Original DFS approach
    BFS = "bfs"  # BFS with reverse graph
    FIXPOINT = "fixpoint"  # Incremental fixpoint
    SCC = "scc"  # Strongly connected components


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
            except Exception as e:
                print(f"  Warning: Failed to parse {rel_fpath}: {e}")
                symbols, includes, containment_map = [], [], {}
            return rel_fpath, symbols, includes, containment_map

        file_to_syms = {}
        raw_includes = {}
        file_to_containment_map = {}

        if num_workers is None or num_workers == 1:
            # Serial processing
            total = len(file_paths)
            for i, abs_fpath in enumerate(file_paths, 1):
                if i % 25 == 0 or i == total:
                    print(f"  Parsing files... [{i}/{total}]", flush=True)
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
                total = len(file_paths)
                for i, future in enumerate(as_completed(future_to_path), 1):
                    rel_fpath, symbols, includes, containment_map = future.result()
                    if i % 25 == 0 or i == total:
                        print(f"  Parsing files... [{i}/{total}]", flush=True)
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
        algorithm: VisibilityAlgorithm = VisibilityAlgorithm.SCC,
        return_timing: bool = False,
    ) -> Self | tuple[Self, TimingInfo]:
        """
        Build a map from each file -> all files it can 'see' transitively.
        Only links includes that are in parsed.file_to_symbols (our project).

        return_timing: Whether to return timing information
        """
        file_to_symbols = parsed.file_to_symbols
        includes_map = parsed.includes_map

        timing = TimingInfo()

        with timer() as visibility_timer:
            match algorithm:
                case VisibilityAlgorithm.DFS:
                    visibility_map = cls._compute_visibility_dfs(
                        file_to_symbols,
                        includes_map,
                        resolver,
                        num_workers,
                    )
                case VisibilityAlgorithm.BFS:
                    visibility_map = cls._compute_visibility_reverse_bfs(
                        file_to_symbols,
                        includes_map,
                        resolver,
                        num_workers,
                    )
                case VisibilityAlgorithm.FIXPOINT:
                    visibility_map = cls._compute_visibility_incremental_fixed_point(
                        file_to_symbols, includes_map, resolver
                    )
                case VisibilityAlgorithm.SCC:
                    visibility_map = cls._compute_visibility_scc(
                        file_to_symbols, includes_map, resolver
                    )
                case _:
                    raise ValueError(f"Unknown visibility algorithm: {algorithm}")

        timing.visibility_time = visibility_timer["elapsed"]

        result = cls(
            file_to_symbols=file_to_symbols,
            includes_map=includes_map,
            visibility_map=visibility_map,
        )

        if return_timing:
            return result, timing
        return result

    @classmethod
    def _compute_visibility_dfs(
        cls,
        file_to_symbols: dict[Path, list],
        includes_map: dict[Path, list[str]],
        resolver: ImportResolver,
        num_workers: int | None,
    ) -> dict[Path, set[Path]]:
        """Original DFS-based visibility computation."""
        visibility_map: dict[Path, set[Path]] = {}

        def dfs(current: Path, visited: set[Path]) -> None:
            for inc_str in includes_map.get(current, []):
                inc_path = resolver.resolve_import(current, inc_str, file_to_symbols)
                if isinstance(inc_path, list):
                    for p in inc_path:
                        if p not in visited:
                            visited.add(p)
                            # NOTE: Right now we only reach here in Java,
                            # and for Java we don't do DFS here since imports must be explicit
                else:
                    if inc_path and inc_path not in visited:
                        visited.add(inc_path)
                        dfs(inc_path, visited)

        def compute_visited(fpath: Path) -> set[Path]:
            visited: set[Path] = {fpath}
            dfs(fpath, visited)
            return visited

        # For each file, do a DFS of includes:
        total = len(file_to_symbols)
        if num_workers is None or num_workers == 1:
            # Serial processing
            for i, fpath in enumerate(file_to_symbols, 1):
                if i % 25 == 0 or i == total:
                    print(f"  Resolving visibility... [{i}/{total}]", flush=True)
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
                    if i % 25 == 0 or i == total:
                        print(f"  Resolving visibility... [{i}/{total}]", flush=True)
                    visibility_map[future_to_path[future]] = visited

        return visibility_map

    @classmethod
    def _compute_visibility_incremental_fixed_point(
        cls,
        file_to_symbols: dict[Path, list],
        includes_map: dict[Path, list[str]],
        resolver: ImportResolver,
    ) -> dict[Path, set[Path]]:
        """Incremental fixpoint approach (works with cycles)."""
        # Initialize with direct includes
        visibility_map: dict[Path, set[Path]] = {}
        for fpath in file_to_symbols:
            visibility_map[fpath] = {fpath}

        # Build initial direct dependencies
        for fpath in file_to_symbols:
            for inc_str in includes_map.get(fpath, []):
                inc_path = resolver.resolve_import(fpath, inc_str, file_to_symbols)
                if isinstance(inc_path, list):
                    visibility_map[fpath].update(inc_path)
                elif inc_path:
                    visibility_map[fpath].add(inc_path)

        # Iteratively expand until fixpoint
        changed = True
        iteration = 0
        while changed:
            changed = False
            iteration += 1

            for fpath in file_to_symbols:
                old_size = len(visibility_map[fpath])

                # For each visible file, add its visibility
                to_add = set()
                for visible in list(visibility_map[fpath]):
                    if visible in visibility_map:
                        to_add.update(visibility_map[visible])

                visibility_map[fpath].update(to_add)

                if len(visibility_map[fpath]) > old_size:
                    changed = True

        print(f"  Fixpoint converged after {iteration} iterations")
        return visibility_map

    @classmethod
    def _compute_visibility_reverse_bfs(
        cls,
        file_to_symbols: dict[Path, list],
        includes_map: dict[Path, list[str]],
        resolver: ImportResolver,
        num_workers: int | None,
    ) -> dict[Path, set[Path]]:
        """Reverse graph + BFS approach for visibility computation."""
        # Build reverse dependency graph (who includes me?)
        reverse_deps: dict[Path, set[Path]] = defaultdict(set)

        for fpath in file_to_symbols:
            for inc_str in includes_map.get(fpath, []):
                inc_path = resolver.resolve_import(fpath, inc_str, file_to_symbols)
                if isinstance(inc_path, list):
                    for p in inc_path:
                        reverse_deps[p].add(fpath)
                elif inc_path:
                    reverse_deps[inc_path].add(fpath)

        # For each file, BFS to find all files that can see it
        visibility_map: dict[Path, set[Path]] = {}

        def compute_visibility(fpath: Path) -> set[Path]:
            visible = {fpath}
            queue = deque([fpath])

            while queue:
                current = queue.popleft()
                # Add files that current file includes
                for inc_str in includes_map.get(current, []):
                    inc_path = resolver.resolve_import(
                        current, inc_str, file_to_symbols
                    )
                    if isinstance(inc_path, list):
                        for p in inc_path:
                            if p not in visible:
                                visible.add(p)
                                # For Java, don't traverse further
                    else:
                        if inc_path and inc_path not in visible:
                            visible.add(inc_path)
                            queue.append(inc_path)

            return visible

        # Process files in parallel or serial
        total = len(file_to_symbols)
        if num_workers is None or num_workers == 1:
            for i, fpath in enumerate(file_to_symbols, 1):
                if i % 25 == 0 or i == total:
                    print(f"  Computing visibility (BFS)... [{i}/{total}]", flush=True)
                visibility_map[fpath] = compute_visibility(fpath)
        else:
            with ThreadPoolExecutor(max_workers=num_workers) as executor:
                future_to_path = {
                    executor.submit(compute_visibility, fp): fp
                    for fp in file_to_symbols
                }
                for i, future in enumerate(as_completed(future_to_path), 1):
                    visible = future.result()
                    fpath = future_to_path[future]
                    if i % 25 == 0 or i == total:
                        print(
                            f"  Computing visibility (BFS)... [{i}/{total}]", flush=True
                        )
                    visibility_map[fpath] = visible

        return visibility_map

    @classmethod
    def _compute_visibility_scc(
        cls,
        file_to_symbols: dict[Path, list],
        includes_map: dict[Path, list[str]],
        resolver: ImportResolver,
    ) -> dict[Path, set[Path]]:
        """Use Tarjan's algorithm to find SCCs and process as DAG."""
        # Build adjacency list
        graph: dict[Path, set[Path]] = defaultdict(set)
        for fpath in file_to_symbols:
            for inc_str in includes_map.get(fpath, []):
                inc_path = resolver.resolve_import(fpath, inc_str, file_to_symbols)
                if isinstance(inc_path, list):
                    for p in inc_path:
                        graph[fpath].add(p)
                elif inc_path:
                    graph[fpath].add(inc_path)

        # Tarjan's algorithm for SCCs
        index_counter = [0]
        stack = []
        lowlinks = {}
        index = {}
        on_stack = defaultdict(bool)
        sccs = []

        def strongconnect(v: Path) -> None:
            index[v] = index_counter[0]
            lowlinks[v] = index_counter[0]
            index_counter[0] += 1
            stack.append(v)
            on_stack[v] = True

            for w in graph[v]:
                if w not in index:
                    strongconnect(w)
                    lowlinks[v] = min(lowlinks[v], lowlinks[w])
                elif on_stack[w]:
                    lowlinks[v] = min(lowlinks[v], index[w])

            if lowlinks[v] == index[v]:
                scc = []
                while True:
                    w = stack.pop()
                    on_stack[w] = False
                    scc.append(w)
                    if w == v:
                        break
                sccs.append(scc)

        # Find all SCCs
        for v in file_to_symbols:
            if v not in index:
                strongconnect(v)

        # Build SCC graph (DAG)
        scc_map = {}
        for i, scc in enumerate(sccs):
            for node in scc:
                scc_map[node] = i

        scc_graph = defaultdict(set)
        for v in graph:
            for w in graph[v]:
                if scc_map[v] != scc_map[w]:
                    scc_graph[scc_map[v]].add(scc_map[w])

        # Compute reachability in SCC DAG
        scc_visibility = defaultdict(set)

        def dfs_scc(scc_id: int, visited: set[int]) -> None:
            for neighbor in scc_graph[scc_id]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    dfs_scc(neighbor, visited)

        for i in range(len(sccs)):
            reachable = {i}
            dfs_scc(i, reachable)
            scc_visibility[i] = reachable

        # Convert back to file visibility
        visibility_map = {}
        for fpath in file_to_symbols:
            visible = {fpath}
            my_scc = scc_map[fpath]

            # Add all files in same SCC
            visible.update(sccs[my_scc])

            # Add all files in reachable SCCs
            for reachable_scc in scc_visibility[my_scc]:
                visible.update(sccs[reachable_scc])

            visibility_map[fpath] = visible

        return visibility_map


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

        file_to_symbols = dict()
        for k, v in project_vis.file_to_symbols.items():
            new_v = []
            for sym in v:
                if sym.symbol_kind != SymbolKind.IMPORT:
                    new_v.append(sym)
            file_to_symbols[k] = new_v

        for fpath, raw_syms in file_to_symbols.items():
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
        for fpath, raw_syms in file_to_symbols.items():
            visible_files = project_vis.visibility_map.get(fpath, set())
            visible_with_self = {fpath, *visible_files}

            llm_calls_made_this_file = 0

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
                    candidate_defs = [
                        (dfpath, dfsym)
                        for (dfpath, dfsym) in candidates
                        if dfpath in visible_with_self
                    ]
                    vis_defs = []
                    for candidate_def in candidate_defs:
                        if (
                            candidate_def[1].file_path == rsym.file_path
                            and candidate_def[1].start_byte < rsym.start_byte
                            and candidate_def[1].end_byte >= rsym.end_byte
                        ):
                            # This would only occur in the case of a recursion.
                            # So we choose to not link it to itself.
                            continue
                        vis_defs.append(candidate_def)
                    if len(vis_defs) >= 1:
                        # pick first or unify
                        dfpath, def_raw = vis_defs[
                            0
                        ]  # TODO: in C++ taking the first is not always correct due to namespace collisions
                        # This is true even for FQN though due overloading
                        if rsym.symbol_kind == SymbolKind.CALL and len(vis_defs) > 1:
                            # Disambiguate
                            calling_symbol = definitions_by_fqn.get(
                                rsym.fully_qualified_parent_path, []
                            )
                            # TODO: disambiguate calling symbol !
                            if len(calling_symbol) > 0:
                                use_llm = (
                                    llm_calls_made_this_file < MAX_LLM_CALLS_PER_FILE
                                )
                                index, llm_called = disambiguate_call(
                                    vis_defs, rsym, calling_symbol[0][1], use_llm
                                )
                                if llm_called:
                                    llm_calls_made_this_file += 1
                                if index is not None and index < len(vis_defs):
                                    dfpath, def_raw = vis_defs[index]
                                    # TODO: if we fail to get here, default to first element
                                else:
                                    dfpath = None
                                    def_raw = None
                        if def_raw is not None:
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
                elif is_definition(rsym) and is_data_structure(rsym):
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
            if lsym.is_definition and is_data_structure(lsym.raw):
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
                elif is_data_structure(lsym.raw):
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
