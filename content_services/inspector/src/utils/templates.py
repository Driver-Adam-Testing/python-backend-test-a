import logging
import re
from collections.abc import Callable
from enum import IntEnum
from inspect import signature
from pathlib import Path
from typing import Any, Self

from pydantic import BaseModel, ValidationError

from utils.lang_specialization.symbol_common import Lang, ReifiedSymbol, SymbolKind
from utils.models import ChatOpenAI, OutputConfig, OutputConfigKind
from utils.symbol_table.utils import get_fully_qualified_name


def _arity(fn: Callable) -> int:
    return len(signature(fn).parameters)


class S(IntEnum):
    RAW = 0
    SINGLE_PROMPT_TEXT = 1
    SINGLE_PROMPT_JSON = 2
    LLM_COND_TEXT = 3
    LLM_COND_JSON = 4
    FN_COND_TEXT = 5
    FN_COND_JSON = 6
    MULTI_PROMPT_TEXT = 7
    MULTI_PROMPT_JSON = 8
    SINGLE_PROMPT_CHUNK = 9
    MULTI_LLM_COND_JSON = 10
    SINGLE_PROMPT_CHUNK_JSON = 11


class TemplateError(Exception):
    pass


class SectionKind(BaseModel):
    kind: S


class Boolean(BaseModel):
    value: bool

    @classmethod
    def from_llm(
        cls,
        llm: ChatOpenAI,
        code: str,
        system_prompt: str,
        human_prompt: str,
        fallback: bool = True,
    ) -> Self:
        raw_response = llm.generate_response(system_prompt, human_prompt)
        try:
            boolean = cls(value=raw_response)
        except ValidationError as e:
            logging.warn(
                f"Require a boolean value for conditional template section, got {raw_response}: {e}"
            )
            boolean = cls(value=fallback)

        return boolean


class Template(BaseModel):
    template: list[Any]

    def run_with_code(
        self,
        llm: ChatOpenAI,
        root_rel_path: Path,
        code: str,
        language: Lang,
        reified_symbols: list[ReifiedSymbol] | None,
        code_chunks: list[str] | None = None,
        max_num_chunks_to_use: int | None = None,
    ) -> str:
        output = ""
        for tup in self.template:
            tag = SectionKind(kind=tup[0])
            args = tup[1:]
            match tag.kind:
                case S.RAW:
                    (raw_content,) = args
                    output += f"{raw_content}\n"
                case S.SINGLE_PROMPT_TEXT:  # Simple section header, prompt, text output
                    output_cfg = OutputConfig(kind=OutputConfigKind.TEXT)
                    section_title, system_prompt, section_prompt = args
                    user_prompt = f"{section_prompt}\n\nCode:\n\n{code}"
                    content = llm.generate_response(
                        system_prompt=system_prompt,
                        user_prompt=user_prompt,
                        output_cfg=output_cfg,
                    )
                    if reified_symbols is not None:
                        # find all backticked symbols in the content with re
                        _re_backticked = re.compile(r"`[^`]+`")

                        def _sub(m: re.Match[str]) -> str:
                            found_name = m[0][1:-1]

                            repl_text = m[0]
                            for symbol in reified_symbols:
                                if language == Lang.CPP or language == Lang.PYTHON:
                                    linkable_symbol_kinds = {
                                        SymbolKind.CALLABLE,
                                    }
                                elif language == Lang.C:
                                    linkable_symbol_kinds = {
                                        SymbolKind.CALLABLE,
                                        SymbolKind.CALLABLE_DECLARATION,
                                    }
                                if (
                                    found_name == symbol.raw.name
                                    and symbol.raw.symbol_kind in linkable_symbol_kinds
                                ):
                                    name_part = symbol.raw.name
                                    fqn = get_fully_qualified_name(symbol.raw)
                                    kind_part = symbol.raw.symbol_kind.name.lower()
                                    path_part = symbol.raw.file_path

                                    repl_text = f"[`{name_part}`]({path_part}#{kind_part}:{fqn})"
                                    break
                            return repl_text

                        content = _re_backticked.sub(_sub, content)

                    # TODO: actually handle rendering JSON output.
                    output += f"{section_title}\n{content}\n"
                case S.SINGLE_PROMPT_JSON:  # Simple section header, prompt, JSON structured output
                    output_cfg = OutputConfig(kind=OutputConfigKind.JSON_STRICT)
                    section_title, system_prompt, user_prompt, llm_gen_fn = args
                    content = llm_gen_fn(llm, system_prompt, user_prompt, code)
                    output += f"{section_title}\n{content!s}\n"
                case (
                    S.LLM_COND_TEXT
                    | S.LLM_COND_JSON
                ):  # Conditional construct using an LLM
                    section_title, conditional_llm_fn, true_action, false_action = args
                    llm_fn_output: list[str] | None = conditional_llm_fn(
                        llm, code, root_rel_path
                    )
                    action = false_action if llm_fn_output is None else true_action
                    if action is None:
                        pass
                    else:
                        if isinstance(action, Callable):
                            match _arity(action):
                                case 0:
                                    content = action()
                                case 2:
                                    content = action(llm, llm_fn_output)
                                case 3:
                                    content = action(llm, llm_fn_output, code)
                                case _:
                                    raise
                        elif isinstance(action, str):
                            content = action
                        else:
                            raise TemplateError(
                                "`LLM_COND` expects branch string or callable with arity 0 or 3"
                            )
                        output += f"{section_title}\n{content!s}\n"  # Call `str` to render data structure
                case (
                    S.FN_COND_TEXT
                    | S.FN_COND_JSON
                ):  # Conditional construct using a function
                    section_title, conditional_fn, true_action, false_action = args

                    match _arity(conditional_fn):
                        case 2:
                            fn_output = conditional_fn(code, root_rel_path)
                        case 3:
                            fn_output = conditional_fn(
                                code, root_rel_path, reified_symbols
                            )
                        case _:
                            raise TemplateError(
                                "`FN_COND_*` expects conditional function with arity 2 or 3"
                            )
                    action = false_action if fn_output is None else true_action
                    if (
                        action is None
                    ):  # Indication to just bail without adding any content.
                        pass
                    else:
                        if isinstance(action, Callable):
                            match _arity(action):
                                case 0:
                                    content = action()
                                case 2:
                                    content = action(llm, fn_output)
                                case 3:
                                    content = action(llm, fn_output, code)
                                case 4:
                                    content = action(
                                        llm, fn_output, code, root_rel_path
                                    )
                                case _:
                                    raise
                        elif isinstance(action, str):
                            content = action
                        else:
                            raise TemplateError(
                                "`FN_COND` expects branch string or callable with arity 0 or 3"
                            )
                        output += f"{section_title}\n{content!s}\n"  # Call `str` to render data structure
                case S.MULTI_PROMPT_TEXT:  # Simple section, but requires multiple prompts due to context limits
                    (
                        section_title,
                        system_prompt,
                        section_prompt,
                        aggregate_prompt,
                    ) = args
                    chunk_paragraphs = ""
                    for code_chunk in code_chunks[:max_num_chunks_to_use]:
                        user_prompt = f"{section_prompt}\n\nCode:\n\n{code_chunk}"
                        content = llm.generate_response(
                            system_prompt=system_prompt,
                            user_prompt=user_prompt,
                        )
                        chunk_paragraphs += f"{content}\n"
                    aggregate_user_prompt = f"{aggregate_prompt}\n\n{chunk_paragraphs}"
                    content = llm.generate_response(
                        system_prompt=system_prompt,
                        user_prompt=aggregate_user_prompt,
                    )
                    output += f"{section_title}\n{content}\n"
                case S.SINGLE_PROMPT_CHUNK_JSON:  # Simple section for a file that doesn't fit in a single context window,
                    # but only requires first code chunk
                    output_cfg = OutputConfig(kind=OutputConfigKind.JSON_STRICT)
                    section_title, system_prompt, user_prompt, llm_gen_fn = args
                    content = llm_gen_fn(
                        llm, system_prompt, user_prompt, code_chunks[0]
                    )
                    output += f"{section_title}\n{content!s}\n"
                case S.MULTI_LLM_COND_JSON:
                    # TODO: could possibly generalize by passing all code as a list of chunks even if len(chunks) == 1
                    section_title, conditional_llm_fn, true_action, false_action = args
                    llm_fn_output: list[str] | None = conditional_llm_fn(
                        llm, code, root_rel_path
                    )
                    action = false_action if llm_fn_output is None else true_action
                    if action is None:
                        pass
                    else:
                        if isinstance(action, Callable):
                            match _arity(action):
                                case 0:
                                    content = action()
                                case 2:
                                    content = action(llm, llm_fn_output)
                                case 3:
                                    content = action(llm, llm_fn_output, code_chunks)
                                case _:
                                    raise
                        elif isinstance(action, str):
                            content = action
                        else:
                            raise TemplateError(
                                "`LLM_COND` expects branch string or callable with arity 0 or 3"
                            )
                        output += f"{section_title}\n{content!s}\n"  # Call `str` to render data structure

                case _:
                    raise TemplateError(
                        f"Unsupported template section kind {tag.kind} for direct llm execution"
                    )

        return output
