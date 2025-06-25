from os import sep
from pathlib import Path

from utils.lang_specialization.symbol_common import RawTreeSitterSymbolData

from ..base import ImportResolver


class PythonResolver(ImportResolver):
    language = "python"

    def resolve_import(
        self,
        current_file: Path,
        import_str: str,
        project_files_to_symbols_map: dict[Path, list[RawTreeSitterSymbolData]],
    ) -> Path | list[Path] | None:
        """
        Resolve Python import statements to project files.
        """
        project_files = set(project_files_to_symbols_map.keys())
        project_files_lst = list(project_files)

        import_str_pathified = Path(import_str.replace(".", sep)).with_suffix(".py")

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
