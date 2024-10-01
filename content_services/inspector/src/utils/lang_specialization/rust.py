from functools import partial
from pathlib import Path
from typing import Any, Self

from pydantic import BaseModel
from utils.codemap_ctags import extract_symbols_w_ctags
from utils.models import ChatOpenAI, OutputConfig, OutputConfigKind

from .common import (
    MAX_VARIABLES_TO_DOCUMENT,
    FnData,
    NamedContent,
    fn_dict_from_llm,
    render_function,
    variables_dict_from_llm,
)

RUST_DATA_STRUCTURE = {"enum", "struct"}
RUST_FUNCTIONS = {"function"}
RUST_METHODS = {"method"}
RUST_VARIABLES = {"constant", "variable"}
RUST_MACROS = {"macro"}
RUST_TRAITS = {"interface"}
RUST_IMPLEMENTATIONS = {"implementation"}


SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_RUST = """
You are an expert Rust programmer and a software engineering documentation expert. You write detailed documentation to explain code written in Rust.

You are skilled at explaining technical details as well as recognizing and articulating the key conceptual components and purpose of software.
"""

SOURCE_CODE_SMALL_SYSTEM_PROMPT_GENERAL_RUST = """
You are an expert Rust programmer and a software engineering documentation expert. You write detailed documentation to explain code written in Rust.

You are skilled at explaining technical details as well as recognizing and articulating the key conceptual components and purpose of software.

You specialize in effectively describing small and short source code files. Your goal is to be terse and clear, since the source code you are describing is small and simple.
"""

SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT = """
You will be given the content of a source code file. In 1 or 2 paragraphs, explain the purpose of the file.

When writing your paragraphs, do not use speculative language.

When writing your paragraphs, consider questions like the following. You do not need to explicitly state these ideas, they are just given as examples of the kind of information to provide:

- Does this code provide narrow or broad functionality?
- What are the most important technical components?
- Is this code a collection of many different components? If so, what is the common theme or purpose?
- What kind of code is this? For example, is this code clearly as script, a library file intended to be imported elsewhere, etc.?
- Does it define public APIs or external interfaces?
"""

SOURCE_CODE_SMALL_PURPOSE_USER_PROMPT = """
You will be given the content of a source code file. In a single paragraph of 3 to 5 sentences, explain the purpose of the file. Consider questions such as the following when providing your output:

- Does this code provide narrow or broad functionality?
- What kind of code is this? For example, is this code a short script, a collection of global variables or configuration variables, etc.?
"""

DATA_STRUCTURES_FOUND_SYSTEM_PROMPT_JSON = """
You are an expert Rust programmer and a software engineering documentation expert. You write detailed documentation to explain code written in Rust.

You focus on writing technical documentation for data structures in Rust. You are skilled at explaining technical details as well as recognizing and articulating the key conceptual components and purpose of software.

You will be given the name of a data structure to document and the source code where the data structure is defined.

Your job is to describe the data structure. **Always respond using exactly the following JSON schema**:
{
    "type": <struct or enum>,
    "members": [
        {"name": <member_name1>, "content": <Terse 1 sentence description of the first struct field or enum variant>},
        {"name": <member_name2>, "content": <Terse 1 sentence description of the second struct field or enum variant>},
        ...
    ],
    "description": <one paragraph description of the data structure>,
    "trait_bounds": [<list of trait bounds for the data structure>],
}

Return JSON according to the schema above. Do not use the format ```json ... ```, just return the JSON data.
"""

DATA_STRUCTURES_FOUND_USER_PROMPT = """
Summarize the data structure in the code provided below.

- When describing a data structure, provide detail that matches the complexity of the data structure. Large and complex data structures with many members should get longer explanations, while small ones a single sentence.
"""

METHODS_FOUND_SYSTEM_PROMPT_JSON = """
You are an expert Rust programmer and a software engineering documentation expert. You write detailed documentation to explain code written in Rust.

You focus on writing technical documentation for method implementations. You are skilled at explaining technical details as well as recognizing and articulating the key conceptual components and purpose of software.

You will be given the name of a method implementation to document and the source code where the method is implemented.

Identify the associated data structure in your description and always include any `self` argument (self, &self, or &mut self) that exists in a given method as an input.

Your job is to describe the method. **Always respond using exactly the following JSON schema**:
{
    "single_sentence": <terse single sentence description of the function>,
    "inputs": [
        {"name": <self, &self, or &mut self>, "content": <description of input argument 1>},
        {"name": <input_arg2>, "content": <description of input argument 2>},
        ...
    ],
    "control_flow": [
        <bullet point 1 for description of control flow>,
        <bullet point 2 for description of control flow>,
        ...
    ],
    "output": <description of output>
}

Return JSON according to the schema above. Do not use the format ```json ... ```, just return the JSON data.
"""

METHODS_FOUND_USER_PROMPT = """
Summarize the data structure method in the code provided below. Describe the inputs, control flow and logic, and output.

- When describing a data structure method, provide detail that matches the complexity of the method body. Large and complex methods should get longer explanations, while small ones much less.
"""

MACROS_FOUND_SYSTEM_PROMPT_JSON = """
You are an expert Rust programmer and a software engineering documentation expert. You write detailed documentation to explain code written in Rust.

You focus on writing technical documentation for macros in Rust. You are skilled at explaining technical details as well as recognizing and articulating the key conceptual components and purpose of software.

You will be given the name of a macro to document and the source code where the macro is defined.

Your job is to describe the macro. **Always respond using exactly the following JSON schema**:
{
    "type": <type of the macro, either declarative or procedural>,
    "description": <1 to 3 sentence description of the variable>,
    "logic": [
        <bullet point 1 describing logic implemented by the macro>,
        <Bullet point 2 describint logic implemenbed by the macro>,
        ...
    ],
    "use": <Terse 1 sentence description of how this macro is used>,
}

Return JSON according to the schema above. Do not use the format ```json ... ```, just return the JSON data.
"""

MACROS_FOUND_USER_PROMPT = """
Summarize the data structure in the code provided below.

- When describing a data structure, provide detail that matches the complexity of the data structure. Large and complex data structures with many members should get longer explanations, while small ones a single sentence.
"""

FUNCTIONS_FOUND_SYSTEM_PROMPT_JSON = """
You are an expert Rust programmer and a software engineering documentation expert. You write detailed documentation to explain code written in Rust.

You focus on writing technical documentation for functions. You are skilled at explaining technical details as well as recognizing and articulating the key conceptual components and purpose of software.

You will be given the name of a function to document and the source code where the function is defined.

Your job is to describe the function. **Always respond using exactly the following JSON schema**:
{
    "single_sentence": <terse single sentence description of the function>,
    "inputs": [
        {"name": <input_arg1>, "content": <description of input argument 1>},
        {"name": <input_arg2>, "content": <description of input argument 2>},
        ...
    ],
    "control_flow": [
        <bullet point 1 for description of control flow>,
        <bullet point 2 for description of control flow>,
        ...
    ],
    "output": <description of output>
}

Return JSON according to the schema above. Do not use the format ```json ... ```, just return the JSON data.
"""

FUNCTIONS_FOUND_USER_PROMPT = """
Summarize the function in the code provided below. Describe the inputs, control flow and logic, and output.

- When describing a function, provide detail that matches the complexity of the function body. Large and complex functions should get longer explanations, while small ones much less.
"""

VARIABLES_FOUND_SYSTEM_PROMPT_JSON = """
You are an expert Rust programmer and a software engineering documentation expert. You write detailed documentation to explain code written in Python.

You focus on writing technical documentation for global variables and constants. You are skilled at explaining technical details as well as recognizing and articulating the key conceptual components and purpose of software.

You will be given the name of a global variable or constant to document and the source code where the data structure is defined.

Your job is to describe the global variable or constant. **Always respond using exactly the following JSON schema**:
{
    "type": <type of the variable>,
    "description": <1 to 3 sentence description of the variable>,
    "use": <Terse 1 sentence description of how this variable is used>,
}

Return JSON according to the schema above. Do not use the format ```json ... ```, just return the JSON data.
"""

VARIABLES_FOUND_USER_PROMPT = """
Summarize the global variable or constant in the code provided below.

- A global variable is declared at the top level scope. Local variables declared and used inside of functions are not global variables. You will be describing a global variable.
- When describing a variable, provide detail that matches the complexity of the variable. Large and complex global variables (e.g., containing large data structure instances) should get longer explanations, while small ones (e.g., one line definitions) much less.
"""

TRAITS_FOUND_SYSTEM_PROMPT_JSON = """
You are an expert Rust programmer and a software engineering documentation expert. You write detailed documentation to explain code written in Rust.

You focus on writing technical documentation for data structures in Rust. You are skilled at explaining technical details as well as recognizing and articulating the key conceptual components and purpose of software.

You will be given the name of a Rust trait to document and the source code where the trait is defined.

Your job is to describe the data structure. **Always respond using exactly the following JSON schema**:
{
    "trait_bounds": [<list of concrete trait bounds for the trait, if any>],
    "generic_types": [<list of generic types for the trait, if any>],
    "methods": [
        {"name": <member_name1>, "content": <Terse 1 sentence description of the first method defined for the trait>},
        {"name": <member_name2>, "content": <Terse 1 sentence description of the second method defined for the trait>},
        ...
    ],
    "description": <one paragraph description of the trait>,
}

Return JSON according to the schema above. Do not use the format ```json ... ```, just return the JSON data.
"""

TRAITS_FOUND_USER_PROMPT = """
Summarize the trait in the code provided below.

- When describing a trait, provide detail that matches the complexity of the trait. Large and complex data structures with many methods, generics, and trait bounds should get longer explanations, while small ones a single sentence.
"""


class MacroData(BaseModel):
    type: str
    description: str
    logic: list[str]
    use: str

    @classmethod
    def from_llm(
        cls,
        llm: ChatOpenAI,
        system_prompt: str,
        user_prompt: str,
        macro_name: str,
        code: str,
    ) -> Self:
        user_prompt_complete = (
            f"{user_prompt}Macro to document: {macro_name}\n\nCode:\n\n{code}"
        )
        content_raw = llm.generate_response(
            system_prompt=system_prompt,
            user_prompt=user_prompt_complete,
            output_cfg=OutputConfig(kind=OutputConfigKind.JSON_STRICT, payload=cls),
        )

        return cls.parse_raw(content_raw)


class MacroDict(BaseModel):
    data: dict[str, MacroData]

    def render_markdown(self) -> str:
        output = ""
        for k, v in self.data.items():
            output += f"\n---\n## {k}\n"
            output += f"- **Type**: `{v.type}`\n"
            output += f"- **Description**: {v.description}\n"
            output += "- **Logic**:\n"
            for item in v.logic:
                output += f"    - {item}\n"
            output += f"- **Use**: {v.use}\n\n"

        return output

    def __str__(self) -> str:
        return self.render_markdown()


class TraitData(BaseModel):
    trait_bounds: list[str]
    generic_types: list[str]
    methods: list[NamedContent]
    description: str

    @classmethod
    def from_llm(
        cls,
        llm: ChatOpenAI,
        system_prompt: str,
        user_prompt: str,
        trait_name: str,
        code: str,
    ) -> Self:
        user_prompt_complete = (
            f"{user_prompt}Trait to document: {trait_name}\n\nCode:\n\n{code}"
        )
        content_raw = llm.generate_response(
            system_prompt=system_prompt,
            user_prompt=user_prompt_complete,
            output_cfg=OutputConfig(kind=OutputConfigKind.JSON_STRICT, payload=cls),
        )

        return cls.parse_raw(content_raw)


class TraitDataDict(BaseModel):
    data: dict[str, TraitData]

    def render_markdown(self) -> str:
        output = ""
        for k, v in self.data.items():
            output += f"\n---\n## {k}\n"
            if len(v.trait_bounds) > 0:
                output += "- **Trait Bounds**\n"
                for tb in v.trait_bounds:
                    output += f"    - `{tb}`\n"
            if len(v.generic_types) > 0:
                output += "- **Generic Types**\n"
                for gt in v.generic_types:
                    output += f"    - `{gt}`\n"
            if len(v.methods) > 0:
                output += "- **Methods**\n"
                for m in v.methods:
                    output += f"    - `{m.name}`: {m.content}\n"
            output += f"- **Description**\n{v.description}\n"
        return output

    def __str__(self) -> str:
        return self.render_markdown()


class DataStructureBaseData(BaseModel):
    type: str
    members: list[NamedContent]
    description: str
    trait_bounds: list[str]

    @classmethod
    def from_llm(
        cls,
        llm: ChatOpenAI,
        system_prompt: str,
        user_prompt: str,
        name: str,
        code: str,
    ) -> Self:
        user_prompt_complete = (
            f"{user_prompt}Data structure to document: {name}\n\nCode:\n\n{code}"
        )
        content_raw = llm.generate_response(
            system_prompt=system_prompt,
            user_prompt=user_prompt_complete,
            output_cfg=OutputConfig(kind=OutputConfigKind.JSON_STRICT, payload=cls),
        )

        return cls.parse_raw(content_raw)


class DataStructureData(BaseModel):
    base_data: DataStructureBaseData
    methods: dict[str, FnData | list[FnData]]
    nested_data_structures: list[str]


def render_data_structure_base_data(
    data_structure_name: str, data_structure_data: DataStructureData
) -> str:
    output = ""
    output += f"\n---\n---\n### {data_structure_name}\n"
    output += f"- **Type**: `{data_structure_data.base_data.type}`\n"
    if len(data_structure_data.base_data.trait_bounds) > 0:
        output += "\n- **Trait Bounds**:\n"
        for i in data_structure_data.base_data.trait_bounds:
            output += f"    - `{i}`\n"
    output += f"\n- **Description**: {data_structure_data.base_data.description}\n\n"
    output += "\n- **Members**:\n"
    if len(data_structure_data.base_data.members) > 0:
        non_dupe_members = 0
        for m in data_structure_data.base_data.members:
            if (
                data_structure_name not in data_structure_data.methods
                and data_structure_name
                not in data_structure_data.nested_data_structures
            ):
                output += f"    - `{m.name}`: {m.content}\n"
                non_dupe_members += 1
        if non_dupe_members == 0:
            output += "    - None\n"
    return output


class DataStructureDict(BaseModel):
    data: dict[str, DataStructureData]

    def render_markdown(self) -> str:
        output = ""
        for k, v in self.data.items():
            output += render_data_structure_base_data(k, v)
            if len(v.methods) > 0:
                output += "\n**Methods**\n"
                for n, m in v.methods.items():
                    # Case of potentially overloaded method.
                    if isinstance(m, list):
                        for sub_m in m:
                            output += render_function(n, sub_m, 4)
                    else:
                        output += render_function(n, m, 4)
            if len(v.nested_data_structures) > 0:
                output += "\n**Nested Data Structures**:\n"
                for n in v.nested_data_structures:
                    output += f"    - {n}\n"

        return output

    def __str__(self) -> str:
        return self.render_markdown()


def macros_dict_from_llm(
    system_prompt: str,
    user_prompt: str,
    llm: ChatOpenAI,
    macros_list: list[str],
    code: str,
) -> MacroDict:
    macros_dict = {
        m: MacroData.from_llm(
            llm=llm,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            macro_name=m,
            code=code,
        )
        for m in macros_list[:MAX_VARIABLES_TO_DOCUMENT]
    }
    return MacroDict(data=macros_dict)


BLIND_ADVANCE_IF_NO_END_LINE = 200


def data_structure_dict_from_llm(
    system_prompt_ds: str,
    user_prompt_ds: str,
    system_prompt_fn: str,
    user_prompt_fn: str,
    method_delimiter: str,
    llm: ChatOpenAI,
    data_structure_dict_raw: dict[str, dict[str, Any]],
    code: str,
) -> DataStructureDict:
    data_structure_dict_documented = {}
    global_method_counts = {}
    for _, ds_data in data_structure_dict_raw.items():
        for m in ds_data["methods"]:
            name = m["name"]
            global_method_counts[name] = global_method_counts.get(name, 0) + 1
    for ds_name, ds_data in data_structure_dict_raw.items():
        data_structure_base = DataStructureBaseData.from_llm(
            system_prompt=system_prompt_ds,
            user_prompt=user_prompt_ds,
            llm=llm,
            name=ds_name,
            code=code,
        )
        methods = {}
        nested_data_structures = []
        for m in ds_data["methods"]:
            m_name = m["name"]
            scoped_name = ds_name + method_delimiter + m_name
            # More than one method with the same name in the file: cut scope for LLM.
            if global_method_counts[m_name] > 1:
                m_start_line = m["line"]
                # TODO: Better solution if end line is not present.
                m_end_line = m.get("end", m_start_line + BLIND_ADVANCE_IF_NO_END_LINE)
                code_lines = code.splitlines()
                m_code = "\n".join(code_lines[m_start_line - 1 : m_end_line + 1])
                # Use list to handle method overloading, if present.
                if scoped_name not in methods:
                    methods[scoped_name] = []
                methods[scoped_name].append(
                    FnData.from_llm(
                        system_prompt=system_prompt_fn,
                        user_prompt=user_prompt_fn,
                        llm=llm,
                        fn_name=m_name,
                        code=m_code,
                    )
                )
            else:
                m_data = FnData.from_llm(
                    system_prompt=system_prompt_fn,
                    user_prompt=user_prompt_fn,
                    llm=llm,
                    fn_name=m_name,
                    code=code,
                )
                methods[scoped_name] = m_data

        for nested_data_structure in ds_data["nested_data_structures"]:
            nested_data_structures.append(nested_data_structure["name"])

        data_structure_data = DataStructureData(
            base_data=data_structure_base,
            methods=methods,
            nested_data_structures=nested_data_structures,
        )
        data_structure_dict_documented[ds_name] = data_structure_data
    return DataStructureDict(data=data_structure_dict_documented)


def traits_dict_from_llm(
    system_prompt: str,
    user_prompt: str,
    llm: ChatOpenAI,
    traits_list: list[str],
    code: str,
) -> TraitDataDict:
    traits_dict = {
        v: TraitData.from_llm(
            llm=llm,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            trait_name=v,
            code=code,
        )
        for v in traits_list[:MAX_VARIABLES_TO_DOCUMENT]
    }
    return TraitDataDict(data=traits_dict)


def rust_data_structure_checker(
    code: str, root_rel_path: Path, structured_output: bool = True
) -> dict[str, dict[str, Any]] | str | None:
    symbols = extract_symbols_w_ctags(root_rel_path=root_rel_path, file_content=code)
    data_structures_dict = {}
    for s in symbols:
        if s["kind"] in RUST_DATA_STRUCTURE and not s["name"].startswith("__anon"):
            name = s["name"]
            methods = []
            nested_data_structures = []
            for sub_s in symbols:
                if (
                    (sub_s.get("scopeKind") in RUST_IMPLEMENTATIONS)
                    and (sub_s.get("scope") == name)
                    and (sub_s is not s)
                ):
                    # TODO: Pretty sure we're safe here as Rust does not have method overloading.
                    if sub_s["kind"] in RUST_METHODS:
                        methods.append(sub_s)
                    elif sub_s["kind"] in RUST_DATA_STRUCTURE:
                        nested_data_structures.append(sub_s)
                    else:
                        print(
                            f"Unhandled child ({sub_s['name']}) of parent ({s['name']} in {root_rel_path}"
                        )
            data_structures_dict[name] = {
                "methods": methods,
                "nested_data_structures": nested_data_structures,
            }
    if len(data_structures_dict) > 0:
        if structured_output:
            output = data_structures_dict
        else:
            output = "\nData structures to document in the code:\n\n"
            for n in data_structures_dict:
                output += f"- {n}\n"
    else:
        output = None

    return output


def rust_function_checker(
    code: str, root_rel_path: Path, structured_output: bool = True
) -> list[str] | str | None:
    symbols = extract_symbols_w_ctags(root_rel_path=root_rel_path, file_content=code)
    fn_list = []
    for s in symbols:
        if s["kind"] in RUST_FUNCTIONS and not s["name"].startswith("__anon"):
            fn_list.append(s["name"])
    if len(fn_list) > 0:
        if structured_output:
            output = fn_list
        else:
            output = "\nFunctions to document in the code:\n\n"
            for fn in fn_list:
                output += f"- {fn}\n"
    else:
        output = None
    return output


def rust_variables_checker(
    code: str, root_rel_path: Path, structured_output: bool = True
) -> list[str] | str | None:
    symbols = extract_symbols_w_ctags(root_rel_path=root_rel_path, file_content=code)
    v_list = [s["name"] for s in symbols if s["kind"] in RUST_VARIABLES]
    if len(v_list) > 0:
        if structured_output:
            output = v_list
        else:
            output = "\nVariables to document in the code:\n\n"
            for v in v_list:
                output += f"- {v}\n"
    else:
        output = None
    return output


def rust_macros_checker(
    code: str, root_rel_path: Path, structured_output: bool = True
) -> list[str] | str | None:
    symbols = extract_symbols_w_ctags(root_rel_path=root_rel_path, file_content=code)
    m_list = [s["name"] for s in symbols if s["kind"] in RUST_MACROS]
    if len(m_list) > 0:
        if structured_output:
            output = m_list
        else:
            output = "\nMacros to document in the code:\n\n"
            for v in m_list:
                output += f"- {v}\n"
    else:
        output = None
    return output


def rust_traits_checker(
    code: str, root_rel_path: Path, stuctured_output: bool = True
) -> list[str] | str | None:
    symbols = extract_symbols_w_ctags(root_rel_path=root_rel_path, file_content=code)
    t_list = [s["name"] for s in symbols if s["kind"] in RUST_TRAITS]
    if len(t_list) > 0:
        if stuctured_output:
            output = t_list
        else:
            output = "\nTraits to document in the code:\n\n"
            for t in t_list:
                output += f"- {t}\n"
    else:
        output = None
    return output


variables_dict_from_llm_rust = partial(
    variables_dict_from_llm,
    VARIABLES_FOUND_SYSTEM_PROMPT_JSON,
    VARIABLES_FOUND_USER_PROMPT,
)

macros_dict_from_llm_rust = partial(
    macros_dict_from_llm,
    MACROS_FOUND_SYSTEM_PROMPT_JSON,
    MACROS_FOUND_USER_PROMPT,
)

data_structure_dict_from_llm_rust = partial(
    data_structure_dict_from_llm,
    DATA_STRUCTURES_FOUND_SYSTEM_PROMPT_JSON,
    DATA_STRUCTURES_FOUND_USER_PROMPT,
    METHODS_FOUND_SYSTEM_PROMPT_JSON,
    METHODS_FOUND_USER_PROMPT,
    "::",
)

fn_dict_from_llm_rust = partial(
    fn_dict_from_llm,
    FUNCTIONS_FOUND_SYSTEM_PROMPT_JSON,
    FUNCTIONS_FOUND_USER_PROMPT,
)

traits_dict_from_llm_rust = partial(
    traits_dict_from_llm,
    TRAITS_FOUND_SYSTEM_PROMPT_JSON,
    TRAITS_FOUND_USER_PROMPT,
)

# variables_dict_from_llm_py_multi_prompt = partial(
#     variables_dict_from_llm_multi_prompt,
#     VARIABLES_FOUND_SYSTEM_PROMPT_JSON,
#     VARIABLES_FOUND_USER_PROMPT,
# )

# class_dict_from_llm_py_multi_prompt = partial(
#     classes_dict_from_llm_multi_prompt,
#     CLASSES_FOUND_SYSTEM_PROMPT_JSON,
#     CLASSES_FOUND_USER_PROMPT,
#     FUNCTIONS_FOUND_SYSTEM_PROMPT_JSON,
#     FUNCTIONS_FOUND_USER_PROMPT,
#     ".",
# )

# fn_dict_from_llm_py_multi_prompt = partial(
#     fn_dict_from_llm_multi_prompt,
#     FUNCTIONS_FOUND_SYSTEM_PROMPT_JSON,
#     FUNCTIONS_FOUND_USER_PROMPT,
# )
