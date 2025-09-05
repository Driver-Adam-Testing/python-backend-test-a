from collections import defaultdict
from pathlib import Path

from utils.lang_specialization.symbol_common import RawTreeSitterSymbolData

from ..base import SymbolResolver


class CCppResolver(SymbolResolver):
    language = "c_cpp"

    # TODO: DFS
    def resolve_imports_to_symbols(
        self,
        all_files_imports: dict[Path, list[RawTreeSitterSymbolData]],
        all_files_symbols: dict[Path, list[RawTreeSitterSymbolData]],
        num_workers: int | None,
    ) -> dict[Path, set[RawTreeSitterSymbolData]]:
        visible_symbols = defaultdict(set)
        for file_path in all_files_imports:
            for import_sym in all_files_imports[file_path]:
                resolved_path = self.resolve_import(
                    current_file=file_path,
                    import_sym=import_sym,
                    project_files_to_symbols_map=all_files_symbols,
                )
                if resolved_path:
                    visible_symbols[file_path].update(
                        all_files_symbols.get(resolved_path, [])
                    )
        # TODO: handle aliases here?
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
