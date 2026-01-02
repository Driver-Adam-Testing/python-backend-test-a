"""
Integration tests for tree walk with filtering.

TDD: These tests define expected behavior BEFORE modifying _walk_tree_recursive.
The tree walk should only count files matching inspector's is_analyzable criteria.
"""
import pytest
import tempfile
from pathlib import Path
import pygit2


class TestTreeWalkFiltering:
    """Test that tree walk filters files to match inspector."""
    
    @pytest.fixture
    def repo_with_mixed_files(self, tmp_path):
        """
        Create a test repo with various file types:
        - Code files (should be counted)
        - Documentation (should NOT be counted)
        - Config files (should NOT be counted)
        - Binary files (should NOT be counted)
        """
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()
        
        # Code files (SHOULD be counted)
        (repo_path / "main.py").write_text("def hello():\n    print('Hello')\n")  # 2 lines
        (repo_path / "utils.js").write_text("function test() {\n  return true;\n}\n")  # 3 lines
        
        # Create src directory with more code
        src_dir = repo_path / "src"
        src_dir.mkdir()
        (src_dir / "app.py").write_text("class App:\n    pass\n")  # 2 lines
        
        # Documentation (should NOT be counted)
        (repo_path / "README.md").write_text("# Hello\n\nThis is a readme.\n")
        (repo_path / "CHANGELOG.md").write_text("## v1.0\n- Initial release\n")
        
        docs_dir = repo_path / "docs"
        docs_dir.mkdir()
        (docs_dir / "guide.md").write_text("# User Guide\n\nContent here.\n")
        
        # Config files (should NOT be counted)
        (repo_path / "package.json").write_text('{"name": "test"}\n')
        (repo_path / "pyproject.toml").write_text('[project]\nname = "test"\n')
        (repo_path / ".gitignore").write_text("*.pyc\n__pycache__/\n")
        
        # Special files that SHOULD be counted
        (repo_path / "Dockerfile").write_text("FROM python:3.12\nCOPY . .\n")  # 2 lines
        (repo_path / "Makefile").write_text("build:\n\tpython setup.py build\n")  # 2 lines
        
        # Create git repo and commit
        repo = pygit2.init_repository(str(repo_path), bare=False)
        config = repo.config
        config["user.name"] = "Test"
        config["user.email"] = "test@test.com"
        
        index = repo.index
        index.add_all()
        index.write()
        tree = index.write_tree()
        
        sig = pygit2.Signature("Test", "test@test.com")
        repo.create_commit("HEAD", sig, sig, "Initial commit", tree, [])
        
        return repo_path, repo
    
    def test_only_code_files_counted(self, repo_with_mixed_files):
        """Verify only code files are counted, not docs/config."""
        from analytics.pipeline.phases.extract import _get_tree_size_at_commit
        
        repo_path, repo = repo_with_mixed_files
        commit = repo.head.peel(pygit2.Commit)
        
        tree_bytes, tree_lines = _get_tree_size_at_commit(repo, commit)
        
        # Expected code files:
        # main.py: 2 lines
        # utils.js: 3 lines
        # src/app.py: 2 lines
        # Dockerfile: 2 lines
        # Makefile: 2 lines
        # Total: 11 lines
        #
        # NOT counted:
        # README.md, CHANGELOG.md, docs/guide.md
        # package.json, pyproject.toml, .gitignore
        
        assert tree_lines == 11, f"Expected 11 lines (code only), got {tree_lines}"
    
    def test_git_directory_excluded(self, tmp_path):
        """Verify .git directory contents are not counted."""
        from analytics.pipeline.phases.extract import _get_tree_size_at_commit
        
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()
        
        # Create a simple file
        (repo_path / "main.py").write_text("x = 1\n")
        
        # Create repo
        repo = pygit2.init_repository(str(repo_path), bare=False)
        config = repo.config
        config["user.name"] = "Test"
        config["user.email"] = "test@test.com"
        
        index = repo.index
        index.add("main.py")
        index.write()
        tree = index.write_tree()
        
        sig = pygit2.Signature("Test", "test@test.com")
        repo.create_commit("HEAD", sig, sig, "Initial", tree, [])
        
        commit = repo.head.peel(pygit2.Commit)
        tree_bytes, tree_lines = _get_tree_size_at_commit(repo, commit)
        
        # Only main.py should be counted (1 line)
        # .git directory contents should NOT be in the tree
        # (git doesn't store .git in the tree, but this test confirms behavior)
        assert tree_lines == 1
    
    def test_nested_code_files_counted(self, tmp_path):
        """Verify code files in nested directories are counted."""
        from analytics.pipeline.phases.extract import _get_tree_size_at_commit
        
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()
        
        # Create nested structure
        deep_dir = repo_path / "src" / "components" / "utils"
        deep_dir.mkdir(parents=True)
        (deep_dir / "helper.py").write_text("def help():\n    pass\n")  # 2 lines
        
        # Root file
        (repo_path / "main.py").write_text("import src\n")  # 1 line
        
        # Create repo
        repo = pygit2.init_repository(str(repo_path), bare=False)
        config = repo.config
        config["user.name"] = "Test"
        config["user.email"] = "test@test.com"
        
        index = repo.index
        index.add_all()
        index.write()
        tree = index.write_tree()
        
        sig = pygit2.Signature("Test", "test@test.com")
        repo.create_commit("HEAD", sig, sig, "Initial", tree, [])
        
        commit = repo.head.peel(pygit2.Commit)
        tree_bytes, tree_lines = _get_tree_size_at_commit(repo, commit)
        
        # Both files should be counted: main.py (1) + helper.py (2) = 3 lines
        assert tree_lines == 3


class TestTreeWalkConsistencyWithInspector:
    """
    Test that tree walk produces similar results to inspector.
    
    These tests verify the core filtering logic matches.
    """
    
    def test_markdown_files_excluded(self, tmp_path):
        """Markdown files should NOT be counted (matching inspector)."""
        from analytics.pipeline.phases.extract import _get_tree_size_at_commit
        
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()
        
        # Only markdown files
        (repo_path / "README.md").write_text("# Title\n\nContent\n")
        (repo_path / "CONTRIBUTING.md").write_text("# How to contribute\n")
        
        # Create repo
        repo = pygit2.init_repository(str(repo_path), bare=False)
        config = repo.config
        config["user.name"] = "Test"
        config["user.email"] = "test@test.com"
        
        index = repo.index
        index.add_all()
        index.write()
        tree = index.write_tree()
        
        sig = pygit2.Signature("Test", "test@test.com")
        repo.create_commit("HEAD", sig, sig, "Initial", tree, [])
        
        commit = repo.head.peel(pygit2.Commit)
        tree_bytes, tree_lines = _get_tree_size_at_commit(repo, commit)
        
        # No code files, so should be 0
        assert tree_lines == 0
        assert tree_bytes == 0
    
    def test_json_config_files_excluded(self, tmp_path):
        """JSON/YAML config files should NOT be counted."""
        from analytics.pipeline.phases.extract import _get_tree_size_at_commit
        
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()
        
        # Only config files
        (repo_path / "package.json").write_text('{"name": "test"}\n')
        (repo_path / "tsconfig.json").write_text('{"compilerOptions": {}}\n')
        (repo_path / "config.yaml").write_text("key: value\n")
        
        # Create repo
        repo = pygit2.init_repository(str(repo_path), bare=False)
        config = repo.config
        config["user.name"] = "Test"
        config["user.email"] = "test@test.com"
        
        index = repo.index
        index.add_all()
        index.write()
        tree = index.write_tree()
        
        sig = pygit2.Signature("Test", "test@test.com")
        repo.create_commit("HEAD", sig, sig, "Initial", tree, [])
        
        commit = repo.head.peel(pygit2.Commit)
        tree_bytes, tree_lines = _get_tree_size_at_commit(repo, commit)
        
        # No code files, so should be 0
        assert tree_lines == 0
        assert tree_bytes == 0

