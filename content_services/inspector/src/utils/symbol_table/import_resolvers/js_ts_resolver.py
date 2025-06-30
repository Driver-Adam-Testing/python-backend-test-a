from os.path import normpath
from pathlib import Path

from utils.symbol_table.base import ImportResolver


class JsTsResolver(ImportResolver):
    language = "js_ts"

    def resolve_import(
        self, current_file: Path, import_str: str, project_files: set[Path]
    ) -> Path | None:
        """
        Resolve TypeScript import statements to project files.
        """
        project_files_lst = list(project_files)

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
