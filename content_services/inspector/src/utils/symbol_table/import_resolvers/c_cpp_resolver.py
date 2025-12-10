from collections import defaultdict
from pathlib import Path

from utils.lang_specialization.symbol_common import RawTreeSitterSymbolData

from ..base import SymbolResolver


def _compute_visibility_scc(
    file_to_symbols: dict[Path, list[RawTreeSitterSymbolData]],
    includes_map: dict[Path, list[RawTreeSitterSymbolData]],
    resolver: SymbolResolver,
) -> dict[Path, set[Path]]:
    """Use Tarjan's algorithm to find SCCs and process as DAG."""
    # Build adjacency list
    graph: dict[Path, set[Path]] = defaultdict(set)
    for fpath in file_to_symbols:
        for inc_sym in includes_map.get(fpath, []):
            inc_path = resolver.resolve_import(fpath, inc_sym, file_to_symbols)
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


class CCppResolver(SymbolResolver):
    language = "c_cpp"

    def resolve_imports_to_symbols(
        self,
        all_files_imports: dict[Path, list[RawTreeSitterSymbolData]],
        all_files_symbols: dict[Path, list[RawTreeSitterSymbolData]],
        num_workers: int | None,
        project_root: Path,
    ) -> dict[Path, set[RawTreeSitterSymbolData]]:
        visible_symbols = defaultdict(set)
        file_visibility_map = _compute_visibility_scc(
            file_to_symbols=all_files_symbols,
            includes_map=all_files_imports,
            resolver=self,
        )
        for fpath, visible_files in file_visibility_map.items():
            for vf in visible_files:
                visible_symbols[fpath].update(all_files_symbols.get(vf, []))
        return visible_symbols

    def resolve_import(
        self,
        current_file: Path,
        import_sym: RawTreeSitterSymbolData,
        project_files_to_symbols_map: dict[Path, list[RawTreeSitterSymbolData]],
    ) -> Path | list[Path] | None:
        """
        Resolve C/C++ #include directives to project files.

        Minimal attempt: if `current_file.parent/include_str` is in the project, return it.
        Otherwise, look for a file in project_files that ends with include_str as a fallback.
        If collisions happen, pick the first or None.
        """
        project_files = set(project_files_to_symbols_map.keys())
        # 1) Direct local path approach
        candidate = (current_file.parent / import_sym.name).resolve()
        if candidate in project_files:
            return candidate

        # 2) Fallback: see which project files end with include_str
        #    e.g. "foo/bar.h" might match ".../some/path/foo/bar.h"
        possible_matches = [
            pf for pf in project_files if str(pf).endswith(import_sym.name)
        ]
        if not possible_matches:
            return None
        if len(possible_matches) == 1:
            return possible_matches[0]

        # If multiple matches remain, pick one. Crudely, we just pick the first.
        return possible_matches[0]
