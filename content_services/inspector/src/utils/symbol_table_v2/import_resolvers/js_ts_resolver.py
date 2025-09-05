from collections import defaultdict
from os.path import normpath
from pathlib import Path

from utils.lang_specialization.symbol_common import RawTreeSitterSymbolData
from utils.symbol_table_v2.base import SymbolResolver


class JsTsResolver(SymbolResolver):
    language = "js_ts"

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
    ) -> Path | None:
        """
        Resolve TypeScript import statements to project files.
        """
        project_files_lst = list(project_files_to_symbols_map)
        import_str = import_sym.name

        # Check if it's a relative import
        if not import_str.startswith(("./", "../")):
            return None

        import_path_resolved = Path(normpath(current_file.parent / Path(import_str)))
        for f in project_files_lst:
            if (
                import_path_resolved.suffix in [".ts", ".js"]
                and f == import_path_resolved
            ):
                return f
            elif import_path_resolved.suffix != "":
                continue
            else:
                for candidate_suffix in [".ts", ".js"]:
                    candidate = import_path_resolved.with_suffix(candidate_suffix)
                    if candidate == f:
                        return f

                if (
                    f.parts[-1] in ["index.ts", "index.js"]
                    and import_path_resolved == f.parent
                ):
                    return f
        return None
