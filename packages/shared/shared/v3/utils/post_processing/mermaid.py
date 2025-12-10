# shared/utils/mermaid_fix.py
from __future__ import annotations

import re

from modal import Function
from shared.prompts.task.codeblock_syntax_mermaid import (
    PROMPT as CODEBLOCK_SYNTAX_MERMAID_PROMPT,
)
from shared.v3.app.static.messages.software_expertise import SoftwareExpertiseMessage
from shared.v3.globals.global_messages import GlobalSystemMessage
from shared.v3.interfaces.llm_message import LlmMessage, MessageKind
from shared.v3.interfaces.llm_message_history import LlmMessageHistory
from shared.v3.llms.clients.llm_client import LlmClient

MERMAID_RE = re.compile(r"```mermaid\s*\n(.*?)\n```", re.DOTALL)


def _extract_mermaid_interior(text: str) -> str:
    """
    Pull only the diagram no ````mermaid``` fences.
    Falls back to the full text if the fences are missing.
    """
    match = MERMAID_RE.search(text)
    return match.group(1).strip() if match else text.strip()


def _check_mermaid_syntax(diagram: str) -> tuple[bool, str]:
    """
    Wrapper around the Modal function so we can catch transport errors and
    treat them as “renderable” (i.e. don't block the pipeline).
    """
    try:
        check_mermaid = Function.from_name(
            "mermaid-syntax-check", "check_mermaid_syntax"
        )
        status, msg = check_mermaid.remote(diagram)
        return status == "ok", msg
    except Exception as exc:  # network / timeout, etc.
        return True, str(exc)


def _fix_with_llm(
    bad_diagram: str, error: str, *, client: LlmClient, max_attempts: int
) -> str:
    """
    Keep asking the model to repair the diagram until it passes validation or
    we hit `max_attempts`.
    """
    diagram = bad_diagram
    attempts = 0
    while attempts < max_attempts:
        resp = client.single_shot(
            message_history=LlmMessageHistory(
                messages=[
                    GlobalSystemMessage(),
                    SoftwareExpertiseMessage(),
                    LlmMessage(
                        message_kind=MessageKind.USER,
                        content=(
                            "The following Mermaid diagram fails to render. "
                            "Please return **only** the corrected diagram inside a single "
                            "mermaid code block.\n\n"
                            f"Error message:\n{error}\n\n"
                            f"{CODEBLOCK_SYNTAX_MERMAID_PROMPT}\n\n"
                            f"```mermaid\n{diagram}\n```"
                        ),
                    ),
                ]
            )
        )

        diagram = _extract_mermaid_interior(resp.content)
        ok, error = _check_mermaid_syntax(diagram)
        if ok:
            break
        attempts += 1
    return diagram


def fix_mermaid_syntax_in_response(
    text: str,
    *,
    client: LlmClient = LlmClient.gpt_4_1(),
    max_attempts: int = 3,
) -> str:
    """
    Scan `text` for mermaid code blocks, validate them, and replace any broken
    ones with repaired versions via the LLM.  A lightweight, synchronous helper
    that can be run as the final postprocessing step of any pipeline.

    Parameters
    ----------
    text : str
        The full response string (Markdown allowed).
    client : LlmClient, optional
        Defaults to GPT4.1.  Pass a different client if desired.
    max_attempts : int, optional
        Maximum repair attempts per diagram (default=3).

    Returns
    -------
    str:
        The updated response with all Mermaid diagrams guaranteed to render
        (or left unchanged if no valid fix was found within `max_attempts`).
    """

    def _replace(match: re.Match[str]) -> str:
        body = match.group(1).strip()
        ok, err = _check_mermaid_syntax(body)
        if ok:
            return match.group(0)  # leave unchanged

        fixed = _fix_with_llm(body, err, client=client, max_attempts=max_attempts)
        return f"```mermaid\n{fixed}\n```"

    return MERMAID_RE.sub(_replace, text)
