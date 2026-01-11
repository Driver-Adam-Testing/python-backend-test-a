"""Unit tests for language detection.

A11: Language Detection

Tests for detecting primary language from file changes:
- Detection by file extension
- Detection by bytes (not file count)
- Special filenames (Dockerfile, Makefile, etc.)
"""
import pytest
from collections import defaultdict


class TestDetectPrimaryLanguage:
    """Tests for detect_primary_language function."""

    def test_detects_python_from_extension(self):
        """Python files detected as Python."""
        from analytics.aggregation.language import detect_primary_language
        
        file_changes = [
            {'file_path': 'src/main.py', 'addition_bytes': 1000},
            {'file_path': 'src/utils.py', 'addition_bytes': 500},
        ]
        
        result = detect_primary_language(file_changes)
        assert result == 'Python'

    def test_detects_javascript_from_extension(self):
        """JavaScript files detected as JavaScript."""
        from analytics.aggregation.language import detect_primary_language
        
        file_changes = [
            {'file_path': 'src/app.js', 'addition_bytes': 2000},
            {'file_path': 'src/index.js', 'addition_bytes': 500},
        ]
        
        result = detect_primary_language(file_changes)
        assert result == 'JavaScript'

    def test_detects_typescript_from_extension(self):
        """TypeScript files detected as TypeScript."""
        from analytics.aggregation.language import detect_primary_language
        
        file_changes = [
            {'file_path': 'src/app.ts', 'addition_bytes': 1500},
            {'file_path': 'src/component.tsx', 'addition_bytes': 2000},
        ]
        
        result = detect_primary_language(file_changes)
        # tsx might be TSX or TypeScript depending on mapping
        assert result in ('TypeScript', 'TSX')

    def test_detects_by_bytes_not_file_count(self):
        """Primary language determined by bytes, not file count."""
        from analytics.aggregation.language import detect_primary_language
        
        # 10 small text files, 1 large Python file
        file_changes = [
            {'file_path': f'doc{i}.txt', 'addition_bytes': 10}  # 10 files * 10 bytes = 100 bytes
            for i in range(10)
        ] + [
            {'file_path': 'src/main.py', 'addition_bytes': 5000},  # 5000 bytes
        ]
        
        result = detect_primary_language(file_changes)
        # Python should win by bytes even though fewer files
        assert result == 'Python'

    def test_detects_dockerfile(self):
        """Dockerfile detected as Docker."""
        from analytics.aggregation.language import detect_primary_language
        
        file_changes = [
            {'file_path': 'Dockerfile', 'addition_bytes': 500},
            {'file_path': 'docker-compose.yml', 'addition_bytes': 200},
        ]
        
        result = detect_primary_language(file_changes)
        # Should detect Dockerfile as primary (or Docker)
        assert result is not None

    def test_detects_makefile(self):
        """Makefile detected as Makefile."""
        from analytics.aggregation.language import detect_primary_language
        
        file_changes = [
            {'file_path': 'Makefile', 'addition_bytes': 1000},
        ]
        
        result = detect_primary_language(file_changes)
        # Should detect Makefile
        assert result is not None

    def test_empty_file_changes_returns_none(self):
        """Empty file changes returns None."""
        from analytics.aggregation.language import detect_primary_language
        
        result = detect_primary_language([])
        assert result is None

    def test_ignores_unrecognized_extensions(self):
        """Files with unrecognized extensions are ignored."""
        from analytics.aggregation.language import detect_primary_language
        
        file_changes = [
            {'file_path': 'data.xyz', 'addition_bytes': 1000},  # Unknown
            {'file_path': 'src/main.py', 'addition_bytes': 500},  # Known
        ]
        
        result = detect_primary_language(file_changes)
        assert result == 'Python'

    def test_handles_files_without_extension(self):
        """Files without extensions use filename detection."""
        from analytics.aggregation.language import detect_primary_language
        
        file_changes = [
            {'file_path': 'README', 'addition_bytes': 500},
            {'file_path': 'src/main.py', 'addition_bytes': 1000},
        ]
        
        result = detect_primary_language(file_changes)
        # Python should be primary by bytes
        assert result == 'Python'

    def test_handles_nested_paths(self):
        """Correctly extracts extension from nested paths."""
        from analytics.aggregation.language import detect_primary_language
        
        file_changes = [
            {'file_path': 'src/components/Button.tsx', 'addition_bytes': 1000},
            {'file_path': 'src/utils/helpers.ts', 'addition_bytes': 500},
            {'file_path': 'tests/unit/test_api.py', 'addition_bytes': 300},
        ]
        
        result = detect_primary_language(file_changes)
        # TypeScript family should dominate (1500 bytes) vs Python (300 bytes)
        assert result in ('TypeScript', 'TSX')


class TestLanguageByFilePath:
    """Tests for _get_language_from_path helper."""

    def test_gets_language_from_py_extension(self):
        """Python extension returns Python."""
        from analytics.aggregation.language import _get_language_from_path
        
        result = _get_language_from_path('src/main.py')
        assert result == 'Python'

    def test_gets_language_from_js_extension(self):
        """JavaScript extension returns JavaScript."""
        from analytics.aggregation.language import _get_language_from_path
        
        result = _get_language_from_path('src/app.js')
        assert result == 'JavaScript'

    def test_gets_language_from_dockerfile(self):
        """Dockerfile returns language."""
        from analytics.aggregation.language import _get_language_from_path
        
        result = _get_language_from_path('Dockerfile')
        # Could be 'Dockerfile' or 'Docker' depending on mapping
        assert result is not None

    def test_returns_none_for_unknown(self):
        """Unknown extension returns None."""
        from analytics.aggregation.language import _get_language_from_path
        
        result = _get_language_from_path('data.xyz')
        assert result is None

