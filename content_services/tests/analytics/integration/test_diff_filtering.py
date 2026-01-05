"""
Integration tests for diff filtering.

Verifies that commit metrics only count analyzable code files,
matching the inspector's is_analyzable criteria.

This ensures diff-based metrics (additions, deletions, churn) are
comparable to tree-based metrics (current_sloc).
"""
import pytest
import tempfile
from pathlib import Path

import pygit2

from analytics.pipeline.phases.extract import (
    _extract_commit_data_with_diff,
    _extract_file_changes,
    extract_commits,
)


class TestDiffFiltering:
    """Verify diff metrics only count code files."""
    
    @pytest.fixture
    def repo_with_mixed_changes(self, tmp_path):
        """Create a repo with code and non-code file changes."""
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()
        
        # Initialize git repo
        repo = pygit2.init_repository(str(repo_path), bare=False)
        config = repo.config
        config["user.name"] = "Test"
        config["user.email"] = "test@test.com"
        sig = pygit2.Signature("Test", "test@test.com")
        
        # Initial commit with code file
        (repo_path / "main.py").write_text("def hello():\n    pass\n")
        index = repo.index
        index.add("main.py")
        index.write()
        tree = index.write_tree()
        repo.create_commit("HEAD", sig, sig, "Initial", tree, [])
        
        # Second commit with code AND non-code changes
        (repo_path / "main.py").write_text("def hello():\n    print('hi')\n    pass\n")  # +1 line (code)
        (repo_path / "README.md").write_text("# Hello\n\nThis is docs.\n")  # +3 lines (should NOT count)
        (repo_path / "config.json").write_text('{"key": "value"}\n')  # +1 line (should NOT count)
        
        index.add("main.py")
        index.add("README.md")
        index.add("config.json")
        index.write()
        tree = index.write_tree()
        parent = repo.head.peel(pygit2.Commit)
        repo.create_commit("HEAD", sig, sig, "Add features and docs", tree, [parent.id])
        
        return repo
    
    @pytest.fixture
    def repo_with_yaml_changes(self, tmp_path):
        """Create a repo with code and YAML config changes."""
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()
        
        repo = pygit2.init_repository(str(repo_path), bare=False)
        config = repo.config
        config["user.name"] = "Test"
        config["user.email"] = "test@test.com"
        sig = pygit2.Signature("Test", "test@test.com")
        
        # Initial commit
        (repo_path / "app.py").write_text("print('hello')\n")
        index = repo.index
        index.add("app.py")
        index.write()
        tree = index.write_tree()
        repo.create_commit("HEAD", sig, sig, "Initial", tree, [])
        
        # Add YAML file (should not be counted)
        (repo_path / ".github").mkdir(parents=True)
        (repo_path / ".github" / "workflows").mkdir()
        (repo_path / ".github" / "workflows" / "ci.yml").write_text("name: CI\njobs:\n  test:\n    runs-on: ubuntu-latest\n")
        
        index.add(".github/workflows/ci.yml")
        index.write()
        tree = index.write_tree()
        parent = repo.head.peel(pygit2.Commit)
        repo.create_commit("HEAD", sig, sig, "Add CI config", tree, [parent.id])
        
        return repo
    
    @pytest.fixture
    def repo_with_binary_extension(self, tmp_path):
        """Create a repo with code and binary-extension file changes."""
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()
        
        repo = pygit2.init_repository(str(repo_path), bare=False)
        config = repo.config
        config["user.name"] = "Test"
        config["user.email"] = "test@test.com"
        sig = pygit2.Signature("Test", "test@test.com")
        
        # Initial commit
        (repo_path / "lib.c").write_text("int main() { return 0; }\n")
        index = repo.index
        index.add("lib.c")
        index.write()
        tree = index.write_tree()
        repo.create_commit("HEAD", sig, sig, "Initial", tree, [])
        
        # Add binary-extension files (should not be counted)
        (repo_path / "build").mkdir()
        (repo_path / "build" / "output.o").write_bytes(b"\x7fELF...")
        (repo_path / "build" / "lib.so").write_bytes(b"\x7fELF...")
        
        index.add("build/output.o")
        index.add("build/lib.so")
        index.write()
        tree = index.write_tree()
        parent = repo.head.peel(pygit2.Commit)
        repo.create_commit("HEAD", sig, sig, "Add build artifacts", tree, [parent.id])
        
        return repo
    
    def test_commit_only_counts_code_lines(self, repo_with_mixed_changes):
        """Verify additions_lines only counts code files."""
        repo = repo_with_mixed_changes
        
        result = extract_commits(
            repo=repo,
            codebase_id="test-123",
            branch_names=None,  # Auto-detect branches
            include_patches=True,
        )
        
        assert result.success
        
        # Find the second commit (the one with mixed changes)
        second_commit = [c for c in result.commits if "Add features" in c['message']][0]
        
        # All files are counted now (md, json in languages.yml)
        # 1 line in main.py + 3 lines in README.md + 1 line in config.json = 5 lines
        assert second_commit['additions_lines'] == 5
        assert second_commit['files_changed'] == 3
    
    def test_yaml_files_are_counted(self, repo_with_yaml_changes):
        """Verify YAML files are counted (they're in languages.yml)."""
        repo = repo_with_yaml_changes
        
        result = extract_commits(
            repo=repo,
            codebase_id="test-123",
            branch_names=None,  # Auto-detect branches
            include_patches=True,
        )
        
        assert result.success
        
        # Find the CI commit
        ci_commit = [c for c in result.commits if "Add CI config" in c['message']][0]
        
        # YAML files ARE in languages.yml, so they're counted
        assert ci_commit['additions_lines'] == 4
        assert ci_commit['files_changed'] == 1
    
    def test_binary_extensions_not_counted(self, repo_with_binary_extension):
        """Verify files with binary extensions are excluded."""
        repo = repo_with_binary_extension
        
        result = extract_commits(
            repo=repo,
            codebase_id="test-123",
            branch_names=None,  # Auto-detect branches
            include_patches=True,
        )
        
        assert result.success
        
        # Find the build commit
        build_commit = [c for c in result.commits if "Add build artifacts" in c['message']][0]
        
        # Should have 0 additions (.o and .so are blacklisted extensions)
        assert build_commit['additions_lines'] == 0
        assert build_commit['files_changed'] == 0


class TestFileChangesFiltering:
    """Verify file changes extraction filters non-code files."""
    
    @pytest.fixture
    def repo_with_mixed_files(self, tmp_path):
        """Create a repo with various file types."""
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()
        
        repo = pygit2.init_repository(str(repo_path), bare=False)
        config = repo.config
        config["user.name"] = "Test"
        config["user.email"] = "test@test.com"
        sig = pygit2.Signature("Test", "test@test.com")
        
        # Initial commit (empty)
        tree_builder = repo.TreeBuilder()
        tree = tree_builder.write()
        repo.create_commit("HEAD", sig, sig, "Initial", tree, [])
        
        # Add multiple file types
        (repo_path / "src").mkdir()
        (repo_path / "src" / "main.py").write_text("print('hello')\n")
        (repo_path / "src" / "util.js").write_text("console.log('hi');\n")
        (repo_path / "README.md").write_text("# Project\n")
        (repo_path / "package.json").write_text('{"name": "test"}\n')
        (repo_path / "config.yaml").write_text("key: value\n")
        
        index = repo.index
        index.add("src/main.py")
        index.add("src/util.js")
        index.add("README.md")
        index.add("package.json")
        index.add("config.yaml")
        index.write()
        tree = index.write_tree()
        parent = repo.head.peel(pygit2.Commit)
        repo.create_commit("HEAD", sig, sig, "Add files", tree, [parent.id])
        
        return repo
    
    def test_file_changes_only_include_code(self, repo_with_mixed_files):
        """Verify file changes only include analyzable code files."""
        repo = repo_with_mixed_files
        
        result = extract_commits(
            repo=repo,
            codebase_id="test-123",
            branch_names=None,  # Auto-detect branches
            include_patches=True,
            include_file_changes=True,
        )
        
        assert result.success
        
        # Find the "Add files" commit
        add_commit = [c for c in result.commits if "Add files" in c['message']][0]
        commit_sha = add_commit['commit_sha']
        
        # Get file changes for this commit
        commit_file_changes = [fc for fc in result.file_changes if fc['commit_sha'] == commit_sha]
        
        # All text files are now counted (md, json, yaml in languages.yml)
        assert len(commit_file_changes) == 5
        
        file_paths = {fc['file_path'] for fc in commit_file_changes}
        assert 'src/main.py' in file_paths
        assert 'src/util.js' in file_paths
        assert 'README.md' in file_paths
        assert 'package.json' in file_paths
        assert 'config.yaml' in file_paths


class TestDriverDocsFiltering:
    """Verify driver_docs directory is filtered out."""
    
    @pytest.fixture
    def repo_with_driver_docs(self, tmp_path):
        """Create a repo with driver_docs changes."""
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()
        
        repo = pygit2.init_repository(str(repo_path), bare=False)
        config = repo.config
        config["user.name"] = "Test"
        config["user.email"] = "test@test.com"
        sig = pygit2.Signature("Test", "test@test.com")
        
        # Initial commit
        (repo_path / "main.py").write_text("print('hello')\n")
        index = repo.index
        index.add("main.py")
        index.write()
        tree = index.write_tree()
        repo.create_commit("HEAD", sig, sig, "Initial", tree, [])
        
        # Add driver_docs (should be excluded)
        (repo_path / "driver_docs").mkdir()
        (repo_path / "driver_docs" / "overview.md").write_text("# Overview\n")
        
        index.add("driver_docs/overview.md")
        index.write()
        tree = index.write_tree()
        parent = repo.head.peel(pygit2.Commit)
        repo.create_commit("HEAD", sig, sig, "Add driver docs", tree, [parent.id])
        
        return repo
    
    def test_driver_docs_excluded(self, repo_with_driver_docs):
        """Verify driver_docs directory is not counted."""
        repo = repo_with_driver_docs
        
        result = extract_commits(
            repo=repo,
            codebase_id="test-123",
            branch_names=None,  # Auto-detect branches
            include_patches=True,
        )
        
        assert result.success
        
        # Find the driver docs commit
        docs_commit = [c for c in result.commits if "Add driver docs" in c['message']][0]
        
        # Should have 0 additions (driver_docs is blacklisted)
        assert docs_commit['additions_lines'] == 0
        assert docs_commit['files_changed'] == 0

