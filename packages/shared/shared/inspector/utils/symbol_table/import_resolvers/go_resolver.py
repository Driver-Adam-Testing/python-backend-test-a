"""
Go Import Resolver

Go Module System Overview:
- Each go.mod file defines a module with a name (e.g., "github.com/org/project")
- Import paths starting with the module name resolve to local files
- External imports (different module names) are dependencies, not project files
- Monorepos can have multiple modules, each with their own go.mod

Strategy:
1. Group all .go files by their nearest ancestor go.mod file
2. For each module group:
   - Extract module name from go.mod
   - Build package-to-files mapping (e.g., "myproject/pkg/utils" -> [util1.go, util2.go])
   - Resolve imports within that module's context only
3. Dictionary lookups per import

Example Repository Structure:
my-repo/
├── go.mod (module "myproject")
├── main.go
├── pkg/
│   └── utils/
│       ├── helper.go
│       └── math.go
└── services/
    ├── go.mod (module "myproject/services")  # Nested module
    └── api.go

Input Paths (repo-relative with repo name as first component):
- Path("my-repo/main.go")
- Path("my-repo/pkg/utils/helper.go")
- Path("my-repo/services/api.go")

Package Mappings:
- Main module: {"myproject": [Path("my-repo/main.go")], "myproject/pkg/utils": [Path("my-repo/pkg/utils/helper.go"), Path("my-repo/pkg/utils/math.go")]}
- Services module: {"myproject/services": [Path("my-repo/services/api.go")]}

Import Resolution:
- my-repo/main.go imports "myproject/pkg/utils" -> resolves to [helper.go, math.go]
- my-repo/services/api.go imports "myproject/pkg/utils" -> no resolution (different module)
- my-repo/main.go imports "fmt" -> no resolution (standard library, external)
"""

import os
import re
from collections import defaultdict
from functools import lru_cache
from pathlib import Path

from shared.inspector.utils.lang_specialization.symbol_common import (
    RawTreeSitterSymbolData,
)
from shared.inspector.utils.treesitter_drivers.go_driver import GoImportData

from ..base import SymbolResolver

DEBUG = os.getenv("DEBUG", "").lower() in ("1", "true", "yes")


class GoResolver(SymbolResolver):
    language = "go"

    def resolve_imports_to_symbols(
        self,
        all_files_imports: dict[Path, list[RawTreeSitterSymbolData]],
        all_files_symbols: dict[Path, list[RawTreeSitterSymbolData]],
        num_workers: int | None,
        project_root: Path,
    ) -> dict[Path, set[RawTreeSitterSymbolData]]:
        if DEBUG:
            print(f"\nGoResolver: Processing {len(all_files_symbols)} files")
            print("Files with imports:", list(all_files_imports.keys()))

        visible_symbols = defaultdict(set)

        # Group files by their nearest go.mod
        module_groups = self._group_files_by_module(
            set(all_files_symbols.keys()), project_root
        )

        if DEBUG:
            print(f"Found {len(module_groups)} Go modules:")
            for go_mod_path, files in module_groups.items():
                print(f"  - {go_mod_path} ({len(files)} files)")

        # We can process each module separately
        for go_mod_path, module_files in module_groups.items():
            module_name = self._get_module_name(go_mod_path, project_root)
            if not module_name:
                if DEBUG:
                    print(f"Warning: Could not extract module name from {go_mod_path}")
                continue

            if DEBUG:
                print(f"\nProcessing module '{module_name}' at {go_mod_path}")

            # Build package mapping for this module
            # Maps import paths to actual files: "myproject/pkg/utils" -> [helper.go, math.go]
            package_mapping = self._build_package_mapping(
                module_name, go_mod_path.parent, module_files
            )

            if DEBUG:
                print(f"Package mapping for '{module_name}':")
                for pkg_path, files in package_mapping.items():
                    print(f"  {pkg_path} -> {[f.name for f in files]}")

            # Resolve imports for files in this module
            total_imports = 0
            resolved_imports = 0
            for file_path in module_files:
                if file_path not in all_files_imports:
                    continue

                file_imports = all_files_imports[file_path]
                if file_imports and DEBUG:
                    print(f"\nProcessing imports in {file_path.name}:")

                for import_sym in file_imports:
                    total_imports += 1
                    if not isinstance(import_sym.bespoke_data, GoImportData):
                        if DEBUG:
                            print(f"  ERROR: {import_sym.name}: No GoImportData")
                        continue

                    import_data: GoImportData = import_sym.bespoke_data

                    # Skip special imports that don't resolve to symbols
                    if import_data.blank_import or import_data.dot_import:
                        if DEBUG:
                            print(
                                f"  SKIP: {import_data.package_path}: Blank/dot import"
                            )
                        continue

                    # Only imports matching this module's name will be found
                    resolved_files = package_mapping.get(import_data.package_path, [])
                    if resolved_files:
                        resolved_imports += 1
                        if DEBUG:
                            print(
                                f"  RESOLVED: {import_data.package_path} -> {[f.name for f in resolved_files]}"
                            )
                        for resolved_file in resolved_files:
                            resolved_symbols = all_files_symbols.get(resolved_file, [])
                            if DEBUG:
                                print(
                                    f"    Adding {len(resolved_symbols)} symbols from {resolved_file.name}"
                                )
                                if resolved_symbols:
                                    print(
                                        f"      Symbols: {[s.name for s in resolved_symbols[:3]]}{'...' if len(resolved_symbols) > 3 else ''}"
                                    )
                            visible_symbols[file_path].update(resolved_symbols)
                    else:
                        if DEBUG:
                            print(
                                f"  EXTERNAL: {import_data.package_path}: No matching package (external/stdlib)"
                            )

            if DEBUG:
                print(
                    f"\nModule summary: {resolved_imports}/{total_imports} imports resolved"
                )

        total_visible = sum(len(syms) for syms in visible_symbols.values())
        if DEBUG:
            print(
                f"\nTotal visible symbols: {total_visible} across {len(visible_symbols)} files"
            )

            if visible_symbols:
                print("Visibility breakdown:")
                for file_path, symbols in visible_symbols.items():
                    print(f"  {file_path.name}: {len(symbols)} visible symbols")

        return visible_symbols

    @lru_cache(maxsize=128)
    def _find_go_mod_file(self, start_path: Path, project_root: Path) -> Path | None:
        """Find go.mod file by walking up directory tree."""
        current = start_path.parent if start_path.is_file() else start_path

        # Handle repo-relative paths - don't go above repo root
        original_parts = current.parts
        if not original_parts:
            return None

        while len(current.parts) > 1:
            go_mod_path = current / "go.mod"
            abs_go_mod_path = project_root / Path(*go_mod_path.parts[1:])
            if abs_go_mod_path.exists():
                return go_mod_path
            current = current.parent

        # Check repo root too
        go_mod_path = current / "go.mod"
        abs_go_mod_path = project_root / Path(*go_mod_path.parts[1:])
        if abs_go_mod_path.exists():
            return go_mod_path
        return None

    @lru_cache(maxsize=128)
    def _get_module_name(self, go_mod_path: Path, project_root: Path) -> str | None:
        try:
            abs_go_mod_path = project_root / Path(*go_mod_path.parts[1:])
            content = abs_go_mod_path.read_text(encoding="utf-8")
            # Match, for example "module github.com/org/project"
            match = re.search(r"^module\s+(.+)$", content, re.MULTILINE)
            return match.group(1).strip() if match else None
        except (OSError, UnicodeDecodeError):
            return None

    def _group_files_by_module(
        self, project_files: set[Path], project_root: Path
    ) -> dict[Path, set[Path]]:
        """Group repo-relative project files by their nearest go.mod file."""
        module_groups = defaultdict(set)

        for file_path in project_files:
            if file_path.suffix != ".go":
                continue

            go_mod_path = self._find_go_mod_file(file_path, project_root)
            if go_mod_path:
                module_groups[go_mod_path].add(file_path)

        return dict(module_groups)

    def _build_package_mapping(
        self, module_name: str, module_root: Path, module_files: set[Path]
    ) -> dict[str, list[Path]]:
        """Build mapping from package paths to repo-relative Go files within a module."""
        package_mapping = defaultdict(list)

        for file_path in module_files:
            # Calculate package path relative to module root
            try:
                rel_path = file_path.parent.relative_to(module_root)
                if str(rel_path) == ".":
                    # File is in module root
                    package_path = module_name
                else:
                    # File is in subdirectory
                    package_path = f"{module_name}/{rel_path.as_posix()}"

                package_mapping[package_path].append(file_path)
            except ValueError:
                # File is not under module root, skip it
                continue

        return dict(package_mapping)
