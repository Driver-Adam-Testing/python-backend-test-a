from collections import defaultdict
from pathlib import Path

from shared.inspector.utils.lang_specialization.symbol_common import (
    RawTreeSitterSymbolData,
    SymbolKind,
)
from shared.inspector.utils.treesitter_drivers.csharp_driver import (
    CSharpImportScopeKind,
)

from ..base import SymbolResolver


def _is_namespace(sym: RawTreeSitterSymbolData) -> bool:
    return (
        sym.bespoke_data.scoping_kind
        == CSharpImportScopeKind.NAMESPACE_BLOCK_SCOPE_DECL
        or sym.bespoke_data.scoping_kind
        == CSharpImportScopeKind.NAMESPACE_FILE_SCOPE_DECL
    )


class CSharpResolver(SymbolResolver):
    language = "csharp"
    _cached_namespace_data: (
        tuple[set[str], defaultdict[str, list[RawTreeSitterSymbolData]]] | None
    ) = None
    _cached_global_using_data: list[Path] | None = None

    def resolve_imports_to_symbols(
        self,
        all_files_imports: dict[Path, list[RawTreeSitterSymbolData]],
        all_files_symbols: dict[Path, list[RawTreeSitterSymbolData]],
        num_workers: int | None,
        project_root: Path,
    ) -> dict[Path, set[RawTreeSitterSymbolData]]:
        visible_symbols = defaultdict(set)
        for file_path in all_files_imports:
            for import_sym in all_files_imports[file_path]:
                resolved_paths = self.resolve_import(
                    current_file=file_path,
                    import_sym=import_sym,
                    project_files_to_symbols_map=all_files_symbols,
                )
                for path in resolved_paths:
                    visible_symbols[file_path].update(all_files_symbols.get(path, []))
        # TODO: handle aliases here?
        return visible_symbols

    def _namespace_resolver(
        self, project_files_to_symbols_map: dict[Path, list[RawTreeSitterSymbolData]]
    ) -> tuple[set[str], defaultdict[str, list[Path]]]:
        namespaces_map = defaultdict(list)
        for path, symbols in project_files_to_symbols_map.items():
            for sym in symbols:
                if sym.symbol_kind == SymbolKind.IMPORT and _is_namespace(sym):
                    namespaces_map[sym.name].append(path)
        namespaces_set = set(namespaces_map.keys())

        return namespaces_set, namespaces_map

    def _global_using_resolver(
        self,
        project_files_to_symbols_map: dict[Path, list[RawTreeSitterSymbolData]],
        namespaces_set: set[str],
        namespaces_map: defaultdict[str, list[RawTreeSitterSymbolData]],
    ) -> list[Path]:
        global_paths_list = []
        for symbols in project_files_to_symbols_map.values():
            for sym in symbols:
                if (
                    sym.symbol_kind == SymbolKind.IMPORT
                    and sym.bespoke_data.scoping_kind
                    == CSharpImportScopeKind.GLOBAL_USING
                ):
                    if sym.name in namespaces_set:
                        global_paths_list.extend(namespaces_map[sym.name])
                    else:
                        parts = sym.name.split(sym.delimiter)[:-1]
                        stripped_name = sym.delimiter.join(parts)
                        if stripped_name in namespaces_set:
                            # TODO: Just add the single symbol!
                            global_paths_list.extend(namespaces_map[stripped_name])

        return global_paths_list

    def resolve_import(
        self,
        current_file: Path,
        import_sym: RawTreeSitterSymbolData,
        project_files_to_symbols_map: dict[Path, list[RawTreeSitterSymbolData]],
    ) -> Path | list[Path] | None:
        """
        Resolve C# import statements and namespace declarations to project files.

        0) Make sure some pre-computed `namespace` and `global using` data has been computed.
        1) Add all `global using` symbols, if present.
        2) Handle (local) `using` statement by comparing with `namespace` map, if applicable.
        3) Handle `namespace`s declaration, if applicable.
        """
        if not self._cached_namespace_data:
            self._cached_namespace_data = self._namespace_resolver(
                project_files_to_symbols_map=project_files_to_symbols_map
            )
        namespaces_set, namespaces_map = self._cached_namespace_data

        if not self._cached_global_using_data:
            self._cached_global_using_data = self._global_using_resolver(
                project_files_to_symbols_map=project_files_to_symbols_map,
                namespaces_set=namespaces_set,
                namespaces_map=namespaces_map,
            )
        visible_paths = []

        # Handle `global using` first.
        visible_paths.extend(self._cached_global_using_data)

        # First test to see if the `using` <name> is a namespace.
        # - if True, then include all files with that namespace.
        # - if False, then chew off a suffix one time and see if the remainder is a namespace.
        if not _is_namespace(import_sym):
            if import_sym.name in namespaces_set:
                visible_paths.extend(namespaces_map[import_sym.name])
            else:
                parts = import_sym.name.split(import_sym.delimiter)[:-1]
                stripped_name = import_sym.delimiter.join(parts)
                if stripped_name in namespaces_set:
                    # TODO: Just add the single symbol!
                    visible_paths.extend(namespaces_map[stripped_name])
        else:
            paths = None
            if import_sym.name in namespaces_set:
                paths = namespaces_map.get(import_sym.name)
            if paths:
                visible_paths.extend(namespaces_map[import_sym.name])
            else:
                print("Untracked `namespace` declaration")

        return visible_paths
