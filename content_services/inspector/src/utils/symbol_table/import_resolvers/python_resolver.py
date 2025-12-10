from collections import defaultdict
from os import sep
from pathlib import Path

from utils.lang_specialization.symbol_common import RawTreeSitterSymbolData

from ..base import SymbolResolver


class PythonResolver(SymbolResolver):
    language = "python"

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
                resolved_path = self.resolve_import(
                    current_file=file_path,
                    import_sym=import_sym,
                    project_files_to_symbols_map=all_files_symbols,
                )
                if resolved_path is not None:
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
        Resolve Python import statements to project files.
        """
        project_files = set(project_files_to_symbols_map.keys())
        project_files_lst = list(project_files)

        import_str_pathified = Path(import_sym.name.replace(".", sep)).with_suffix(
            ".py"
        )

        # 1) For cases like `import my_module` implemented in `/some_path/my_module.py`
        candidate = import_str_pathified
        for idx, f in enumerate(project_files_lst):
            if str(candidate) in str(f):
                return project_files_lst[idx]
            elif str(candidate.parent) == ".":
                # Avoid adding `import random` erroneously in the next section when using `parent`
                return None

        # 2) For `from my_module import fn` or `import my_module.fn` in `/some_path/my_module.py`
        try:
            candidate = import_str_pathified.parent.with_suffix(".py")
        except ValueError:
            # import_str_pathified.parent is just "/" or similar in this case, and can't be resolved
            return None
        for idx, f in enumerate(project_files_lst):
            if str(candidate) in str(f):
                return project_files_lst[idx]

        # 3) TODO: Figure out how to handle subfolders as modules (with __init__.py)

        return None
