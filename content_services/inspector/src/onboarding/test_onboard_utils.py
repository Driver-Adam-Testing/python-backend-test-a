import zipfile
from pathlib import Path

from onboard_utils import unpack_archive


def test_unpack_archive_single_file_no_root(tmp_path: Path) -> None:
    """Test unpacking a zip with a single file and no root directory"""
    zip_path: Path = tmp_path / "single_file.zip"
    extraction_path: Path = tmp_path / "extracted"
    extraction_path.mkdir()

    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("lonely_file.txt", "hello")

    result_path: Path = unpack_archive(zip_path, extraction_path)

    assert result_path.exists()
    assert result_path.name == "single_file"
    assert (result_path / "lonely_file.txt").exists()


def test_unpack_archive_multiple_root_dirs(tmp_path: Path) -> None:
    """Test unpacking a zip with multiple top-level directories"""
    zip_path: Path = tmp_path / "multi_root_dirs.zip"
    extraction_path: Path = tmp_path / "extracted"
    extraction_path.mkdir()

    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.mkdir("dir1/")
        zf.mkdir("dir2/")
        zf.writestr("dir1/file1.txt", "data1")
        zf.writestr("dir2/file2.txt", "data2")

    result_path: Path = unpack_archive(zip_path, extraction_path)

    assert result_path.exists()
    assert result_path.name == "multi_root_dirs"
    assert (result_path / "dir1/file1.txt").exists()
    assert (result_path / "dir2/file2.txt").exists()


def test_unpack_archive_mixed_files_and_dirs(tmp_path: Path) -> None:
    """Test unpacking a zip with a mix of files and directories at the root"""
    zip_path: Path = tmp_path / "mixed.zip"
    extraction_path: Path = tmp_path / "extracted"
    extraction_path.mkdir()

    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.mkdir("dir_a/")
        zf.writestr("random_file.txt", "hello")
        zf.writestr("dir_a/inside_file.txt", "world")

    result_path: Path = unpack_archive(zip_path, extraction_path)

    assert result_path.exists()
    assert result_path.name == "mixed"
    assert (result_path / "random_file.txt").exists()
    assert (result_path / "dir_a/inside_file.txt").exists()


def test_unpack_archive_single_root_dir_with_subdirs(tmp_path: Path) -> None:
    """Test unpacking a zip with a single root directory containing multiple files and subdirectories"""
    zip_path: Path = tmp_path / "different_name.zip"
    extraction_path: Path = tmp_path / "extracted"
    extraction_path.mkdir()

    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.mkdir("real_root/")
        zf.mkdir("real_root/subdir/")
        zf.writestr("real_root/file1.txt", "data1")
        zf.writestr("real_root/subdir/file2.txt", "data2")

    result_path: Path = unpack_archive(zip_path, extraction_path)

    assert result_path.exists()
    assert result_path.name == "real_root"
    assert (result_path / "file1.txt").exists()
    assert (result_path / "subdir/file2.txt").exists()


def test_unpack_archive_single_root_dir_same_as_zip(tmp_path: Path) -> None:
    """Test unpacking a zip where the top-level directory matches the zip filename"""
    zip_stem = "project_folder"
    zip_path: Path = tmp_path / f"{zip_stem}.zip"
    extraction_path: Path = tmp_path / "extracted"
    extraction_path.mkdir()

    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.mkdir(f"{zip_stem}/")
        zf.mkdir(f"{zip_stem}/subdir/")
        zf.writestr(f"{zip_stem}/file1.txt", "file1 content")
        zf.writestr(f"{zip_stem}/subdir/file2.txt", "file2 content")

    result_path: Path = unpack_archive(zip_path, extraction_path)

    assert result_path.exists()
    assert result_path.name == zip_stem
    assert (result_path / "file1.txt").exists()
    assert (result_path / "subdir/file2.txt").exists()


def test_unpack_archive_with_override_matching_root(tmp_path: Path) -> None:
    """Test unpacking when zip name matches the root dir, using override_codebase_name"""
    zip_stem = "project_folder"
    override_name = "overridden_folder"
    zip_path: Path = tmp_path / f"{zip_stem}.zip"
    extraction_path: Path = tmp_path / "extracted"
    extraction_path.mkdir()

    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.mkdir(f"{zip_stem}/")
        zf.writestr(f"{zip_stem}/file1.txt", "content1")

    result_path: Path = unpack_archive(
        zip_path, extraction_path, override_codebase_name=override_name
    )

    assert result_path.exists()
    assert result_path.name == override_name
    assert (result_path / "file1.txt").exists()


def test_unpack_archive_with_override_nonmatching_root(tmp_path: Path) -> None:
    """Test unpacking when zip name differs from root dir, using override_codebase_name"""
    zip_path: Path = tmp_path / "random_name.zip"
    override_name = "custom_folder_name"
    extraction_path: Path = tmp_path / "extracted"
    extraction_path.mkdir()

    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.mkdir("real_root/")
        zf.writestr("real_root/file_inside.txt", "some data")

    result_path: Path = unpack_archive(
        zip_path, extraction_path, override_codebase_name=override_name
    )

    assert result_path.exists()
    assert result_path.name == override_name
    assert (result_path / "file_inside.txt").exists()
