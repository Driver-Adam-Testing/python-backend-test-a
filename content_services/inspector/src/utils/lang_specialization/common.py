import logging
from enum import IntEnum
from typing import Self

from pydantic import BaseModel
from utils.models import ChatOpenAI, OutputConfig, OutputConfigKind


class Lang(IntEnum):
    C = 0
    CPP = 1
    PYTHON = 2
    DEFAULT = 3

    @classmethod
    def from_ext_and_source(cls, ext: str, source: str) -> Self:
        match ext:
            case ".c":
                return cls.C
            case ".cpp" | ".cc" | ".cxx" | ".c++" | ".hpp" | ".hh" | ".hxx" | ".h++":
                return cls.CPP
            case ".h":
                return _disambiguate_header(source=source, fallback=cls.C)
            case ".py" | ".pyw" | ".pyi":
                return cls.PYTHON
            case _:
                return cls.DEFAULT


def _disambiguate_header(source: str, fallback: Lang) -> Lang:
    llm = ChatOpenAI(model="gpt-4o-2024-08-06", temperature=0, request_timeout=120)
    system_prompt = """
    You are a software engineering expert that determines whether a header file corresponds to the C or C++ language.

    Header files ('.h' extension) are used both in C and C++. You will be given source code from a header file and will answer whether it corresponds to C or C++ code.

    You will be given the source code in the following format:

    File contents:

    <file_contents>

    You only respond with a single number to indicate your response:
    - 0 if the code corresponds to C
    - 1 if the code corresponds to C++
    """
    user_prompt = f"File contents:\n\n{source}"
    c_or_cpp_raw = llm.generate_response(
        system_prompt=system_prompt, user_prompt=user_prompt
    )
    try:
        zero_or_one = int(c_or_cpp_raw)
        match zero_or_one:
            case 0:
                return Lang.C
            case 1:
                return Lang.CPP
            case _:
                return fallback
    except ValueError as e:
        logging.warn(
            f"Failed to parse integer from LLM response to determine if a header file is C or C++: {e}"
        )
        return fallback


class NamedContent(BaseModel):
    name: str
    content: str


class ListData(BaseModel):
    data: list[str]

    @classmethod
    def from_llm(
        cls, llm: ChatOpenAI, system_prompt: str, user_prompt: str, code: str
    ) -> Self:
        user_prompt_complete = f"{user_prompt}\n\nCode:\n\n{code}"
        content_raw = llm.generate_response(
            system_prompt=system_prompt,
            user_prompt=user_prompt_complete,
            output_cfg=OutputConfig(kind=OutputConfigKind.JSON_STRICT, payload=cls),
        )

        return cls.parse_raw(content_raw)

    def render_markdown(self) -> str:
        output = ""
        output += "\n---\n"
        for dep in self.data:
            output += f"- `{dep}`\n"
        output += "\n"
        return output

    def __str__(self) -> str:
        return self.render_markdown()


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
            output_cfg=OutputConfig(kind=OutputConfigKind.JSON_STRICT, payload=cls),
        )

        return cls.parse_raw(content_raw)


class VariableDict(BaseModel):
    data: dict[str, VariableData]

    def render_markdown(self) -> str:
        output = ""
        for k, v in self.data.items():
            output += f"\n---\n### {k}\n"
            output += f"- **Type**: `{v.type}`\n"
            output += f"- **Description**: {v.description}\n"
            output += f"- **Use**: {v.use}\n\n"

        return output

    def __str__(self) -> str:
        return self.render_markdown()


class DataStructureData(BaseModel):
    type: str
    members: list[NamedContent]
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
            output_cfg=OutputConfig(kind=OutputConfigKind.JSON_STRICT, payload=cls),
        )

        return cls.parse_raw(content_raw)


class DataStructureDict(BaseModel):
    data: dict[str, DataStructureData]

    def render_markdown(self) -> str:
        output = ""
        for k, v in self.data.items():
            output += f"\n---\n### {k}\n"
            output += f"- **Type**: `{v.type}`\n"
            output += "\n- **Members**:\n"
            if len(v.members) > 0:
                for m in v.members:
                    output += f"    - `{m.name}`: {m.content}\n"
            else:
                output += "    - None\n"
            output += f"\n- **Description**: {v.description}\n\n"
        return output

    def __str__(self) -> str:
        return self.render_markdown()


class FnData(BaseModel):
    single_sentence: str
    inputs: list[NamedContent]
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
            output_cfg=OutputConfig(kind=OutputConfigKind.JSON_STRICT, payload=cls),
        )

        return cls.parse_raw(content_raw)


class FnDict(BaseModel):
    data: dict[str, FnData]

    def render_markdown(self) -> str:
        output = ""
        for k, v in self.data.items():
            output += f"\n---\n### {k}\n"
            output += f"{v.single_sentence}\n"
            output += "\n- **Inputs**:\n"
            if len(v.inputs) > 0:
                for i in v.inputs:
                    output += f"    - `{i.name}`: {i.content}\n"
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
