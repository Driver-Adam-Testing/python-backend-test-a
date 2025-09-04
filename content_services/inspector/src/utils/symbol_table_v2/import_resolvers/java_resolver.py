from os import sep
from pathlib import Path

from utils.lang_specialization.symbol_common import RawTreeSitterSymbolData

from ..base import ImportResolver


class JavaResolver(ImportResolver):
    language = "java"

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
