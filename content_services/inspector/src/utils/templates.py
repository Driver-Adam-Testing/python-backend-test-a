from modal import Function
from pydantic import UUID4, BaseModel

from utils.models import ChatOpenAI


def _template_section_with_sse(
    section_prompt: str, workspace_id: UUID4, codebase_id: UUID4
) -> str:
    func = Function.lookup("comprehender", "single_shot_edit")
    modal_call = func.remote(
        str(workspace_id), str(codebase_id), f"{section_prompt}", {}
    )
    return f"{modal_call["content"]}\n"


class Template(BaseModel):
    system_prompt: str
    template: list[tuple[str] | tuple[str, str]]

    def run_with_code(self, llm: ChatOpenAI, code: str) -> str:
        output = ""
        for tup in self.template:
            if len(tup) == 1:  # Top level header
                output += f"{tup[0]}\n"
            else:  # 2nd level, prompt pair
                section_title, section_prompt = tup
                human_prompt = f"{section_prompt}\n\nCode:\n\n{code}"
                content = llm.generate_response(self.system_prompt, human_prompt)
                output += f"{section_title}\n{content}\n"

        return output

    def run_with_single_shot_edit_agent(
        self, workspace_id: UUID4, codebase_id: UUID4
    ) -> str:
        output = ""
        for tup in self.template:
            if len(tup) == 1:  # Top level header
                output += f"{tup[0]}\n"
            else:  # 2nd level, prompt pair
                section_title, section_prompt = tup
                content = _template_section_with_sse(
                    section_prompt=section_prompt,
                    workspace_id=workspace_id,
                    codebase_id=codebase_id,
                )
                output += f"{section_title}\n{content}\n"

        return output
