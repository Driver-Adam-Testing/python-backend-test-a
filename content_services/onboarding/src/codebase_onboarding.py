import os
import zipfile
from pathlib import Path
import re
from sqlmodel import Session, select
from dataclasses import dataclass, asdict
from uuid import UUID, uuid4
from urllib.parse import urljoin
import re
from functools import cache

import chardet
from boto3 import resource
from botocore.client import ClientError

import modal
from database.models_v1 import Codebase, SourceContent, SourceContentType, Workspace, Enum_Codebase_Status
from database.db import engine

app = modal.App("codebase-onboarding")

# TODO: configuration
# TODO: parallelize

image = (
    modal.Image.debian_slim(python_version="3.12")
    .copy_local_dir('../../driver_db/', remote_path='/driver_db')
    .poetry_install_from_file("pyproject.toml")
)

def create_base_storage_url(org_id: str):
    return f"https://{org_id}.s3.amazonaws.com"

@cache
def get_source_content_type_uuid(content_type_name: str) -> UUID:
    sct_uuid = None
    with Session(engine) as session:
        sel_statement = select(SourceContentType).where(SourceContentType.type_name == content_type_name)
        res_sct = session.exec(sel_statement).first()
        if res_sct:
            sct_uuid = res_sct.id
    return sct_uuid

def create_bucket_if_dne(bucket_name: str) -> None:
    try:
        # TODO: handle this cleanly? AWS_S3_ENDPOINT_URL returns None if DNE, which reverts to 
        # default boto3 behavior
        s3_resource = resource("s3", endpoint_url=os.environ.get("AWS_S3_ENDPOINT_URL"))
        s3_resource.meta.client.head_bucket(Bucket=bucket_name)
    except ClientError:
        # Bucket does not exist
        s3_resource.create_bucket(Bucket=bucket_name)
        print(f'Created bucket: {bucket_name}')

def download_file_from_s3(
    bucket_name: str, 
    org_id: str,
    file_name: str, 
    download_destination: Path
) -> None:
    s3_file_prefix = "codebases"
    s3_resource = resource("s3", endpoint_url=os.environ.get("AWS_S3_ENDPOINT_URL"))
    #TODO: if S3 is reorged, bucket is consistent?
    s3_bucket = s3_resource.Bucket(bucket_name)
    s3_path_to_file = Path(s3_file_prefix) / org_id / file_name
    download_destination = Path(file_name)

    try:
        s3_bucket.download_file(str(s3_path_to_file), download_destination)
    except Exception as e:
        raise(e)

def get_root_directories_in_archive(zip_file: zipfile.ZipFile) -> list:
    root_dirs = []
    for zip_node in zip_file.infolist():
        if zip_node.is_dir():
            node_path = Path(zip_node.filename)
            if node_path.parts[0] not in root_dirs:
                root_dirs.append(node_path.parts[0])
    return root_dirs

def unpack_archive(archive_path: Path) -> Path:
    # Creating zipfile instance does NOT unpack right away.
    # We can check root dir cases and modify from there BEFORE unpacking
    local_archive = zipfile.ZipFile(archive_path, "r")
    root_dirs = get_root_directories_in_archive(local_archive)
    extracted_path = None
    if len(root_dirs) != 1:
        # Handles both multiple and no roots, extract to an appended root
        extracted_path = Path(archive_path.stem) # TODO: this is sensitive if we modify archive name at all
        extracted_path.mkdir(exist_ok=False) # don't unpack into an existing dir
    local_archive.extractall(path=extracted_path)

    if extracted_path is None:
        extracted_path = Path(root_dirs[0])

    stripped_extracted_path = Path(re.sub(r'/\.[^/.]+$/', "", str(extracted_path)))
    os.rename(extracted_path, stripped_extracted_path)

    return stripped_extracted_path

def upload_directory_contents_to_s3(
    bucket_name: str, 
    destination_root: str, 
    local_root_path: Path
) -> None:
    s3_resource = resource("s3", endpoint_url=os.environ.get("AWS_S3_ENDPOINT_URL"))
    #TODO: if S3 is reorged, bucket is consistent?
    s3_bucket = s3_resource.Bucket(bucket_name) 
    if local_root_path.exists():
        for root, dirs, files in os.walk(local_root_path):
            for filename in files:
                local_path = Path(root) / filename
                s3_destination_path = destination_root / local_path
                s3_bucket.upload_file(local_path, str(s3_destination_path))

def upload_file_to_s3(
    bucket_name: str, 
    destination_root: str, 
    local_path: Path
) -> Path:
    s3_resource = resource("s3", endpoint_url=os.environ.get("AWS_S3_ENDPOINT_URL"))
    #TODO: if S3 is reorged, bucket is consistent?
    s3_bucket = s3_resource.Bucket(bucket_name) 
    if local_path.exists():
        s3_destination_path = destination_root / local_path
        s3_bucket.upload_file(local_path, str(s3_destination_path))
    return s3_destination_path

def evaluate_file_size_processable(filepath: Path):
    is_proc = True
    file_size = os.path.getsize(filepath)
    min_size = 10
    max_size = 1000000000 # TODO: what's a more sensible default?

    if file_size < min_size or file_size > max_size:
        is_proc = False

    return is_proc

def evaluate_file_binary(filepath: Path) -> bool:
    is_binary = False
    chunk_size = 2500
    min_confidence = 0.7

    # Allow ASCII bytes for tab, new line, carriage return, form feed, vert tab and separators
    disallowed_bytes = [
        b'\x00', b'\x01', b'\x02', b'\x03', b'\x04', 
        b'\x05', b'\x06', b'\x07', b'\x08', b'\x0E', 
        b'\x0F', b'\x10', b'\x11', b'\x12', b'\x13', 
        b'\x14', b'\x15', b'\x16', b'\x17', b'\x18', 
        b'\x19', b'\x1A', b'\x1B',
        ]

    with open(filepath, 'rb') as r_file:
        file_bytes = r_file.read()

        if any(test_byte in file_bytes for test_byte in disallowed_bytes):
            # If the file contains any of the control code bytes:
            # We have high confidence it is NOT one of the most used 8-bit encodings.
            # Still need to test for UTF-16 (possibly UTF-32 if we want to support)

            # This decodes random garbage as well, but helpful as a backup to chardet
            utf16_decodes = False
            try:
                file_bytes.decode('utf-16') # Little-endian
                utf16_decodes = True
            except UnicodeDecodeError:
                try:
                    file_bytes.decode('utf-16be') # Big-endian
                    utf16_decodes = True
                except UnicodeDecodeError:
                    pass

            if utf16_decodes:
                pred_enc = chardet.detect(file_bytes[:chunk_size])

                if (pred_enc['encoding'] in ['UTF-16', 'utf-16be'] and
                    pred_enc['confidence'] > min_confidence):
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
                file_bytes.decode('utf-8')
                utf8_decodes = True
            except UnicodeDecodeError:
                pass

            if utf8_decodes:
                is_binary = False
            else:
                # Last effort - use chardet
                pred_enc = chardet.detect(file_bytes[:chunk_size])
                if (pred_enc['confidence'] > min_confidence and 
                    pred_enc['encoding'] is not None):
                    try:
                        file_bytes.decode(pred_enc['encoding'])
                        is_binary = False
                    except UnicodeDecodeError:
                        # Chardet's predicted encoding failed, pass on this file
                        is_binary = True
                else:
                    is_binary = True
    
    return is_binary

def evaluate_file_hex(filepath: Path) -> bool:
    hex_perc_threshold = 0.99 
    regex_test_str = r'[a-fA-F0-9\n ]'
    is_hex = False
    with open(filepath, 'r') as r_file:
        file_str = r_file.read()

        if len(file_str) > 0:
            hex_char_count = len(re.findall(regex_test_str, file_str))
            if hex_char_count / len(file_str) > hex_perc_threshold:
                is_hex = True
    return is_hex

def is_on_blacklist(filepath: Path) -> bool:
    blacklist_dirs = ['.git']
    blacklist_file_exts = []
    is_blacklisted = False

    if any(dir in filepath.parts for dir in blacklist_dirs):
        is_blacklisted = True
    
    if filepath.is_file() and filepath.suffix in blacklist_file_exts:
        is_blacklisted = True
    
    return is_blacklisted

def reencode_file(filepath: Path) -> None:
    is_utf8 = False
    chunk_size = 2500
    decoded_str = None

    with open(filepath, 'rb') as r_file:
        file_bytes = r_file.read()

        try:
            file_bytes.decode('utf-8')
            is_utf8 = True
        except UnicodeDecodeError:
            is_utf8 = False
        
        if not is_utf8:
            pred_enc = chardet.detect(file_bytes[:chunk_size])
            if pred_enc['encoding']:
                try:
                    decoded_str = file_bytes.decode(pred_enc['encoding'])
                except UnicodeDecodeError as e:
                    print(f"Error: {e} decoding {filepath} \
                          with predicted encoding: {pred_enc['encoding']}")
                    # TODO: force UTF-8 encoding with ignored characters? 
            else:
                print(f"Chardet returned None for {filepath}")
    
    if decoded_str: 
        with open(filepath, 'w', encoding='utf-8') as w_file:
            w_file.write(decoded_str)
        print(f"Updated {filepath} to UTF-8")

def analyze_text_file(filepath: Path) -> dict:
    is_hex = evaluate_file_hex(filepath)
    return {
        'size': os.path.getsize(filepath),
        'sloc': sum(1 for _ in open(filepath)),
        'extension': filepath.suffix,
        'is_binary': False,
        'is_hex' : is_hex
    }

def analyze_binary_file(filepath: Path) -> dict:
    return {
        'size': os.path.getsize(filepath),
        'sloc': 0,
        'extension': filepath.suffix,
        'is_binary': True,
        'is_hex' : False
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
        file_stats = analyze_text_file(local_path)

        default_process_state = False
        if not file_stats['is_hex'] and file_size_processable and not is_blacklisted:
            default_process_state = True
        file_stats['is_analyzable'] = default_process_state
    else:
        file_stats = analyze_binary_file(local_path)
        file_stats['is_analyzable'] = False
    file_stats['is_blacklisted'] = is_blacklisted

    return file_stats

@app.function(
    image=image,
    mounts=[
        modal.Mount.from_local_python_packages("database"),
        modal.Mount.from_local_dir(
            local_path="../../driver_db/certs/",
            remote_path="/root/data/",
        )
    ],
    secrets=[
        modal.Secret.from_name("aws-inspector-s3"),
        modal.Secret.from_name("db")
    ],
    proxy=modal.Proxy.from_name("pg-proxy"),
    timeout=60*60,
)
def run_codebase_onboarding(
    bucket_name: str, 
    archive_name: str, 
    org_id: str, 
    creator_id: str,
    workspace_id: str
) -> None:
    # Org check
    # TODO: Validate org exists

    download_dest = Path(archive_name)
    download_file_from_s3(bucket_name, org_id, archive_name, download_dest)
    print(f'Downloaded {archive_name} from S3')

    extracted_path = unpack_archive(download_dest)
    print("Unpacked archive to: ", extracted_path)

    all_directories = []
    codebase_stats = {}

    if extracted_path.exists():
        upload_bucket = org_id
        create_bucket_if_dne(upload_bucket)
        codebase_id = uuid4()

        for root, dirs, files in os.walk(extracted_path):
            all_directories.append(root)
            for filename in files:
                local_path = Path(root) / filename

                file_stats = run_file_stats_and_reencode(
                    local_path, 
                )
                codebase_stats[local_path] = file_stats

        s3_dest_root = Path(str(codebase_id)) / "source"
        # TODO: put this in a threadpoolexecutor
        for file_path in codebase_stats.keys():
            if not codebase_stats[file_path]['is_blacklisted']:
                uploaded_dest_path = upload_file_to_s3(upload_bucket, s3_dest_root, file_path)

        with Session(engine) as session:
            with session.begin():
                base_url = create_base_storage_url(org_id)
                final_storage_url = urljoin(base_url, str(codebase_id))
                codebase = Codebase(
                    id=codebase_id,
                    codebase_name=str(extracted_path),
                    creator_id=creator_id,
                    description='',
                    resource_root=f"{str(extracted_path)}/",
                    storage_url=final_storage_url,
                    workspace_id=workspace_id,
                    status=Enum_Codebase_Status.processing
                )
                session.add(codebase)
                # Flush here to confirm that Source Contents created after this will know that the 
                # codebase exists
                session.flush()
                print(f"Created but not commited codebase: {str(extracted_path)}, with ID: {codebase_id}")

                cb_sc_uuid = get_source_content_type_uuid("codebase")
                cb_sc = SourceContent(
                    codebase_id=codebase_id,
                    relative_path=str(extracted_path),
                    source_content_type_id=cb_sc_uuid,
                    workspace_id=workspace_id,
                    analysis_metadata=dict()
                )
                session.add(cb_sc)

                # Add directories source contents
                dir_sc_uuid = get_source_content_type_uuid("codebase-directory")
                for directory in all_directories:
                    if not is_on_blacklist(Path(directory)):
                        # TODO: analysis metadata for directories? 
                        # TODO: this is fragile - consider using DAG logic here 
                        dir_sc = SourceContent(
                            codebase_id=codebase_id,
                            relative_path=directory,
                            source_content_type_id=dir_sc_uuid,
                            workspace_id=workspace_id,
                            analysis_metadata=dict()
                        )
                        session.add(dir_sc)
                        print(f"Created but not commited source content for: {directory}.")

                # Add file source contents
                for file_path in codebase_stats.keys():
                    if not codebase_stats[file_path]['is_blacklisted']:
                        file_sc_type = get_source_content_type_uuid("codebase-file")
                        file_sc = SourceContent(
                            codebase_id=codebase_id,
                            relative_path=str(file_path),
                            source_content_type_id=file_sc_type,
                            workspace_id=workspace_id,
                            analysis_metadata=codebase_stats[file_path]
                        )
                        session.add(file_sc)

                        print(f"Created but not commited source content for: {file_path}. Processable: {codebase_stats[file_path]['is_analyzable']}. Stats: {codebase_stats[file_path]}")

    print("Codebase onboarding complete for codebase id: ", codebase_id)
    return codebase_id

@app.function(
    image=image,
    mounts=[
        modal.Mount.from_local_python_packages("database"),
        modal.Mount.from_local_dir(
            local_path="../../driver_db/certs/",
            remote_path="/root/data/",
        )
    ],
    secrets=[
        modal.Secret.from_name("aws-inspector-s3"),
        modal.Secret.from_name("db")
    ],
    proxy=modal.Proxy.from_name("pg-proxy"),
    timeout=24*60*60
)
def onboard_and_inspect(dropzone_bucket_name:str, archive_name: str, org_id: str, creator_id: str, workspace_id: UUID):
    inspect_db = modal.Function.lookup("inspector-v2", "inspect_db")

    codebase_id = run_codebase_onboarding.remote(dropzone_bucket_name, archive_name, org_id, creator_id, workspace_id)
    print("onboarding complete for codebase: ", codebase_id)
    print("Inspecting...")

    run_id = uuid4()
    inspect_db.remote(codebase_id, run_id)


@app.local_entrypoint()
def main():
    # s3_bucket_name = "modal-dev-inspector-1234442"
    s3_bucket_name = "development-codebase-dropzone"
    s3_prefix = "codebases"
    archive_name = "mtb-example-psoc6-crypto-aes.zip"
    # create_bucket_if_dne(s3_bucket_name)

    # # Upload to bucket if doesn't exist
    # local_path = Path('examples') / archive_name
    # s3_resource = resource("s3", endpoint_url=os.environ["AWS_S3_ENDPOINT_URL"])
    
    # s3_destination_path = Path(s3_prefix) / archive_name 
    # try:
    #     s3_resource.Object(s3_bucket_name, str(s3_destination_path)).load()
    #     print('obj exists')
    # except:
    #     s3_bucket = s3_resource.Bucket(s3_bucket_name) 
    #     s3_bucket.upload_file(local_path, str(s3_destination_path))

    org_id = '6b00f9ade1094692d388c5dc385d7dccc474504aa5778cb5389f732f36ef641'
    creator_id = 'auth0|6650e02b9812cd674f78cf75'
    workspace_id = UUID('2fb6c92d-68cb-4864-a457-8031589e3210')

    # if modal.is_local():
    #     from dotenv import load_dotenv
    #     load_dotenv()
    #     run_codebase_onboarding.local(s3_bucket_name, s3_prefix, archive_name, org_id, creator_id, workspace_id)
    # else:
    onboard_and_inspect.remote(s3_bucket_name, archive_name, org_id, creator_id, workspace_id)