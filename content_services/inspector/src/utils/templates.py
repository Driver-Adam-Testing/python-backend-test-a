import logging
from collections.abc import Callable
from typing import Self

from modal import Function
from pydantic import UUID4, BaseModel, ValidationError

from utils.models import ChatOpenAI


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
    template: list[
        tuple[str]
        | tuple[str, str]
        | tuple[str, str, str | Callable[[], str], str | Callable[[], str]]
    ]

    def run_with_code(self, llm: ChatOpenAI, code: str) -> str:
        output = ""
        for tup in self.template:
            arity = len(tup)
            match arity:
                case 1:  # Top level header
                    output += f"{tup[0]}\n"
                case 2:  # Simple section header, prompt pair
                    section_title, section_prompt = tup
                    human_prompt = f"{section_prompt}\n\nCode:\n\n{code}"
                    content = llm.generate_response(self.system_prompt, human_prompt)
                    output += f"{section_title}\n{content}\n"
                case 4:  # Conditional construct
                    section_title, conditional_prompt, true_action, false_action = tup
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
                case _:
                    raise ValueError(
                        f"Unsupported template section arity {arity} for direct llm execution"
                    )

        return output

    def run_with_single_shot_edit_agent(
        self, workspace_id: UUID4, codebase_id: UUID4
    ) -> str:
        output = ""
        for tup in self.template:
            arity = len(tup)
            match arity:
                case 1:  # Top level header
                    output += f"{tup[0]}\n"
                case 2:  # Simple section header, prompt pair
                    section_title, section_prompt = tup
                    content = _template_section_with_sse(
                        section_prompt=section_prompt,
                        workspace_id=workspace_id,
                        codebase_id=codebase_id,
                    )
                    output += f"{section_title}\n{content}\n"
                case _:
                    raise ValueError(
                        f"Unsupported template section arity {arity} for single shot edit agent execution"
                    )

        return output
