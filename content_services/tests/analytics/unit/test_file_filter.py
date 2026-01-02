"""
Tests for file filtering to ensure parity with inspector.

TDD: These tests define the expected behavior BEFORE implementation.
The filtering logic must match the inspector's is_analyzable criteria.
"""
import pytest


class TestBlacklistDirectories:
    """Test directory blacklisting matches inspector."""
    
    def test_git_directory_blacklisted(self):
        from analytics.utils.file_filter import is_blacklisted_path
        
        assert is_blacklisted_path(('.git',))
        assert is_blacklisted_path(('.git', 'config'))
        assert is_blacklisted_path(('src', '.git', 'HEAD'))
        
    def test_driver_docs_blacklisted(self):
        from analytics.utils.file_filter import is_blacklisted_path
        
        assert is_blacklisted_path(('driver_docs',))
        assert is_blacklisted_path(('driver_docs', 'README.md'))
        
    def test_normal_paths_not_blacklisted(self):
        from analytics.utils.file_filter import is_blacklisted_path
        
        assert not is_blacklisted_path(('src',))
        assert not is_blacklisted_path(('src', 'main.py'))
        assert not is_blacklisted_path(('tests', 'test_main.py'))
        assert not is_blacklisted_path(('docs', 'api.md'))


class TestBlacklistExtensions:
    """Test extension blacklisting matches inspector."""
    
    def test_image_extensions_blacklisted(self):
        from analytics.utils.file_filter import is_blacklisted_extension
        
        assert is_blacklisted_extension('.svg')
        
    def test_binary_extensions_blacklisted(self):
        from analytics.utils.file_filter import is_blacklisted_extension
        
        assert is_blacklisted_extension('.hex')
        assert is_blacklisted_extension('.bin')
        assert is_blacklisted_extension('.BIN')
        assert is_blacklisted_extension('.dat')
        assert is_blacklisted_extension('.DAT')
        assert is_blacklisted_extension('.exe')
        assert is_blacklisted_extension('.o')
        assert is_blacklisted_extension('.a')
        assert is_blacklisted_extension('.so')
        assert is_blacklisted_extension('.dll')
        assert is_blacklisted_extension('.dylib')
        assert is_blacklisted_extension('.cdylib')
        assert is_blacklisted_extension('.axf')
        assert is_blacklisted_extension('.elf')
        
    def test_code_extensions_not_blacklisted(self):
        from analytics.utils.file_filter import is_blacklisted_extension
        
        assert not is_blacklisted_extension('.py')
        assert not is_blacklisted_extension('.js')
        assert not is_blacklisted_extension('.ts')
        assert not is_blacklisted_extension('.java')
        assert not is_blacklisted_extension('.go')
        assert not is_blacklisted_extension('.rs')
        assert not is_blacklisted_extension('.c')
        assert not is_blacklisted_extension('.cpp')
        assert not is_blacklisted_extension('.h')


class TestBlacklistFilenames:
    """Test filename blacklisting matches inspector."""
    
    def test_ds_store_blacklisted(self):
        from analytics.utils.file_filter import is_blacklisted_filename
        
        assert is_blacklisted_filename('.DS_Store')
        
    def test_driverignore_blacklisted(self):
        from analytics.utils.file_filter import is_blacklisted_filename
        
        assert is_blacklisted_filename('.driverignore')
        
    def test_normal_filenames_not_blacklisted(self):
        from analytics.utils.file_filter import is_blacklisted_filename
        
        assert not is_blacklisted_filename('main.py')
        assert not is_blacklisted_filename('README.md')
        assert not is_blacklisted_filename('.gitignore')
        assert not is_blacklisted_filename('Dockerfile')


class TestHexDetection:
    """Test hex file detection matches inspector (>40% threshold)."""
    
    def test_pure_hex_content_detected(self):
        from analytics.utils.file_filter import is_hex_content
        
        # 100% hex characters
        hex_content = b"0123456789abcdefABCDEF" * 10
        assert is_hex_content(hex_content)
        
    def test_mostly_hex_content_detected(self):
        from analytics.utils.file_filter import is_hex_content
        
        # >40% hex characters (hex dump style)
        hex_dump = b"00 01 02 03 04 05 06 07 08 09 0a 0b 0c 0d 0e 0f\n" * 10
        assert is_hex_content(hex_dump)
        
    def test_normal_code_not_hex(self):
        from analytics.utils.file_filter import is_hex_content
        
        code = b"def hello():\n    print('Hello, World!')\n    return True\n"
        assert not is_hex_content(code)
        
    def test_json_not_hex(self):
        from analytics.utils.file_filter import is_hex_content
        
        json_content = b'{"name": "test", "value": 123, "active": true}\n'
        assert not is_hex_content(json_content)
        
    def test_empty_content_not_hex(self):
        from analytics.utils.file_filter import is_hex_content
        
        assert not is_hex_content(b"")
        assert not is_hex_content(None)


class TestLanguageRecognition:
    """Test language recognition using languages.yml."""
    
    def test_python_extension_recognized(self):
        from analytics.utils.file_filter import has_recognized_language
        
        assert has_recognized_language('.py', 'main.py')
        
    def test_javascript_extensions_recognized(self):
        from analytics.utils.file_filter import has_recognized_language
        
        assert has_recognized_language('.js', 'app.js')
        assert has_recognized_language('.ts', 'app.ts')
        assert has_recognized_language('.jsx', 'Component.jsx')
        assert has_recognized_language('.tsx', 'Component.tsx')
        
    def test_common_code_extensions_recognized(self):
        from analytics.utils.file_filter import has_recognized_language
        
        assert has_recognized_language('.java', 'Main.java')
        assert has_recognized_language('.go', 'main.go')
        assert has_recognized_language('.rs', 'main.rs')
        assert has_recognized_language('.c', 'main.c')
        assert has_recognized_language('.cpp', 'main.cpp')
        assert has_recognized_language('.h', 'header.h')
        assert has_recognized_language('.rb', 'app.rb')
        assert has_recognized_language('.php', 'index.php')
        
    def test_markdown_not_recognized_as_code(self):
        from analytics.utils.file_filter import has_recognized_language
        
        # Markdown should NOT be recognized as analyzable code
        # This is key to matching inspector behavior
        assert not has_recognized_language('.md', 'README.md')
        assert not has_recognized_language('.rst', 'docs.rst')
        
    def test_config_files_not_recognized_as_code(self):
        from analytics.utils.file_filter import has_recognized_language
        
        # Config files should NOT be recognized
        assert not has_recognized_language('.json', 'package.json')
        assert not has_recognized_language('.toml', 'pyproject.toml')
        assert not has_recognized_language('.ini', 'config.ini')
        
    def test_special_filenames_recognized(self):
        from analytics.utils.file_filter import has_recognized_language
        
        # Some files are recognized by name, not extension
        assert has_recognized_language('', 'Dockerfile')
        assert has_recognized_language('', 'Makefile')


class TestIsAnalyzableFile:
    """Test the complete is_analyzable logic matching inspector."""
    
    def test_python_file_analyzable(self):
        from analytics.utils.file_filter import is_analyzable_file
        
        assert is_analyzable_file(
            path_parts=('src', 'main.py'),
            filename='main.py',
            extension='.py',
            is_binary=False
        )
        
    def test_javascript_file_analyzable(self):
        from analytics.utils.file_filter import is_analyzable_file
        
        assert is_analyzable_file(
            path_parts=('src', 'app.js'),
            filename='app.js',
            extension='.js',
            is_binary=False
        )
        
    def test_binary_file_not_analyzable(self):
        from analytics.utils.file_filter import is_analyzable_file
        
        assert not is_analyzable_file(
            path_parts=('assets', 'image.png'),
            filename='image.png',
            extension='.png',
            is_binary=True
        )
        
    def test_markdown_not_analyzable(self):
        from analytics.utils.file_filter import is_analyzable_file
        
        # Critical: .md should NOT be analyzable (matches inspector)
        assert not is_analyzable_file(
            path_parts=('docs',),
            filename='README.md',
            extension='.md',
            is_binary=False
        )
        
    def test_json_not_analyzable(self):
        from analytics.utils.file_filter import is_analyzable_file
        
        assert not is_analyzable_file(
            path_parts=('',),
            filename='package.json',
            extension='.json',
            is_binary=False
        )
        
    def test_git_directory_file_not_analyzable(self):
        from analytics.utils.file_filter import is_analyzable_file
        
        assert not is_analyzable_file(
            path_parts=('.git', 'config'),
            filename='config',
            extension='',
            is_binary=False
        )
        
    def test_blacklisted_extension_not_analyzable(self):
        from analytics.utils.file_filter import is_analyzable_file
        
        assert not is_analyzable_file(
            path_parts=('build',),
            filename='output.exe',
            extension='.exe',
            is_binary=False  # Even if not detected as binary
        )
        
    def test_hex_file_not_analyzable(self):
        from analytics.utils.file_filter import is_analyzable_file
        
        hex_content = b"0123456789abcdef" * 100
        
        assert not is_analyzable_file(
            path_parts=('data',),
            filename='dump.txt',
            extension='.txt',
            is_binary=False,
            content=hex_content
        )
        
    def test_dockerfile_analyzable(self):
        from analytics.utils.file_filter import is_analyzable_file
        
        assert is_analyzable_file(
            path_parts=('',),
            filename='Dockerfile',
            extension='',
            is_binary=False
        )
        
    def test_makefile_analyzable(self):
        from analytics.utils.file_filter import is_analyzable_file
        
        assert is_analyzable_file(
            path_parts=('',),
            filename='Makefile',
            extension='',
            is_binary=False
        )


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_nested_git_directory(self):
        from analytics.utils.file_filter import is_analyzable_file
        
        # File deep in .git should not be analyzable
        assert not is_analyzable_file(
            path_parts=('.git', 'objects', 'pack', 'file'),
            filename='file',
            extension='',
            is_binary=False
        )
        
    def test_file_with_git_in_name_but_not_directory(self):
        from analytics.utils.file_filter import is_analyzable_file
        
        # "git" in filename shouldn't trigger blacklist
        assert is_analyzable_file(
            path_parts=('src',),
            filename='git_utils.py',
            extension='.py',
            is_binary=False
        )
        
    def test_empty_path_parts(self):
        from analytics.utils.file_filter import is_analyzable_file
        
        # Root-level file
        assert is_analyzable_file(
            path_parts=(),
            filename='main.py',
            extension='.py',
            is_binary=False
        )
        
    def test_case_sensitivity_extensions(self):
        from analytics.utils.file_filter import is_blacklisted_extension
        
        # Both .BIN and .bin should be blacklisted
        assert is_blacklisted_extension('.BIN')
        assert is_blacklisted_extension('.bin')

