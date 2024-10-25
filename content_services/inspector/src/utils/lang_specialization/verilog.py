from functools import partial
from pathlib import Path
from typing import Self

import openai
from pydantic import BaseModel
from utils.codemap_ctags import extract_symbols_w_ctags
from utils.models import ChatOpenAI, OutputConfig, OutputConfigKind

from .common import (
    NamedContent,
    variables_dict_from_llm,
)

# GO for:
# Tasks and Functions
# Modules
# Constants
# Data Types (regs and nets)
# Ports


VERILOG_MODULES = {"module"}
VERILOG_FUNCTIONS_AND_TASKS = {"function", "task"}
VERILOG_DATA_TYPES = {"register", "net", "port"}
VERILOG_CONSTANTS = {"constant"}
VERILOG_PORTS = {"port"}

SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_VERILOG = """
You are an expert verilog programmer, experienced with hardware description languages and design, and a technical documentation expert. You write detailed documentation to explain code written in verilog.

You are skilled at explaining technical details as well as recognizing and articulating the key conceptual components and purpose of software.
"""

SOURCE_CODE_SMALL_SYSTEM_PROMPT_GENERAL_VERILOG = """
You are an expert verilog programmer, experienced with hardware description languages and design, and a technical documentation expert. You write detailed documentation to explain code written in verilog.

You are skilled at explaining technical details as well as recognizing and articulating the key conceptual components and purpose of software.

You specialize in effectively describing small and short source code files. Your goal is to be terse and clear, since the source code you are describing is small and simple.
"""

SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT = """
You will be given the content of a verilog source code file. In 1 or 2 paragraphs, explain the purpose of the file.

When writing your paragraphs, do not use speculative language.

When writing your paragraphs, consider questions like the following. You do not need to explicitly state these ideas, they are just given as examples of the kind of information to provide:

- Does this code provide narrow or broad functionality?
- What are the most important technical components?
- Is this code a collection of many different components? If so, what is the common theme or purpose?
- What kind of code is this? Does this largely define library components used elsewhere, top-level implementation, etc.?
"""

SOURCE_CODE_SMALL_PURPOSE_USER_PROMPT = """
You will be given the content of a verilog source code file. In a single paragraph of 3 to 5 sentences, explain the purpose of the file
"""

MODULES_FOUND_SYSTEM_PROMPT_JSON = """
You are an expert Verilog and hardware description language programmer and a technical documentation expert. You write detailed documentation to explain code written in Verilog.

You focus on writing technical documentation for modules. You are skilled at explaining technical details as well as recognizing and articulating the key conceptual components and purpose of software.

You will be given the name of a module to document and the source code where the module is defined.

Your job is to describe the module. **Always respond using exactly the following JSON schema**:
{
    "constants": [
        {"name": <constant1>, "content": <description of constant parameter 1>},
        {"name": <constant2>, "content": <description of constant parameter 2>},
        ...
    ],
    "ports": [
        {"name": <port_name1>, "content": <Terse 1 sentence description of the first port>},
        {"name": <port_name2>, "content": <Terse 1 sentence description of the second port>},
        ...
    ],
    "description": <one paragraph description of the module>,
}

Return JSON according to the schema above. Do not use the format ```json ... ```, just return the JSON data.
"""

MODULES_FOUND_USER_PROMPT = """
Summarize the modules in the code provided below.

- A verilog module is a reusable block of verilog code that implements a specific functionality.
- A verilog module can embed other modules or be embedded in other modules.
- A verilog module may contain a list of parameter constants.
- A verilog module communicates through a list of input and output ports.
- When describing a module, provide detail that matches the complexity of the module. Large and complex modules should get longer explanations, while small ones a single sentence.
"""

MODULES_NONE_CONTENT = "\n---\nNo modules defined in this file."

FUNCTIONS_AND_TASKS_FOUND_SYSTEM_PROMPT_JSON = """
You are an expert Verilog and hardware description language programmer and a technical documentation expert. You write detailed documentation to explain code written in Verilog.

You focus on writing technical documentation for functions and tasks. You are skilled at explaining technical details as well as recognizing and articulating the key conceptual components and purpose of software.

You will be given the name of a functon or task to document and the source code where the module is defined.

In Verilog, a function processes a single input and returns a single value. A task is more general and can calculate multiple return values, returning them using `output` and `inout` type arguments.

Your job is to describe the function or task. **Always respond using exactly the following JSON schema**:
{
    "single_sentence": <terse single sentence description of the function or task>,
    "inputs": [
        {"name": <input_arg1>, "content": <description of input argument 1>},
        {"name": <input_arg2>, "content": <description of input argument 2>},
        ...
    ],
    "control_flow": [
        <bullet point 1 for description of logic and control flow>,
        <bullet point 2 for description of logic and control flow>,
        ...
    ],
    "outputs": [
        {"name": <output_arg1 or inout_arg1>, "content": <description of output or inout argument 1>},
        {"name": <output_arg2 or inout_arg2>, "content": <description of output or inout argument 2>},
    ]
}

Return JSON according to the schema above. Do not use the format ```json ... ```, just return the JSON data.
"""

FUNCTIONS_AND_TASKS_FOUND_USER_PROMPT = """
Summarize the functions and tasks in the code provided below.

- A verilog function processes a single input and returns a single value.
- A verilog task is more general and can calculate multiple return values, returning them using `output` and `inout` type arguments.
- When describing a function or task, provide detail that matches the complexity of the funciton or task. Large and complex functions or tasks should get longer explanations, while small ones a single sentence.
"""

FUNCTIONS_AND_TASKS_NONE_CONTENT = "\n---\nNo functions or tasks defined in this file."


DATA_TYPES_FOUND_SYSTEM_PROMPT_JSON = """
You are an expert Verilog and hardware description language programmer and a technical documentation expert. You write detailed documentation to explain code written in Verilog.

You focus on writing technical documentation for data types and data structures in verilog. You are skilled at explaining technical details as well as recognizing and articulating the key conceptual components and purpose of software.

You will be given the name of a data structure -- a port, a register, or a net data type -- to document and the source code where the port is defined.

Ports are signals that act as inputs and outputs between modules in verilog. Registers are variables to store values. Net data types represent values that change when some driver changes (e.g., a wire).

Your job is to describe the data type. **Always respond using exactly the following JSON schema**:
{
    "type": <type of the data type>,
    "description": <1 to 3 sentence description of the data type>,
    "use": <Terse 1 sentence description of how this data type is used>,
}

Return JSON according to the schema above. Do not use the format ```json ... ```, just return the JSON data.
"""

DATA_TYPES_FOUND_USER_PROMPT = """
Summarize the data types in the code provided below.

- Ports are signals that act as inputs and outputs between modules in verilog.
- Registers are variables to store values.
- Net data types represent values that change when some driver changes (e.g., a wire).
- When describing a data type, provide detail that matches the complexity of the data type. Large and complex data types should get longer explanations, while simpler ones much less.
"""

DATA_TYPES_NONE_CONTENT = "\n---\nNo data types defined in this file."


class ModuleData(BaseModel):
    constants: list[NamedContent]
    ports: list[NamedContent]
    description: str

    @classmethod
    def from_llm(
        cls,
        llm: ChatOpenAI,
        system_prompt: str,
        user_prompt: str,
        m_name: str,
        code: str,
    ) -> Self:
        user_prompt_complete = (
            f"{user_prompt}Module to document: {m_name}\n\nCode:\n\n{code}"
        )
        try:
            content_raw = llm.generate_response(
                system_prompt=system_prompt,
                user_prompt=user_prompt_complete,
                output_cfg=OutputConfig(kind=OutputConfigKind.JSON_STRICT, payload=cls),
            )
        except openai.LengthFinishReasonError as _:
            return cls(type="", members=[], description="Module too large to process")

        return cls.parse_raw(content_raw)


class ModuleDict(BaseModel):
    data: dict[str, ModuleData]

    def render_markdown(self) -> str:
        output = ""
        for k, v in self.data.items():
            output += f"\n---\n### {k}\n"
            output += "\n- **Constants**:\n"
            if len(v.constants) > 0:
                for c in v.constants:
                    output += f"    - `{c.name}`: {c.content}\n"
            else:
                output += "    - None\n"
            output += "\n- **Ports**:\n"
            if len(v.ports) > 0:
                for m in v.ports:
                    output += f"    - `{m.name}`: {m.content}\n"
            else:
                output += "    - None\n"
            output += f"\n- **Description**: {v.description}\n\n"
        return output

    def __str__(self) -> str:
        return self.render_markdown()


def module_dict_from_llm_verilog(
    llm: ChatOpenAI, m_list: list[str], code: str
) -> ModuleDict:
    m_dict = {
        m: ModuleData.from_llm(
            llm=llm,
            system_prompt=MODULES_FOUND_SYSTEM_PROMPT_JSON,
            user_prompt=MODULES_FOUND_USER_PROMPT,
            m_name=m,
            code=code,
        )
        for m in m_list
    }
    return ModuleDict(data=m_dict)


def verilog_module_checker(
    code: str, root_rel_path: Path, structured_output: bool = True
) -> list[str] | str | None:
    symbols = extract_symbols_w_ctags(root_rel_path=root_rel_path, file_content=code)
    m_list = []
    for s in symbols:
        if s["kind"] in VERILOG_MODULES:
            m_list.append(s["name"])
    if len(m_list) > 0:
        if structured_output:
            output = m_list
        else:
            output = "\nModules to document in the code:\n\n"
            for m in m_list:
                output += f"- {m}\n"
    else:
        output = None
    return output


class FnTaskData(BaseModel):
    single_sentence: str
    inputs: list[NamedContent]
    control_flow: list[str]
    outputs: list[str]

    @classmethod
    def from_llm(
        cls,
        llm: ChatOpenAI,
        system_prompt: str,
        user_prompt: str,
        ft_name: str,
        code: str,
    ) -> Self:
        user_prompt_complete = (
            f"{user_prompt}Function or task to document: {ft_name}\n\nCode:\n\n{code}"
        )
        content_raw = llm.generate_response(
            system_prompt=system_prompt,
            user_prompt=user_prompt_complete,
            output_cfg=OutputConfig(kind=OutputConfigKind.JSON_STRICT, payload=cls),
        )

        return cls.parse_raw(content_raw)


class FnTaskDict(BaseModel):
    data: dict[str, FnTaskData]

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
            if len(v.outputs) > 0:
                for o in v.outputs:
                    output += f"    - {o}\n"
            else:
                output += "    - None\n"
            output += "\n- **Logic and Control Flow**:\n"
            for item in v.control_flow:
                output += f"    - {item}\n"
            output += "\n"
        return output

    def __str__(self) -> str:
        return self.render_markdown()


def fntask_dict_from_llm_verilog(
    llm: ChatOpenAI, ft_list: list[str], code: str
) -> FnTaskDict:
    ft_dict = {
        ft: FnTaskData.from_llm(
            llm=llm,
            system_prompt=FUNCTIONS_AND_TASKS_FOUND_SYSTEM_PROMPT_JSON,
            user_prompt=FUNCTIONS_AND_TASKS_FOUND_USER_PROMPT,
            ft_name=ft,
            code=code,
        )
        for ft in ft_list
    }
    return FnTaskDict(data=ft_dict)


def verilog_fntask_checker(
    code: str, root_rel_path: Path, structured_output: bool = True
) -> list[str] | str | None:
    symbols = extract_symbols_w_ctags(root_rel_path=root_rel_path, file_content=code)
    ft_list = []
    for s in symbols:
        if s["kind"] in VERILOG_FUNCTIONS_AND_TASKS:
            ft_list.append(s["name"])
    if len(ft_list) > 0:
        if structured_output:
            output = ft_list
        else:
            output = "\nFunctions and tasks to document in the code:\n\n"
            for ft in ft_list:
                output += f"- {ft}\n"
    else:
        output = None
    return output


def verilog_data_types_checker(
    code: str, root_rel_path: Path, structured_output: bool = True
) -> list[str] | str | None:
    symbols = extract_symbols_w_ctags(root_rel_path=root_rel_path, file_content=code)
    dt_list = [s["name"] for s in symbols if s["kind"] in VERILOG_DATA_TYPES]
    if len(dt_list) > 0:
        if structured_output:
            output = dt_list
        else:
            output = "\nData types to document in the code:\n\n"
            for dt in dt_list:
                output += f"- {dt}\n"
    else:
        output = None
    return output


data_types_dict_from_llm_verilog = partial(
    variables_dict_from_llm,
    DATA_TYPES_FOUND_SYSTEM_PROMPT_JSON,
    DATA_TYPES_FOUND_USER_PROMPT,
)
