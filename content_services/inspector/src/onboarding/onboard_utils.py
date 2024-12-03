import hashlib
import os
import re
import zipfile
from functools import cache
from pathlib import Path
from urllib.parse import urlparse
from uuid import UUID

import requests
from boto3 import resource
from botocore.client import ClientError
from database.models_v1 import (
    Codebase,
    DerivedContent,
    DerivedContentType,
    Enum_Codebase_Status,
    Enum_Derived_Content_Status,
)
from sqlmodel import Session, select


# TODO dedup; already exists for inspector
@cache
def get_source_content_type_uuid(content_type_name: str) -> UUID:
    from database.db import engine

    sct_uuid = None
    with Session(engine) as session:
        sel_statement = select(DerivedContentType).where(
            DerivedContentType.type_name == content_type_name
        )
        res_sct = session.exec(sel_statement).first()
        if res_sct:
            sct_uuid = res_sct.id
    return sct_uuid


def set_codebase_status(codebase_id: UUID, status: Enum_Derived_Content_Status) -> None:
    from database.db import engine
    from sqlmodel import Session, select

    with Session(engine) as session, session.begin():
        codebase = session.get(Codebase, codebase_id)
        if codebase:
            codebase.status = Enum_Codebase_Status.processing_complete
            session.add(codebase)
        else:
            raise Exception(f"Codebase with ID: {codebase_id} not found.")

        cb_sc_uuid = get_source_content_type_uuid("codebase")
        sel_statement = select(DerivedContent).where(
            DerivedContent.codebase_id == codebase_id,
            DerivedContent.content_type_id == cb_sc_uuid,
        )
        codebase_dc = session.exec(sel_statement).first()
        if codebase_dc:
            codebase_dc.status = status
            session.add(codebase_dc)
        else:
            raise Exception(
                f"Codebase Source Content with ID: {codebase_id} not found."
            )


def create_base_storage_url(org_id: str) -> str:
    hashed_org_id = hashlib.sha256(org_id.encode()).hexdigest()[:63]
    return f"https://{hashed_org_id}.s3.amazonaws.com"


def create_bucket_if_dne(bucket_name: str) -> None:
    try:
        # TODO: handle this cleanly? AWS_S3_ENDPOINT_URL returns None if DNE, which reverts to
        # default boto3 behavior
        s3_resource = resource("s3", endpoint_url=os.environ.get("AWS_S3_ENDPOINT_URL"))
        s3_resource.meta.client.head_bucket(Bucket=bucket_name)
    except ClientError:
        # Bucket does not exist
        s3_resource.create_bucket(Bucket=bucket_name)
        print(f"Created bucket: {bucket_name}")


def download_file_from_s3(
    bucket_name: str, org_id: str, file_name: str, download_destination: Path
) -> None:
    s3_file_prefix = "codebases"
    s3_resource = resource("s3", endpoint_url=os.environ.get("AWS_S3_ENDPOINT_URL"))
    # TODO: if S3 is reorged, bucket is consistent?
    s3_bucket = s3_resource.Bucket(bucket_name)
    s3_path_to_file = Path(s3_file_prefix) / org_id / file_name
    download_destination = Path(file_name)

    try:
        s3_bucket.download_file(str(s3_path_to_file), download_destination)
    except Exception as e:
        raise e


def download_file_from_presigned_url(
    presigned_url: str, download_destination: Path
) -> None:
    with requests.get(presigned_url, stream=True) as r:
        r.raise_for_status()
        with open(download_destination, "wb") as w_file:
            for chunk in r.iter_content(chunk_size=8192):
                w_file.write(chunk)


def get_root_directories_in_archive(zip_file: zipfile.ZipFile) -> list:
    root_dirs = []
    for zip_node in zip_file.infolist():
        if zip_node.is_dir():
            node_path = Path(zip_node.filename)
            if node_path.parts[0] not in root_dirs:
                root_dirs.append(node_path.parts[0])
    return root_dirs


def unpack_archive(
    archive_path: Path, override_codebase_name: str | None = None
) -> Path:
    # Creating zipfile instance does NOT unpack right away.
    # We can check root dir cases and modify from there BEFORE unpacking
    local_archive = zipfile.ZipFile(archive_path, "r")
    root_dirs = get_root_directories_in_archive(local_archive)
    extracted_path = None
    if len(root_dirs) != 1:
        # Handles both multiple and no roots, extract to an appended root
        extracted_path = Path(
            archive_path.stem
        )  # TODO: this is sensitive if we modify archive name at all
        extracted_path.mkdir(exist_ok=False)  # don't unpack into an existing dir
    local_archive.extractall(path=extracted_path)

    if extracted_path is None:
        extracted_path = Path(root_dirs[0])

    stripped_extracted_path = Path(re.sub(r"/\.[^/.]+$/", "", str(extracted_path)))
    if override_codebase_name:
        stripped_extracted_path = Path(override_codebase_name)

    os.rename(extracted_path, stripped_extracted_path)

    assert stripped_extracted_path.exists()

    return stripped_extracted_path


def upload_file_to_s3(
    bucket_name: str, destination_root: Path, local_path: Path
) -> Path:
    s3_resource = resource("s3", endpoint_url=os.environ.get("AWS_S3_ENDPOINT_URL"))
    # TODO: if S3 is reorged, bucket is consistent?
    s3_bucket = s3_resource.Bucket(bucket_name)
    if local_path.exists():
        s3_destination_path = destination_root / local_path
        s3_bucket.upload_file(local_path, str(s3_destination_path))
    return s3_destination_path


def evaluate_file_size_processable(filepath: Path) -> bool:
    is_proc = True
    file_size = os.path.getsize(filepath)
    min_size = 0
    max_size = 1000000000  # TODO: what's a more sensible default?

    if file_size < min_size or file_size > max_size:
        is_proc = False

    return is_proc


def get_non_ascii_file_encoding(file_bytes: bytes) -> str:
    import chardet

    chunk_size = 2500
    num_chunks = 40
    min_confidence = 0.7
    found_encoding = None

    byte_chunks = [
        file_bytes[i : i + chunk_size] for i in range(0, len(file_bytes), chunk_size)
    ][:num_chunks]
    for chunk in byte_chunks:
        pred_enc = chardet.detect(chunk)
        if (
            pred_enc["encoding"] is not None
            and pred_enc["encoding"] != "ascii"
            and pred_enc["confidence"] > min_confidence
        ):
            try:
                file_bytes.decode(pred_enc["encoding"])
                found_encoding = pred_enc["encoding"]
            except UnicodeDecodeError:
                print(f"Chardet predicted encoding {pred_enc['encoding']} failed")
            break
    return found_encoding


def evaluate_file_binary(filepath: Path) -> bool:
    import chardet

    is_binary = False
    chunk_size = 2500
    min_confidence = 0.7

    # Allow ASCII bytes for tab, new line, carriage return, form feed, vert tab and separators
    disallowed_bytes = [
        b"\x00",
        b"\x01",
        b"\x02",
        b"\x03",
        b"\x04",
        b"\x05",
        b"\x06",
        b"\x07",
        b"\x08",
        b"\x0e",
        b"\x0f",
        b"\x10",
        b"\x11",
        b"\x12",
        b"\x13",
        b"\x14",
        b"\x15",
        b"\x16",
        b"\x17",
        b"\x18",
        b"\x19",
        b"\x1a",
        b"\x1b",
    ]

    with open(filepath, "rb") as r_file:
        file_bytes = r_file.read()

        if any(test_byte in file_bytes for test_byte in disallowed_bytes):
            # If the file contains any of the control code bytes:
            # We have high confidence it is NOT one of the most used 8-bit encodings.
            # Still need to test for UTF-16 (possibly UTF-32 if we want to support)

            # This decodes random garbage as well, but helpful as a backup to chardet
            utf16_decodes = False
            try:
                file_bytes.decode("utf-16")  # Little-endian
                utf16_decodes = True
            except UnicodeDecodeError:
                try:
                    file_bytes.decode("utf-16be")  # Big-endian
                    utf16_decodes = True
                except UnicodeDecodeError:
                    pass

            if utf16_decodes:
                pred_enc = chardet.detect(file_bytes[:chunk_size])

                if (
                    pred_enc["encoding"] in ["UTF-16", "utf-16be"]
                    and pred_enc["confidence"] > min_confidence
                ):
                    is_binary = False
                else:
                    is_binary = True
            else:
                is_binary = True
        else:
            # Lack confidence still as NUL check isn't perfect
            # If file lacks ascii control code bytes, but decodes as utf-8 -> Confident
            utf8_decodes = False
            try:
                file_bytes.decode("utf-8")
                utf8_decodes = True
            except UnicodeDecodeError:
                pass

            if utf8_decodes:
                is_binary = False
            else:
                # Last effort - use chardet
                file_encoding = get_non_ascii_file_encoding(file_bytes)
                is_binary = file_encoding is None

    return is_binary


def evaluate_file_hex(filepath: Path) -> bool:
    hex_perc_threshold = 0.99
    regex_test_str = r"[a-fA-F0-9\n ]"
    is_hex = False
    with open(filepath) as r_file:
        file_str = r_file.read()

        if len(file_str) > 0:
            hex_char_count = len(re.findall(regex_test_str, file_str))
            if hex_char_count / len(file_str) > hex_perc_threshold:
                is_hex = True
    return is_hex


def is_on_blacklist(filepath: Path) -> bool:
    blacklist_dirs = [
        ".git",
    ]
    blacklist_file_exts = [
        ".svg",
    ]
    is_blacklisted = False

    if any(dir in filepath.parts for dir in blacklist_dirs):
        is_blacklisted = True

    if filepath.is_file() and filepath.suffix in blacklist_file_exts:
        is_blacklisted = True

    return is_blacklisted


def reencode_file(filepath: Path) -> None:
    is_utf8 = False
    decoded_str = None

    with open(filepath, "rb") as r_file:
        file_bytes = r_file.read()

        try:
            file_bytes.decode("utf-8")
            is_utf8 = True
        except UnicodeDecodeError:
            is_utf8 = False

        if not is_utf8:
            file_encoding = get_non_ascii_file_encoding(file_bytes)
            if file_encoding:
                try:
                    decoded_str = file_bytes.decode(file_encoding)
                except UnicodeDecodeError as e:
                    print(
                        f"Error: {e} decoding {filepath} \
                          with predicted encoding: {file_encoding}"
                    )
                    # TODO: force UTF-8 encoding with ignored characters?
            else:
                print(f"Chardet returned None for {filepath}")

    if decoded_str is not None:
        with open(filepath, "w", encoding="utf-8") as w_file:
            w_file.write(decoded_str)
        print(f"Updated {filepath} to UTF-8")


# def analyze_text_file(filepath: Path) -> dict:
#     is_hex = evaluate_file_hex(filepath)
#     return {
#         "size": os.path.getsize(filepath),
#         "sloc": sum(1 for _ in open(filepath)),
#         "extension": filepath.suffix,
#         "is_binary": False,
#         "is_hex": is_hex,
#     }


def analyze_text_file(filepath: Path) -> dict:
    is_hex = evaluate_file_hex(filepath)
    with open(filepath) as file:
        sloc = sum(
            1 for line in file if line.strip()
        )  # TODO is this correct? We count whitespace lines as SLOC?
    return {
        "size": os.path.getsize(filepath),
        "sloc": sloc,
        "extension": filepath.suffix,
        "is_binary": False,
        "is_hex": is_hex,
    }


def analyze_binary_file(filepath: Path) -> dict:
    return {
        "size": os.path.getsize(filepath),
        "sloc": 0,
        "extension": filepath.suffix,
        "is_binary": True,
        "is_hex": False,
    }


def run_file_stats_and_reencode(
    local_path: Path,
) -> dict:
    # Evaluate file-processability before reencoding
    # due to file encoding nastiness w/ binary files
    file_size_processable = evaluate_file_size_processable(local_path)
    is_binary = evaluate_file_binary(local_path)
    is_blacklisted = is_on_blacklist(local_path)

    file_stats = {}

    if not is_binary:
        reencode_file(local_path)
        # TODO use concrete type for the stats data structure since we need to mirror it in the API. Currently fraile to changes
        file_stats = analyze_text_file(local_path)

        default_process_state = False
        if not file_stats["is_hex"] and file_size_processable and not is_blacklisted:
            default_process_state = True
        file_stats["is_analyzable"] = default_process_state
    else:
        file_stats = analyze_binary_file(local_path)
        file_stats["is_analyzable"] = False
    file_stats["is_blacklisted"] = is_blacklisted

    return file_stats


# def run_tree(directory: Path, depth: int = 2) -> str:
#     result = subprocess.run(
#         ["tree", str(directory), "-L", str(depth)],
#         stdout=subprocess.PIPE,
#         stderr=subprocess.PIPE,
#         text=True,
#     )
#     return result.stdout if result.returncode == 0 else result.stderr


def download_repo_zip(url: str, commit_sha: str) -> tuple[str, Path]:
    parsed_url = urlparse(url)
    path_parts = parsed_url.path.strip("/").split("/")

    if len(path_parts) < 2:
        raise ValueError("URL must be in the format 'https://github.com/owner/repo'")

    owner, repo = path_parts[:2]
    download_url = f"https://github.com/{owner}/{repo}/archive/{commit_sha}.zip"
    dest_path = Path("/tmp") / f"{commit_sha}.zip"

    response = requests.get(download_url, stream=True)
    response.raise_for_status()

    with dest_path.open("wb") as file:
        for chunk in response.iter_content(chunk_size=8192):
            file.write(chunk)

    return repo, dest_path
