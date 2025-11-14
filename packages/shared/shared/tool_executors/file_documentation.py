from database.db import get_session
from database.models import DerivedContent, VersionNode
from database.models_enums import ContentKind
from pydantic import BaseModel
from sqlmodel import select

from shared.tool_executors.utilities import get_latest_version_for_codebase

from .tool_use_error import ToolUseError


class FileDocumentationPayload(BaseModel):
    content: str
    lines_returned: int
    next_line: int | None
    lines_remaining: int
    next_section: str | None


def _get_long_description(
    org_id: str,
    codebase_name: str,
    path: str,
) -> str:
    with get_session() as db:
        version = get_latest_version_for_codebase(db, org_id, codebase_name)
        if not version:
            raise ToolUseError(
                agent_message=f"No completed documentation found for codebase '{codebase_name}'."
            )

        full_path = f"{codebase_name}/{path.strip('/')}"

        version_node = db.exec(
            select(VersionNode)
            .where(VersionNode.version_id == version.id)
            .where(VersionNode.relative_path == full_path)
        ).first()

        if not version_node:
            raise ToolUseError(
                agent_message=f"File '{path}' not found in codebase '{codebase_name}' documentation. "
            )

        content = db.exec(
            select(DerivedContent)
            .where(DerivedContent.node_id == version_node.node_id)
            .where(DerivedContent.content_kind == ContentKind.LONG_DESCRIPTION)
        ).first()

        if not content or not content.content:
            raise ToolUseError(
                agent_message=f"No documentation available for '{path}' in codebase '{codebase_name}'. "
            )
        return content.content


def _apply_file_doc_pagination(
    markdown_text: str, start_line: int, max_lines: int
) -> FileDocumentationPayload:
    if not markdown_text:
        raise ToolUseError(agent_message="No documentation available for the file.")

    if start_line < 1:
        raise ToolUseError(
            agent_message="Start line must be greater than or equal to 1."
        )

    if max_lines < 0:
        raise ToolUseError(
            agent_message="Max lines must be greater than or equal to 0."
        )

    full_text = markdown_text.split("\n")

    if start_line > len(full_text):
        raise ToolUseError(
            agent_message=f"Start line {start_line} is greater than the number of lines in the file ({len(full_text)})"
        )

    start_idx = start_line - 1

    # return what's left of the file
    if (start_idx + max_lines >= len(full_text)) or max_lines == 0:
        content_lines = full_text[start_idx:]

        return FileDocumentationPayload(
            content="\n".join(content_lines),
            lines_returned=len(content_lines),
            next_line=None,
            lines_remaining=0,
            next_section=None,
        )

    end_idx = start_idx + max_lines - 1
    partial_text = full_text[start_idx : end_idx + 1]

    # we just happened to stop at the end of a section
    if full_text[end_idx + 1].lstrip().startswith("#"):
        return FileDocumentationPayload(
            content="\n".join(partial_text),
            lines_returned=len(partial_text),
            next_line=end_idx + 2,
            lines_remaining=len(full_text) - end_idx - 1,
            next_section=full_text[end_idx + 1].lstrip().lstrip("#").strip(),
        )

    # we landed in the middle or start of a section
    for idx in reversed(range(len(partial_text))):
        if partial_text[idx].lstrip().startswith("#") and idx != 0:
            return FileDocumentationPayload(
                content="\n".join(partial_text[:idx]),
                lines_returned=len(partial_text[:idx]),
                next_line=idx + start_idx + 1,
                lines_remaining=len(full_text) - idx - start_idx,
                next_section=partial_text[idx].lstrip().lstrip("#").strip(),
            )

    # we started in the middle of a section that was too long
    return FileDocumentationPayload(
        content="\n".join(partial_text),
        lines_returned=len(partial_text),
        next_line=end_idx + 2,
        lines_remaining=len(full_text) - end_idx - 1,
        next_section=None,
    )


def get_file_documentation(
    org_id: str,
    codebase_name: str,
    path: str,
    start_line: int,
    max_lines: int,
) -> FileDocumentationPayload:
    markdown_text = _get_long_description(
        org_id=org_id, codebase_name=codebase_name, path=path
    )
    return _apply_file_doc_pagination(
        markdown_text=markdown_text, start_line=start_line, max_lines=max_lines
    )
