from collections import defaultdict
from os import sep
from pathlib import Path

from utils.lang_specialization.symbol_common import RawTreeSitterSymbolData

from ..base import SymbolResolver


class JavaResolver(SymbolResolver):
    language = "java"

    def resolve_imports_to_symbols(
        self,
        all_files_imports: dict[Path, list[RawTreeSitterSymbolData]],
        all_files_symbols: dict[Path, list[RawTreeSitterSymbolData]],
        num_workers: int | None,
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

    def resolve_import(
        self,
        current_file: Path,
        import_sym: RawTreeSitterSymbolData,
        project_files_to_symbols_map: dict[Path, list[RawTreeSitterSymbolData]],
    ) -> Path | list[Path] | None:
        """
        Resolve Java import statements to project files.
        """
        project_files = set(project_files_to_symbols_map.keys())
        project_files_lst = list(project_files)

        import_str_pathified = Path(import_sym.name.replace(".", sep)).with_suffix(
            ".java"
        )

        # 1) For cases like `import com.abc.ClassName` implemented in `/com/abc/ClassName.java`
        candidate = import_str_pathified
        for idx, f in enumerate(project_files_lst):
            if str(candidate) in str(f):
                return [project_files_lst[idx]]
            elif str(candidate.parent) == ".":
                return None

        # 2) Attempt at handling package imports e.g. `package com.xyz` and `import com.abc.*`
        package_str = import_sym.name.replace(".", sep)
        packages = []
        for idx, f in enumerate(project_files_lst):
            f_str = sep.join(str(f).split(sep)[:-1])  # Remove the file name
            if f_str.endswith(package_str):
                packages.append(project_files_lst[idx])
        return packages
        # TODO: should also return a bool to indicate not to do the DFS

        return None
