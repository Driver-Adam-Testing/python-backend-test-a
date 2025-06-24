"""
Tests for JavaScript/TypeScript import resolver
"""

from pathlib import Path

import pytest

from .js_ts_resolver import JsTsResolver


class TestJsTsResolver:
    """Test JavaScript/TypeScript import resolution functionality"""

    @pytest.fixture
    def resolver(self) -> JsTsResolver:
        return JsTsResolver()

    @pytest.fixture
    def project_files(self) -> set[Path]:
        """Create a mock project file structure"""
        return {
            Path("/project/src/index.ts"),
            Path("/project/src/utils/helpers.ts"),
            Path("/project/src/utils/index.js"),
            Path("/project/src/components/Button.ts"),
            Path("/project/src/components/index.ts"),
            Path("/project/lib/math.js"),
            Path("/project/lib/string.ts"),
            Path("/project/test/unit.test.ts"),
        }

    def test_resolve_relative_import_same_directory(
        self, resolver: JsTsResolver, project_files: set[Path]
    ) -> None:
        """Test resolving imports from the same directory"""
        current_file = Path("/project/src/utils/helpers.ts")

        # Test .ts extension
        result = resolver.resolve_import(current_file, "./index", project_files)
        assert result == Path("/project/src/utils/index.js")

    def test_resolve_relative_import_parent_directory(
        self, resolver: JsTsResolver, project_files: set[Path]
    ) -> None:
        """Test resolving imports from parent directory"""
        current_file = Path("/project/src/components/Button.ts")

        # Test going up one level
        result = resolver.resolve_import(current_file, "../index", project_files)
        assert result == Path("/project/src/index.ts")

        # Test going up two levels
        result = resolver.resolve_import(current_file, "../../lib/math", project_files)
        assert result == Path("/project/lib/math.js")

    def test_resolve_relative_import_child_directory(
        self, resolver: JsTsResolver, project_files: set[Path]
    ) -> None:
        """Test resolving imports from child directory"""
        current_file = Path("/project/src/index.ts")

        # Test going down into subdirectory
        result = resolver.resolve_import(current_file, "./utils/helpers", project_files)
        assert result == Path("/project/src/utils/helpers.ts")

        # Test another subdirectory
        result = resolver.resolve_import(
            current_file, "./components/Button", project_files
        )
        assert result == Path("/project/src/components/Button.ts")

    def test_resolve_import_with_index_file(
        self, resolver: JsTsResolver, project_files: set[Path]
    ) -> None:
        """Test resolving imports that point to directories with index files"""
        current_file = Path("/project/src/index.ts")

        # Test import of directory with index.js
        result = resolver.resolve_import(current_file, "./utils", project_files)
        assert result == Path("/project/src/utils/index.js")

        # Test import of directory with index.ts
        result = resolver.resolve_import(current_file, "./components", project_files)
        assert result == Path("/project/src/components/index.ts")

    def test_non_relative_import_returns_none(
        self, resolver: JsTsResolver, project_files: set[Path]
    ) -> None:
        """Test that non-relative imports return None"""
        current_file = Path("/project/src/index.ts")

        # Node module imports
        assert resolver.resolve_import(current_file, "react", project_files) is None
        assert (
            resolver.resolve_import(
                current_file, "@testing-library/react", project_files
            )
            is None
        )
        assert (
            resolver.resolve_import(current_file, "lodash/debounce", project_files)
            is None
        )

    def test_import_not_found_returns_none(
        self, resolver: JsTsResolver, project_files: set[Path]
    ) -> None:
        """Test that imports pointing to non-existent files return None"""
        current_file = Path("/project/src/index.ts")

        # File doesn't exist
        assert (
            resolver.resolve_import(current_file, "./non-existent", project_files)
            is None
        )
        assert (
            resolver.resolve_import(current_file, "../missing/file", project_files)
            is None
        )

    def test_complex_relative_paths(
        self, resolver: JsTsResolver, project_files: set[Path]
    ) -> None:
        """Test resolving complex relative paths with multiple ../ segments"""
        current_file = Path("/project/test/unit.test.ts")

        # Navigate up and then down
        result = resolver.resolve_import(
            current_file, "../src/utils/helpers", project_files
        )
        assert result == Path("/project/src/utils/helpers.ts")

        # Navigate to sibling directory
        result = resolver.resolve_import(current_file, "../lib/math", project_files)
        assert result == Path("/project/lib/math.js")

    def test_normalized_paths(
        self, resolver: JsTsResolver, project_files: set[Path]
    ) -> None:
        """Test that paths with redundant segments are normalized correctly"""
        current_file = Path("/project/src/components/Button.ts")

        # Path with redundant segments
        result = resolver.resolve_import(
            current_file, "./../utils/./helpers", project_files
        )
        assert result == Path("/project/src/utils/helpers.ts")

        # Another redundant path
        result = resolver.resolve_import(
            current_file, "../components/../index", project_files
        )
        assert result == Path("/project/src/index.ts")

    def test_exact_file_match_preserves_path_object(
        self, resolver: JsTsResolver
    ) -> None:
        """Test that the exact Path object from project_files is returned"""
        # Create specific Path objects
        path1 = Path("/project/src/index.ts")
        path2 = Path("/project/src/utils.ts")
        project_files = {path1, path2}

        current_file = Path("/project/src/other.ts")
        result = resolver.resolve_import(current_file, "./index", project_files)

        # Should return the exact same object, not a new Path
        assert result is path1

    def test_explicit_extension_respected(
        self, resolver: JsTsResolver, project_files: set[Path]
    ) -> None:
        """Test that explicit extensions in imports are respected"""
        current_file = Path("/project/src/index.ts")

        # When importing with explicit .ts extension, should find the .ts file
        result = resolver.resolve_import(
            current_file, "./components/Button.ts", project_files
        )
        assert result == Path("/project/src/components/Button.ts")

        # When importing with explicit .js extension, should find the .js file
        result = resolver.resolve_import(current_file, "../lib/math.js", project_files)
        assert result == Path("/project/lib/math.js")

        # When importing without extension, should still resolve
        result = resolver.resolve_import(
            current_file, "./components/Button", project_files
        )
        assert result == Path("/project/src/components/Button.ts")

    def test_explicit_extension_not_found(
        self, resolver: JsTsResolver, project_files: set[Path]
    ) -> None:
        """Test that explicit extensions that don't exist return None"""
        current_file = Path("/project/src/index.ts")

        # Button.ts exists, but Button.jsx doesn't
        result = resolver.resolve_import(
            current_file, "./components/Button.jsx", project_files
        )
        assert result is None

        # helpers.ts exists, but helpers.mjs doesn't
        result = resolver.resolve_import(
            current_file, "./utils/helpers.mjs", project_files
        )
        assert result is None
