from collections import defaultdict
from pathlib import Path
from typing import TYPE_CHECKING

from utils.lang_specialization.symbol_common import RawTreeSitterSymbolData

from ..base import SymbolResolver

if TYPE_CHECKING:
    from utils.treesitter_drivers.ruby_driver import RubyRequireBespokeMarker


class RubyResolver(SymbolResolver):
    language = "ruby"

    def resolve_imports_to_symbols(
        self,
        all_files_imports: dict[Path, list[RawTreeSitterSymbolData]],
        all_files_symbols: dict[Path, list[RawTreeSitterSymbolData]],
        num_workers: int | None,
        project_root: Path,
    ) -> dict[Path, set[RawTreeSitterSymbolData]]:
        """
        Resolve Ruby require/require_relative statements to project files.

        Handles both:
        - require_relative: resolved relative to the current file's directory
        - require: searched across project files
        """
        visible_symbols = defaultdict(set)
        for file_path in all_files_imports:
            # Ensure file appears in result even if imports don't resolve
            visible_symbols[file_path]  # Touch the key to ensure it exists

            for import_sym in all_files_imports[file_path]:
                resolved_path = self._resolve_import(
                    current_file=file_path,
                    import_sym=import_sym,
                    project_files=set(all_files_symbols.keys()),
                )
                if resolved_path is not None:
                    visible_symbols[file_path].update(
                        all_files_symbols.get(resolved_path, [])
                    )
        return visible_symbols

    def _resolve_import(
        self,
        current_file: Path,
        import_sym: RawTreeSitterSymbolData,
        project_files: set[Path],
    ) -> Path | None:
        file_set = project_files

        import_name = import_sym.name
        if not import_name:
            return None

        bespoke_data: RubyRequireBespokeMarker = import_sym.bespoke_data

        if bespoke_data.is_relative:
            return self._resolve_relative_import(current_file, import_name, file_set)
        else:
            return self._resolve_absolute_import(import_name, file_set)

    def _resolve_relative_import(
        self, current_file: Path, import_name: str, project_files: set[Path]
    ) -> Path | None:
        """
        Resolve require_relative statements.

        Ruby's require_relative resolves paths relative to the directory
        containing the current file.
        """
        current_dir = current_file.parent

        import_path_str = import_name.removesuffix(".rb")

        full_path = (current_dir / import_path_str).resolve()

        full_path_with_ext = full_path.with_suffix(".rb")

        for project_file in project_files:
            if project_file.resolve() == full_path_with_ext:
                return project_file

        return None

    def _resolve_absolute_import(
        self, import_name: str, project_files: set[Path]
    ) -> Path | None:
        """
        Resolve require statements (absolute imports).

        Simply finds any file in the repo whose path ends with the import path.

        Returns None if:
        - No match found
        - Multiple matches found (ambiguous)
        """
        # Build the suffix: /import_name.rb (remove .rb first if present)
        import_suffix = f"/{import_name.removesuffix('.rb')}.rb"

        # Find all files whose path ends with /import_name.rb
        # The leading / ensures we don't match partial directory names
        matches = [f for f in project_files if str(f).endswith(import_suffix)]

        return matches[0] if len(matches) == 1 else None
