"""
Tests for Ruby import resolver
"""

from pathlib import Path

import pytest
from shared.inspector.utils.lang_specialization.symbol_common import (
    RawTreeSitterSymbolData,
    SymbolKind,
)
from shared.inspector.utils.treesitter_drivers.ruby_driver import (
    RubyRequireBespokeMarker,
)

from .ruby_resolver import RubyResolver


def create_import_symbol(name: str, is_relative: bool) -> RawTreeSitterSymbolData:
    """Helper to create import symbols with Ruby-specific bespoke data"""
    return RawTreeSitterSymbolData(
        name=name,
        start_line=1,
        end_line=1,
        start_byte=0,
        end_byte=0,
        file_path=Path(""),
        symbol_kind=SymbolKind.IMPORT,
        fully_qualified_parent_path=None,
        symbol_code=None,
        delimiter=None,
        base_class_names=None,
        bespoke_data=RubyRequireBespokeMarker(is_relative=is_relative),
    )


class TestRubyResolver:
    """Test Ruby import resolution functionality"""

    @pytest.fixture
    def resolver(self) -> RubyResolver:
        return RubyResolver()

    @pytest.fixture
    def project_files(self) -> set[Path]:
        """Create a mock Ruby project file structure"""
        return {
            # App structure (Rails-like)
            Path("/project/app/models/user.rb"),
            Path("/project/app/models/team.rb"),
            Path("/project/app/models/admin/user.rb"),
            Path("/project/app/controllers/users_controller.rb"),
            Path("/project/app/controllers/admin/users_controller.rb"),
            Path("/project/app/services/authentication_service.rb"),
            # Lib directory
            Path("/project/lib/authentication.rb"),
            Path("/project/lib/utils/string_helper.rb"),
            Path("/project/lib/utils/date_helper.rb"),
            # Config
            Path("/project/config/database.rb"),
            Path("/project/config/environments/production.rb"),
            # Test directory
            Path("/project/test/models/user_test.rb"),
            Path("/project/test/test_helper.rb"),
        }

    # ========================================================================
    # require_relative - Same Directory
    # ========================================================================

    def test_require_relative_same_directory(
        self, resolver: RubyResolver, project_files: set[Path]
    ) -> None:
        """Test resolving require_relative from the same directory"""
        current_file = Path("/project/app/models/user.rb")
        symbol = create_import_symbol(name="./team", is_relative=True)

        result = resolver._resolve_import(current_file, symbol, project_files)
        assert result == Path("/project/app/models/team.rb")

    def test_require_relative_same_directory_with_rb_extension(
        self, resolver: RubyResolver, project_files: set[Path]
    ) -> None:
        """Test that .rb extension is handled correctly"""
        current_file = Path("/project/app/models/user.rb")
        symbol = create_import_symbol(name="./team.rb", is_relative=True)

        result = resolver._resolve_import(current_file, symbol, project_files)
        assert result == Path("/project/app/models/team.rb")

    def test_require_relative_without_dot_slash(
        self, resolver: RubyResolver, project_files: set[Path]
    ) -> None:
        """Test require_relative without ./ prefix (valid Ruby)"""
        current_file = Path("/project/app/models/user.rb")
        symbol = create_import_symbol(name="team", is_relative=True)

        result = resolver._resolve_import(current_file, symbol, project_files)
        assert result == Path("/project/app/models/team.rb")

    # ========================================================================
    # require_relative - Parent Directory
    # ========================================================================

    def test_require_relative_parent_directory(
        self, resolver: RubyResolver, project_files: set[Path]
    ) -> None:
        """Test resolving require_relative from parent directory"""
        current_file = Path("/project/app/controllers/users_controller.rb")
        symbol = create_import_symbol(name="../models/user", is_relative=True)

        result = resolver._resolve_import(current_file, symbol, project_files)
        assert result == Path("/project/app/models/user.rb")

    def test_require_relative_multiple_parent_levels(
        self, resolver: RubyResolver, project_files: set[Path]
    ) -> None:
        """Test navigating up multiple directory levels"""
        current_file = Path("/project/app/controllers/admin/users_controller.rb")
        symbol = create_import_symbol(name="../../models/user", is_relative=True)

        result = resolver._resolve_import(current_file, symbol, project_files)
        assert result == Path("/project/app/models/user.rb")

    def test_require_relative_from_test_to_app(
        self, resolver: RubyResolver, project_files: set[Path]
    ) -> None:
        """Test requiring from test directory to app directory"""
        current_file = Path("/project/test/models/user_test.rb")
        symbol = create_import_symbol(name="../../app/models/user", is_relative=True)

        result = resolver._resolve_import(current_file, symbol, project_files)
        assert result == Path("/project/app/models/user.rb")

    # ========================================================================
    # require_relative - Child Directory
    # ========================================================================

    def test_require_relative_child_directory(
        self, resolver: RubyResolver, project_files: set[Path]
    ) -> None:
        """Test resolving require_relative to child directory"""
        current_file = Path("/project/app/models/user.rb")
        symbol = create_import_symbol(name="./admin/user", is_relative=True)

        result = resolver._resolve_import(current_file, symbol, project_files)
        assert result == Path("/project/app/models/admin/user.rb")

    def test_require_relative_nested_path(
        self, resolver: RubyResolver, project_files: set[Path]
    ) -> None:
        """Test requiring deeply nested files"""
        current_file = Path("/project/app/models/user.rb")
        symbol = create_import_symbol(
            name="../../config/environments/production", is_relative=True
        )

        result = resolver._resolve_import(current_file, symbol, project_files)
        assert result == Path("/project/config/environments/production.rb")

    # ========================================================================
    # require_relative - Path Normalization
    # ========================================================================

    def test_require_relative_with_redundant_segments(
        self, resolver: RubyResolver, project_files: set[Path]
    ) -> None:
        """Test that redundant path segments are normalized"""
        current_file = Path("/project/app/controllers/users_controller.rb")
        symbol = create_import_symbol(
            name="./../controllers/../models/user", is_relative=True
        )

        result = resolver._resolve_import(current_file, symbol, project_files)
        assert result == Path("/project/app/models/user.rb")

    def test_require_relative_complex_navigation(
        self, resolver: RubyResolver, project_files: set[Path]
    ) -> None:
        """Test complex relative path navigation"""
        current_file = Path("/project/config/environments/production.rb")
        symbol = create_import_symbol(name="../../lib/authentication", is_relative=True)

        result = resolver._resolve_import(current_file, symbol, project_files)
        assert result == Path("/project/lib/authentication.rb")

    # ========================================================================
    # require (absolute) - Basic Resolution
    # ========================================================================

    def test_require_absolute_in_lib(
        self, resolver: RubyResolver, project_files: set[Path]
    ) -> None:
        """Test resolving absolute require from lib directory"""
        current_file = Path("/project/app/models/user.rb")
        symbol = create_import_symbol(name="authentication", is_relative=False)

        result = resolver._resolve_import(current_file, symbol, project_files)
        assert result == Path("/project/lib/authentication.rb")

    def test_require_absolute_with_nested_path(
        self, resolver: RubyResolver, project_files: set[Path]
    ) -> None:
        """Test requiring with nested path in name"""
        current_file = Path("/project/app/models/user.rb")
        symbol = create_import_symbol(name="utils/string_helper", is_relative=False)

        result = resolver._resolve_import(current_file, symbol, project_files)
        assert result == Path("/project/lib/utils/string_helper.rb")

    def test_require_absolute_single_exact_match(self, resolver: RubyResolver) -> None:
        """Test that a single exact match is resolved correctly"""
        project_files = {
            Path("/project/lib/user.rb"),
            Path("/project/lib/team.rb"),
        }
        current_file = Path("/project/app/controllers/users_controller.rb")
        symbol = create_import_symbol(name="user", is_relative=False)

        result = resolver._resolve_import(current_file, symbol, project_files)
        # Should find the single exact match
        assert result == Path("/project/lib/user.rb")

    def test_require_absolute_exact_match_only(self, resolver: RubyResolver) -> None:
        """Test that only exact filename matches are resolved, not partial matches"""
        project_files = {
            Path("/project/lib/user.rb"),
            Path("/project/lib/user_service.rb"),
            Path("/project/lib/admin_user.rb"),
        }
        current_file = Path("/project/app/models/team.rb")
        symbol = create_import_symbol(name="user", is_relative=False)

        result = resolver._resolve_import(current_file, symbol, project_files)
        # Should match user.rb exactly (single exact match)
        assert result == Path("/project/lib/user.rb")

    # ========================================================================
    # Edge Cases - Not Found
    # ========================================================================

    def test_require_relative_not_found_returns_none(
        self, resolver: RubyResolver, project_files: set[Path]
    ) -> None:
        """Test that non-existent files return None"""
        current_file = Path("/project/app/models/user.rb")
        symbol = create_import_symbol(name="./nonexistent", is_relative=True)

        result = resolver._resolve_import(current_file, symbol, project_files)
        assert result is None

    def test_require_absolute_not_found_returns_none(
        self, resolver: RubyResolver, project_files: set[Path]
    ) -> None:
        """Test that non-existent absolute requires return None"""
        current_file = Path("/project/app/models/user.rb")
        symbol = create_import_symbol(name="nonexistent_gem", is_relative=False)

        result = resolver._resolve_import(current_file, symbol, project_files)
        assert result is None

    def test_require_relative_wrong_directory_returns_none(
        self, resolver: RubyResolver, project_files: set[Path]
    ) -> None:
        """Test that incorrect relative paths return None"""
        current_file = Path("/project/app/models/user.rb")
        symbol = create_import_symbol(
            name="../controllers/nonexistent", is_relative=True
        )

        result = resolver._resolve_import(current_file, symbol, project_files)
        assert result is None

    # ========================================================================
    # Edge Cases - External Dependencies
    # ========================================================================

    def test_external_gem_returns_none(
        self, resolver: RubyResolver, project_files: set[Path]
    ) -> None:
        """Test that external gem requires return None (not in project)"""
        current_file = Path("/project/app/models/user.rb")

        # Common Rails/Ruby gems
        rails_symbol = create_import_symbol(name="rails", is_relative=False)
        rspec_symbol = create_import_symbol(name="rspec", is_relative=False)
        active_support = create_import_symbol(
            name="active_support/core_ext", is_relative=False
        )

        assert (
            resolver._resolve_import(current_file, rails_symbol, project_files) is None
        )
        assert (
            resolver._resolve_import(current_file, rspec_symbol, project_files) is None
        )
        assert (
            resolver._resolve_import(current_file, active_support, project_files)
            is None
        )

    # ========================================================================
    # Edge Cases - Ambiguous Matches
    # ========================================================================

    def test_exact_match_with_similar_filenames(self, resolver: RubyResolver) -> None:
        """Test that only exact filename matches are resolved"""
        project_files = {
            Path("/project/lib/authentication.rb"),
            Path("/project/lib/authentication_service.rb"),
            Path("/project/lib/user_authentication.rb"),
        }
        current_file = Path("/project/app/models/user.rb")
        symbol = create_import_symbol(name="authentication", is_relative=False)

        result = resolver._resolve_import(current_file, symbol, project_files)
        # Should match authentication.rb exactly, not the others
        assert result == Path("/project/lib/authentication.rb")

    def test_partial_match_returns_none(self, resolver: RubyResolver) -> None:
        """Test that partial/substring matches do NOT resolve (no false positives)"""
        project_files = {
            Path("/project/lib/user_service.rb"),
            Path("/project/lib/admin_user.rb"),
            Path("/project/lib/super_user.rb"),
        }
        current_file = Path("/project/app/models/team.rb")
        symbol = create_import_symbol(name="user", is_relative=False)

        result = resolver._resolve_import(current_file, symbol, project_files)
        # No exact match for 'user', should return None even though
        # 'user' is contained in these filenames
        assert result is None

    def test_ambiguous_multiple_exact_matches_returns_none(
        self, resolver: RubyResolver
    ) -> None:
        """Test that multiple exact matches return None (ambiguous)"""
        project_files = {
            Path("/project/lib/user.rb"),
            Path("/project/app/models/user.rb"),
            Path("/project/services/user.rb"),
        }
        current_file = Path("/project/app/controllers/users_controller.rb")
        symbol = create_import_symbol(name="user", is_relative=False)

        result = resolver._resolve_import(current_file, symbol, project_files)
        # Multiple exact matches - ambiguous, return None to be safe
        assert result is None

    def test_namespace_path_exact_match(
        self, resolver: RubyResolver, project_files: set[Path]
    ) -> None:
        """Test that nested paths match exactly"""
        current_file = Path("/project/app/models/user.rb")
        symbol = create_import_symbol(name="utils/date_helper", is_relative=False)

        result = resolver._resolve_import(current_file, symbol, project_files)
        assert result == Path("/project/lib/utils/date_helper.rb")

    # ========================================================================
    # Integration Tests - Full Resolution Flow
    # ========================================================================

    def test_resolve_imports_to_symbols_basic(self, resolver: RubyResolver) -> None:
        """Test the full resolve_imports_to_symbols method"""
        project_files_map = {
            Path("/project/app/models/user.rb"): [],  # symbols would go here
            Path("/project/app/models/team.rb"): [],
            Path("/project/lib/authentication.rb"): [],
        }

        imports_map = {
            Path("/project/app/models/user.rb"): [
                create_import_symbol(name="./team", is_relative=True),
                create_import_symbol(name="authentication", is_relative=False),
            ]
        }

        result = resolver.resolve_imports_to_symbols(
            all_files_imports=imports_map,
            all_files_symbols=project_files_map,
            num_workers=None,
            project_root=Path("/project"),
        )

        # user.rb should have visibility to both team.rb and authentication.rb
        assert Path("/project/app/models/user.rb") in result
        # The actual symbols would be populated in real usage
        # Here we're just testing the resolution logic works

    def test_resolve_imports_to_symbols_handles_none_results(
        self, resolver: RubyResolver
    ) -> None:
        """Test that unresolved imports don't cause errors"""
        project_files_map = {
            Path("/project/app/models/user.rb"): [],
        }

        imports_map = {
            Path("/project/app/models/user.rb"): [
                create_import_symbol(name="./nonexistent", is_relative=True),
                create_import_symbol(name="external_gem", is_relative=False),
            ]
        }

        result = resolver.resolve_imports_to_symbols(
            all_files_imports=imports_map,
            all_files_symbols=project_files_map,
            num_workers=None,
            project_root=Path("/project"),
        )

        # Should handle gracefully - user.rb has no visible symbols
        user_path = Path("/project/app/models/user.rb")
        assert user_path in result
        assert len(result[user_path]) == 0

    # ========================================================================
    # Specific Ruby Patterns
    # ========================================================================

    def test_require_test_helper(
        self, resolver: RubyResolver, project_files: set[Path]
    ) -> None:
        """Test common pattern of requiring test_helper"""
        current_file = Path("/project/test/models/user_test.rb")
        symbol = create_import_symbol(name="../test_helper", is_relative=True)

        result = resolver._resolve_import(current_file, symbol, project_files)
        assert result == Path("/project/test/test_helper.rb")

    def test_rails_config_pattern(
        self, resolver: RubyResolver, project_files: set[Path]
    ) -> None:
        """Test common Rails config require pattern"""
        current_file = Path("/project/config/database.rb")
        symbol = create_import_symbol(
            name="./environments/production", is_relative=True
        )

        result = resolver._resolve_import(current_file, symbol, project_files)
        assert result == Path("/project/config/environments/production.rb")

    def test_service_requiring_model(
        self, resolver: RubyResolver, project_files: set[Path]
    ) -> None:
        """Test service layer requiring models"""
        current_file = Path("/project/app/services/authentication_service.rb")
        symbol = create_import_symbol(name="../models/user", is_relative=True)

        result = resolver._resolve_import(current_file, symbol, project_files)
        assert result == Path("/project/app/models/user.rb")

    # ========================================================================
    # Extension Handling
    # ========================================================================

    def test_rb_extension_automatically_added(
        self, resolver: RubyResolver, project_files: set[Path]
    ) -> None:
        """Test that .rb extension is added when missing"""
        current_file = Path("/project/app/models/user.rb")

        # Without extension
        symbol_no_ext = create_import_symbol(name="./team", is_relative=True)
        result = resolver._resolve_import(current_file, symbol_no_ext, project_files)
        assert result == Path("/project/app/models/team.rb")

        # With extension
        symbol_with_ext = create_import_symbol(name="./team.rb", is_relative=True)
        result = resolver._resolve_import(current_file, symbol_with_ext, project_files)
        assert result == Path("/project/app/models/team.rb")

    def test_preserves_exact_path_object(self, resolver: RubyResolver) -> None:
        """Test that the exact Path object from project_files is returned"""
        path1 = Path("/project/lib/authentication.rb")
        path2 = Path("/project/lib/utils/string_helper.rb")
        project_files = {path1, path2}

        current_file = Path("/project/app/models/user.rb")
        symbol = create_import_symbol(name="authentication", is_relative=False)

        result = resolver._resolve_import(current_file, symbol, project_files)

        # Should return the exact same object, not a new Path
        assert result is path1
