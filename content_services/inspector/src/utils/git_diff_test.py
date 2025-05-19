from pathlib import Path

from .git_diff import git_diff_size_bytes_per_file

TEST_DIR = Path(__file__).resolve().parent / "git_diff_testcases"
FILE_A = TEST_DIR / "file_a.py"
FILE_B = TEST_DIR / "file_b.py"
NO_FILE = TEST_DIR / "no_file.py"  # file does not exist
DELETED_FILE = TEST_DIR / "deleted_file.py"  # deleted file
EMPTY_FILE = TEST_DIR / "empty_file.py"


# class TestGitDiff:
def test_diff_file_a_to_file_b() -> None:
    diff_bytes = git_diff_size_bytes_per_file(FILE_A, FILE_B)
    # file_a has 19 more bytes compared to file_b
    assert diff_bytes == 19


def test_diff_file_b_to_file_a() -> None:
    diff_bytes = git_diff_size_bytes_per_file(FILE_B, FILE_A)
    assert diff_bytes == 19


def test_diff_with_empty_file() -> None:
    diff_bytes = git_diff_size_bytes_per_file(FILE_A, EMPTY_FILE)
    assert diff_bytes == 288


def test_diff_empty_to_file() -> None:
    diff_bytes = git_diff_size_bytes_per_file(EMPTY_FILE, FILE_A)
    assert diff_bytes == 288


def test_diff_same_file() -> None:
    diff_bytes = git_diff_size_bytes_per_file(FILE_A, FILE_A)
    assert diff_bytes == 0


def test_diff_empty_to_empty() -> None:
    diff_bytes = git_diff_size_bytes_per_file(EMPTY_FILE, EMPTY_FILE)
    assert diff_bytes == 0


def test_diff_no_file_to_file() -> None:
    """
    file_a is added, so the diff should be the size of file_a
    """
    diff_bytes = git_diff_size_bytes_per_file(NO_FILE, FILE_A)
    assert diff_bytes == 288


def test_diff_file_to_deleted_file() -> None:
    """
    file_a is deleted, so the diff should be the size of file_a
    """
    diff_bytes = git_diff_size_bytes_per_file(FILE_A, DELETED_FILE)
    assert diff_bytes == 288
