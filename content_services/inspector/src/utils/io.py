from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


def get_prompt_template(f: Path | str) -> str:
    p = Path(f)
    with p.open("r") as pt:
        return pt.read()


def download_source_file(
    s3_client: any,
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
    s3_client: any,
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
