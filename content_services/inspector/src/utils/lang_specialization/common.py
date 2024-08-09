import json
from enum import IntEnum
from typing import Self

from pydantic import BaseModel
from utils.models import ChatOpenAI


class Lang(IntEnum):
    DEFAULT = 0
    C = 1
    CPP = 2

    @classmethod
    def from_ext(cls, ext: str) -> Self:
        match ext:
            case ".c" | ".h":
                return cls.C
            case ".cpp" | ".cc" | ".cxx" | ".c++" | ".hpp" | ".hh" | ".hxx" | ".h++":
                return cls.CPP
            case _:
                return cls.DEFAULT


class VariableData(BaseModel):
    type: str
    description: str
    use: str

    @classmethod
    def from_llm(
        cls,
        llm: ChatOpenAI,
        system_prompt: str,
        user_prompt: str,
        var_name: str,
        code: str,
    ) -> Self:
        user_prompt_complete = (
            f"{user_prompt}Variable to document: {var_name}\n\nCode:\n\n{code}"
        )
        content_raw = llm.generate_response(
            system_prompt=system_prompt,
            user_prompt=user_prompt_complete,
            use_json_mode=True,
        )
        content_json = json.loads(content_raw)
        return cls(
            type=content_json["type"],
            description=content_json["description"],
            use=content_json["use"],
        )
        # return cls.model_validate_json(content)


class VariableDict(BaseModel):
    data: dict[str, VariableData]

    def render_markdown(self) -> str:
        output = ""
        for k, v in self.data.items():
            output += f"### {k}\n"
            output += f"- **Type**: `{v.type}`\n"
            output += f"- **Description**: {v.description}\n"
            output += f"- **Use**: {v.use}\n\n"
        return output

    def __str__(self) -> str:
        return self.render_markdown()


class DataStructureData(BaseModel):
    type: str
    members: dict[str, str]
    description: str

    @classmethod
    def from_llm(
        cls,
        llm: ChatOpenAI,
        system_prompt: str,
        user_prompt: str,
        ds_name: str,
        code: str,
    ) -> Self:
        user_prompt_complete = (
            f"{user_prompt}Data structure to document: {ds_name}\n\nCode:\n\n{code}"
        )
        content_raw = llm.generate_response(
            system_prompt=system_prompt,
            user_prompt=user_prompt_complete,
            use_json_mode=True,
        )
        content_json = json.loads(content_raw)
        return cls(
            type=content_json["type"],
            members=content_json["members"],
            description=content_json["description"],
        )
        # return cls.model_validate_json(content)


class DataStructureDict(BaseModel):
    data: dict[str, DataStructureData]

    def render_markdown(self) -> str:
        output = ""
        for k, v in self.data.items():
            output += f"### {k}\n"
            output += f"- **Type**: `{v.type}`\n"
            output += "\n- **Members**:\n"
            if len(v.members) > 0:
                for kk, vv in v.members.items():
                    output += f"    - `{kk}`: {vv}\n"
            else:
                output += "    - None\n"
            output += f"\n- **Description**: {v.description}\n\n"
        return output

    def __str__(self) -> str:
        return self.render_markdown()


class FnData(BaseModel):
    single_sentence: str
    inputs: dict[str, str]
    control_flow: list[str]
    output: str

    @classmethod
    def from_llm(
        cls,
        llm: ChatOpenAI,
        system_prompt: str,
        user_prompt: str,
        fn_name: str,
        code: str,
    ) -> Self:
        user_prompt_complete = (
            f"{user_prompt}Function to document: {fn_name}\n\nCode:\n\n{code}"
        )
        content_raw = llm.generate_response(
            system_prompt=system_prompt,
            user_prompt=user_prompt_complete,
            use_json_mode=True,
        )
        content_json = json.loads(content_raw)
        return cls(
            single_sentence=content_json["single_sentence"],
            inputs=content_json["inputs"],
            control_flow=content_json["control_flow"],
            output=content_json["output"],
        )
        # return cls.model_validate_json(content)


class FnDict(BaseModel):
    data: dict[str, FnData]

    def render_markdown(self) -> str:
        output = ""
        for k, v in self.data.items():
            output += f"### {k}\n"
            output += f"{v.single_sentence}\n"
            output += "\n- **Inputs**:\n"
            if len(v.inputs) > 0:
                for kk, vv in v.inputs.items():
                    output += f"    - `{kk}`: {vv}\n"
            else:
                output += "    - None\n"
            output += "\n- **Output**:\n"
            output += f"    - {v.output}\n"
            output += "\n- **Logic and Control Flow**:\n"
            for item in v.control_flow:
                output += f"    - {item}\n"
            output += "\n"
        return output

    def __str__(self) -> str:
        return self.render_markdown()
