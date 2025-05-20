import subprocess
from pathlib import Path

from pydantic import BaseModel

from .dag import Node


class InsufficientBalanceError(Exception):
    pass


class CodeDiffParams(BaseModel):
    codebase_name: str
    version_id: str
    primary_asset_id: str
    org_id: str
    previous_download_root: Path
    download_root: Path
    changed_nodes: list[Node]


def git_diff_size_bytes_per_file(file_a: Path, file_b: Path) -> int:
    file_a_exists = file_a.is_file()
    file_b_exists = file_b.is_file()

    # If both files exist, run git diff
    if file_a_exists and file_b_exists:
        result = subprocess.run(
            ["git", "diff", "--no-index", str(file_a), str(file_b)],
            capture_output=True,
            text=True,
        )

        lines_changed = result.stdout.strip().splitlines()
        file_diff_bytes = 0
        for split_line in lines_changed:
            line = (split_line + "\n").encode("utf-8").decode("utf-8")
            if line.startswith(("+++", "---", "@@")):  # skip these lines
                continue
            if line.startswith("+"):
                file_diff_bytes += len(line[1:])
            elif line.startswith("-"):
                file_diff_bytes -= len(line[1:])
        return abs(file_diff_bytes)

    # If file_a doesn't exist but file_b exists, it's a new file
    elif not file_a_exists and file_b_exists:
        return abs(len(file_b.read_bytes()))

    # If file_b doesn't exist but file_a exists, it's a deleted file
    elif file_a_exists and not file_b_exists:
        return abs(len(file_a.read_bytes()))
    else:
        raise FileNotFoundError(f"Neither file '{file_a!s}' nor '{file_b!s}' exists.")


def compute_and_log_code_diff_size_in_bytes(
    code_diff_params: CodeDiffParams,
) -> None:
    from utils.db import get_usage_balance_in_bytes

    codebase_name = code_diff_params.codebase_name
    version_id = code_diff_params.version_id
    primary_asset_id = code_diff_params.primary_asset_id
    org_id = code_diff_params.org_id
    previous_download_root = code_diff_params.previous_download_root
    download_root = code_diff_params.download_root
    changed_nodes = code_diff_params.changed_nodes

    diff_size_in_bytes = 0
    for node in changed_nodes:
        previous_file_version_path = str(previous_download_root / node.root_rel_path)
        current_file_version_path = str(download_root / node.root_rel_path)

        file_diff_size_in_bytes = git_diff_size_bytes_per_file(
            Path(previous_file_version_path), Path(current_file_version_path)
        )
        print(f"Diff size in bytes: {file_diff_size_in_bytes} for {node.root_rel_path}")
        diff_size_in_bytes += file_diff_size_in_bytes
    print(f"Diff size in bytes: {diff_size_in_bytes} for version {version_id}")

    current_balance_in_bytes = get_usage_balance_in_bytes(org_id)
    if current_balance_in_bytes < diff_size_in_bytes:
        msg = f"Insufficient balance for org {org_id} to process codebase {codebase_name}. {diff_size_in_bytes} bytes needed to process updates."
        print(msg)
        raise InsufficientBalanceError(msg)

    print("Logging code diff usage...")
    log_code_diff_usage(
        content_id=str(primary_asset_id),
        content_name=codebase_name,
        version_id=version_id,
        organization_id=org_id,
        diff_size_in_bytes=diff_size_in_bytes,
    )


def log_code_diff_usage(
    content_id: str,
    content_name: str,
    version_id: str,
    organization_id: str,
    diff_size_in_bytes: int,
) -> None:
    from datetime import UTC, datetime

    from database.models_v1 import UsageEventType
    from shared.interfaces.usage.event_metadata import (
        UsageEventMetadata,
        UsageMetric,
        UsageSessionMetadata,
    )
    from shared.usage.llm_session import LLMUsageSession
    from shared.usage.utils import bytes_to_sloc

    session_meta = UsageSessionMetadata(
        content_type="codebase",
        content_id=content_id,
        content_name=content_name,
        version_id=version_id,
    )
    with LLMUsageSession(organization_id, "SYSTEM", session_meta) as llm_session:
        usage_metric = UsageMetric(
            session_id=llm_session.session_id,
            organization_id=organization_id,
            user_id="SYSTEM",
            event_source="inspect_db",
            bytes_in=-diff_size_in_bytes,
            bytes_out=0,
            tokens_in=0,
            tokens_out=0,
            timestamp=datetime.now(tz=UTC),
            event_type=UsageEventType.INSPECTOR_CODE_DIFF_USAGE_DEBIT,
            event_metadata=UsageEventMetadata(
                model="None",
                provider="None",
                input={},
                output="",
                sloc=bytes_to_sloc(diff_size_in_bytes),
            ),
        )
        llm_session.commit_event_now(usage_metric)
