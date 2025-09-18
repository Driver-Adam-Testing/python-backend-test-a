import contextlib
import pickle
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any


def get_prompt_template(f: Path | str) -> str:
    p = Path(f)
    with p.open("r") as pt:
        return pt.read()


def download_source_file(
    s3_client: Any,
    bucket_name: str,
    primary_asset_id: str,
    version_id: str,
    node_rel_path: str,
    download_root: Path,
) -> Path:
    s3_key = f"{primary_asset_id}/{version_id}/{node_rel_path}"
    local_download_path = download_root / node_rel_path
    local_download_path.parent.mkdir(parents=True, exist_ok=True)

    s3_client.download_file(bucket_name, s3_key, str(local_download_path))
    return local_download_path


def download_all_source_files_in_parallel(
    s3_client: Any,
    bucket_name: str,
    primary_asset_id: str,
    version_id: str,
    node_rel_paths: list[str],
    download_root: Path,
    max_workers: int,
) -> list[Path]:
    paths: list[Path] = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for node_path in node_rel_paths:
            futures.append(
                executor.submit(
                    download_source_file,
                    s3_client,
                    bucket_name,
                    primary_asset_id,
                    version_id,
                    node_path,
                    download_root,
                )
            )

        for future in as_completed(futures):
            # Any exception raised within download_source_file will be re-raised here.
            paths.append(future.result())

    return paths


def _get_symbol_table_s3_key(version_id: str) -> str:
    return f"{version_id}_symbol_table.pkl"


def _get_symbol_table_cache_path(version_id: str) -> Path:
    return Path(f"/tmp/{version_id}_symbol_table.pkl")


def upload_symbol_table_to_s3(
    symbol_table: dict[str, Any],
    s3_client: Any,
    bucket_name: str,
    version_id: str,
) -> str:
    import os
    import tempfile

    s3_key = _get_symbol_table_s3_key(version_id)

    fd, temp_path = tempfile.mkstemp(suffix=".pkl")
    try:
        with os.fdopen(fd, "wb") as temp_file:
            pickle.dump(symbol_table, temp_file)

        s3_client.upload_file(temp_path, bucket_name, s3_key)
    except Exception as e:
        Path(temp_path).unlink(missing_ok=True)
        raise RuntimeError("Failed to upload symbol table to S3") from e
    finally:
        Path(temp_path).unlink(missing_ok=True)

    return s3_key


def download_symbol_table_from_s3_with_cache(
    s3_client: Any,
    bucket_name: str,
    version_id: str,
) -> dict[str, Any]:
    cache_path = _get_symbol_table_cache_path(version_id)
    try:
        with open(cache_path, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        pass
    except Exception:
        cache_path.unlink(missing_ok=True)

    s3_key = _get_symbol_table_s3_key(version_id)
    try:
        s3_client.download_file(bucket_name, s3_key, str(cache_path))
    except Exception as e:
        raise RuntimeError("Failed to download symbol table from S3") from e

    with open(cache_path, "rb") as f:
        return pickle.load(f)


def cleanup_symbol_table_cache(version_id: str) -> None:
    cache_path = _get_symbol_table_cache_path(version_id)
    with contextlib.suppress(Exception):
        cache_path.unlink(missing_ok=True)
