import logging
from collections.abc import Callable
from enum import IntEnum
from pathlib import Path
from typing import Any, Self

from modal import Function
from pydantic import UUID4, BaseModel, ValidationError

from utils.models import ChatOpenAI


class S(IntEnum):
    RAW = 0
    SINGLE_PROMPT = 1
    LLM_COND = 2
    FN_COND = 3


class SectionKind(BaseModel):
    kind: S


def _template_section_with_sse(
    section_prompt: str, workspace_id: UUID4, codebase_id: UUID4
) -> str:
    func = Function.lookup("comprehender", "single_shot_edit")
    modal_call = func.remote(
        str(workspace_id), str(codebase_id), f"{section_prompt}", {}
    )
    return f"{modal_call["content"]}\n"


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
    system_prompt: str
    template: list[Any]

    def run_with_code(self, llm: ChatOpenAI, root_rel_path: Path, code: str) -> str:
        output = ""
        for tup in self.template:
            tag = SectionKind(kind=tup[0])
            args = tup[1:]
            match tag.kind:
                case S.RAW:
                    (raw_content,) = args
                    output += f"{raw_content}\n"
                case S.SINGLE_PROMPT:  # Simple section header, prompt pair
                    section_title, section_prompt = args
                    human_prompt = f"{section_prompt}\n\nCode:\n\n{code}"
                    content = llm.generate_response(self.system_prompt, human_prompt)
                    output += f"{section_title}\n{content}\n"
                case S.LLM_COND:  # Conditional construct using an LLM
                    section_title, conditional_prompt, true_action, false_action = args
                    conditional_human_prompt = (
                        f"{conditional_prompt}\n\nCode:\n\n{code}"
                    )
                    conditional = Boolean.from_llm(
                        llm=llm,
                        code=code,
                        system_prompt=self.system_prompt,
                        human_prompt=conditional_human_prompt,
                    )
                    action = true_action if conditional else false_action
                    if isinstance(action, Callable):
                        content = action()
                    else:
                        action_human_prompt = f"{action}\n\nCode:\n\n{code}"
                        content = llm.generate_response(
                            self.system_prompt, action_human_prompt
                        )
                    output += f"{section_title}\n{content}\n"
                case S.FN_COND:  # Conditional construct using a function
                    section_title, conditional_fn, true_action, false_action = args
                    fn_output: str | None = conditional_fn(code, root_rel_path)
                    action = false_action if fn_output is None else true_action
                    if (
                        action is None
                    ):  # Indication to just bail without adding any content.
                        pass
                    else:
                        if isinstance(action, Callable):
                            content = action()
                        else:
                            context_from_fn = (
                                "" if fn_output is None else f"{fn_output}\n\n"
                            )
                            action_human_prompt = (
                                f"{context_from_fn}{action}\n\nCode:\n\n{code}"
                            )
                            content = llm.generate_response(
                                self.system_prompt, action_human_prompt
                            )
                        output += f"{section_title}\n{content}\n"
                case _:
                    raise ValueError(
                        f"Unsupported template section kind {tag.kind} for direct llm execution"
                    )

        return output

    def run_with_single_shot_edit_agent(
        self, workspace_id: UUID4, codebase_id: UUID4
    ) -> str:
        output = ""
        for tup in self.template:
            tag = SectionKind(kind=tup[0])
            args = tup[1:]
            match tag.kind:
                case S.RAW:
                    (raw_content,) = args
                    output += f"{raw_content}\n"
                case S.SINGLE_PROMPT:  # Simple section header, prompt pair
                    section_title, section_prompt = args
                    content = _template_section_with_sse(
                        section_prompt=section_prompt,
                        workspace_id=workspace_id,
                        codebase_id=codebase_id,
                    )
                    output += f"{section_title}\n{content}\n"
                case _:
                    raise ValueError(
                        f"Unsupported template section kind {tag.kind} for single shot edit agent execution"
                    )

        return output
