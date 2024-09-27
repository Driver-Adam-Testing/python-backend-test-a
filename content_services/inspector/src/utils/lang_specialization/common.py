from enum import IntEnum
from pathlib import Path
from typing import Any, Self

import openai
from pydantic import BaseModel
from utils.codemap_ctags import extract_symbols_w_ctags
from utils.models import ChatOpenAI, OutputConfig, OutputConfigKind


class Lang(IntEnum):
    C = 0
    CPP = 1
    HEADER = 2
    PYTHON = 3
    VERILOG = 4
    DEFAULT = 5

    @classmethod
    def from_ext_and_source(cls, ext: str, source: str) -> Self:
        match ext:
            case ".c":
                return cls.C
            case ".cpp" | ".cc" | ".cxx" | ".c++":
                return cls.CPP
            case ".h" | ".hpp" | ".hh" | ".hxx" | ".h++":
                return cls.HEADER
            case ".py" | ".pyw" | ".pyi":
                return cls.PYTHON
            case ".v" | ".sv":  # TODO: seprately specialize SystemVerilog
                return cls.VERILOG
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
        print(
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
            output += f"\n---\n## {k}\n"
            output += f"- **Type**: `{v.type}`\n"
            output += f"- **Description**\n{v.description}\n"
            output += f"- **Use**\n{v.use}\n\n"

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
        try:
            content_raw = llm.generate_response(
                system_prompt=system_prompt,
                user_prompt=user_prompt_complete,
                output_cfg=OutputConfig(kind=OutputConfigKind.JSON_STRICT, payload=cls),
            )
        except openai.LengthFinishReasonError as _:
            return cls(
                type="", members=[], description="Data structure too large to process"
            )

        return cls.parse_raw(content_raw)


class DataStructureDict(BaseModel):
    data: dict[str, DataStructureData]

    def render_markdown(self) -> str:
        output = ""
        for k, v in self.data.items():
            output += f"\n---\n## {k}\n"
            output += f"### Type\n`{v.type}`\n"
            output += "### Members\n"
            if len(v.members) > 0:
                for m in v.members:
                    output += f"- `{m.name}`: {m.content}\n"
            else:
                output += "- None\n"
            output += f"\n### Description\n{v.description}\n\n"
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
    data: dict[str, FnData | list[FnData]]

    def render_markdown(self) -> str:
        output = ""
        for k, v in self.data.items():
            if isinstance(v, list):
                for fn in v:
                    output += render_function(k, fn, 3)
            else:
                output += render_function(k, v, 3)
        return output

    def __str__(self) -> str:
        return self.render_markdown()


def render_function(fn_name: str, fn_data: FnData, markdown_header_level: int) -> str:
    header = "#" * markdown_header_level
    output = ""
    output += f"\n---\n{header} {fn_name}\n"
    output += f"{fn_data.single_sentence}\n"
    output += "\n- **Inputs**:\n"
    if len(fn_data.inputs) > 0:
        for i in fn_data.inputs:
            output += f"    - `{i.name}`: {i.content}\n"
    else:
        output += "    - None\n"
    output += "\n- **Output**:\n"
    output += f"    - {fn_data.output}\n"
    output += "\n- **Logic and Control Flow**:\n"
    for item in fn_data.control_flow:
        output += f"    - {item}\n"
    output += "\n"
    return output


class ClassBaseData(BaseModel):
    type: str
    members: list[NamedContent]
    description: str

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
            f"{user_prompt}Class to document: {name}\n\nCode:\n\n{code}"
        )
        content_raw = llm.generate_response(
            system_prompt=system_prompt,
            user_prompt=user_prompt_complete,
            output_cfg=OutputConfig(kind=OutputConfigKind.JSON_STRICT, payload=cls),
        )

        return cls.parse_raw(content_raw)


class ClassData(BaseModel):
    base_data: ClassBaseData
    methods: dict[str, FnData]
    nested_classes: list[str]


class ClassDict(BaseModel):
    data: dict[str, ClassData]

    def render_markdown(self) -> str:
        output = ""
        for k, v in self.data.items():
            output += f"\n---\n---\n### {k}\n"
            output += f"- **Type**: `{v.base_data.type}`\n"
            output += f"\n- **Description**: {v.base_data.description}\n\n"
            output += "\n- **Members**:\n"
            non_dupe_members = 0
            if len(v.base_data.members) > 0:
                for m in v.base_data.members:
                    if m.name not in v.methods and m.name not in v.nested_classes:
                        output += f"    - `{m.name}`: {m.content}\n"
                        non_dupe_members += 1
            if non_dupe_members == 0:
                output += "    - None\n"
            output += "\n**Methods**\n"
            if len(v.methods) > 0:
                for n, m in v.methods.items():
                    output += render_function(n, m, 4)
            else:
                output += "    - None\n"
            if len(v.nested_classes) > 0:
                output += "\n**Nested Classes**:\n"
                for n in v.nested_classes:
                    output += f"    - {n}\n"

        return output

    def __str__(self) -> str:
        return self.render_markdown()


MAX_VARIABLES_TO_DOCUMENT = 100
MAX_DATA_STRUCTURES_TO_DOCUMENT = 100
MAX_CLASSES_TO_DOCUMENT = 100
MAX_FUNCTIONS_TO_DOCUMENT = 100


def variables_dict_from_llm(
    system_prompt: str,
    user_prompt: str,
    llm: ChatOpenAI,
    vars_list: list[str],
    code: str,
) -> VariableDict:
    vars_dict = {
        v: VariableData.from_llm(
            llm=llm,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            var_name=v,
            code=code,
        )
        for v in vars_list[:MAX_VARIABLES_TO_DOCUMENT]
    }
    return VariableDict(data=vars_dict)


def data_structure_dict_from_llm(
    system_prompt: str, user_prompt: str, llm: ChatOpenAI, ds_list: list[str], code: str
) -> DataStructureDict:
    ds_dict = {
        ds: DataStructureData.from_llm(
            llm=llm,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            ds_name=ds,
            code=code,
        )
        for ds in ds_list[:MAX_DATA_STRUCTURES_TO_DOCUMENT]
    }
    return DataStructureDict(data=ds_dict)


def fn_dict_from_llm(
    system_prompt: str,
    user_prompt: str,
    llm: ChatOpenAI,
    fn_list: list[str | dict],
    code: str,
) -> FnDict:
    fn_dict = {}
    for fn in fn_list[:MAX_FUNCTIONS_TO_DOCUMENT]:
        if isinstance(fn, str):
            fn_dict[fn] = FnData.from_llm(
                llm=llm,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                fn_name=fn,
                code=code,
            )
        elif isinstance(fn, dict):
            fn_name = fn["name"]
            fn_start_line = fn["line"]
            fn_end_line = fn["end"]
            code_lines = code.splitlines()
            fn_code = "\n".join(code_lines[fn_start_line - 1 : fn_end_line + 1])
            if fn_name not in fn_dict:
                fn_dict[fn_name] = []
            fn_dict[fn_name].append(
                FnData.from_llm(
                    llm=llm,
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    fn_name=fn_name,
                    code=fn_code,
                )
            )
    return FnDict(data=fn_dict)


def class_dict_from_llm(
    system_prompt_class: str,
    user_prompt_class: str,
    system_prompt_fn: str,
    user_prompt_fn: str,
    class_fn_delimiter: str,
    llm: ChatOpenAI,
    class_dict_raw: dict[str, dict[str, Any]],
    code: str,
) -> ClassDict:
    class_dict_documented = {}
    for name, cls_data in class_dict_raw.items():
        class_base = ClassBaseData.from_llm(
            system_prompt=system_prompt_class,
            user_prompt=user_prompt_class,
            llm=llm,
            name=name,
            code=code,
        )
        methods = {}
        nested_classes = []
        for member_fn in cls_data["methods"]:
            # TODO: handle overloaded function names here.
            fn_data = FnData.from_llm(
                system_prompt=system_prompt_fn,
                user_prompt=user_prompt_fn,
                llm=llm,
                fn_name=member_fn["name"],
                code=code,
            )
            function_name = (
                member_fn["scope"].split(class_fn_delimiter)[-1]
                + class_fn_delimiter
                + member_fn["name"]
            )
            methods[function_name] = fn_data

        for nested_class in cls_data["nested_classes"]:
            nested_classes.append(nested_class["name"])

        class_data = ClassData(
            base_data=class_base,
            methods=methods,
            nested_classes=nested_classes,
        )
        class_dict_documented[name] = class_data
    return ClassDict(data=class_dict_documented)


PADDING_LINES_TOP = 100
PADDING_LINES_BOTTOM = 100
SYMBOL_MAX_CHUNK_SIZE = 64_000
SYMBOL_CHUNK_OVERLAP = 1_000


def symbols_dict_from_llm_multi_prompt(
    llm: ChatOpenAI,
    symbols_list: list[str],
    code: str,
    root_rel_path: Path,
    data_class: VariableData | DataStructureData | FnData,
    system_prompt: str,
    user_prompt: str,
    max_symbols_to_document: int,
) -> dict[str, VariableData | DataStructureData | FnData]:
    from shared.chunking.text_splitter import split_text

    symbols = extract_symbols_w_ctags(root_rel_path=root_rel_path, file_content=code)
    symbols_dict = {}
    for symbol in symbols:
        for s in symbols_list:
            if symbol["name"] == s:
                start_line = symbol["line"]
                end_line = symbol.get("end", symbol["line"])
                symbol_code = "\n".join(
                    code.splitlines()[
                        start_line - PADDING_LINES_TOP : end_line + PADDING_LINES_BOTTOM
                    ]
                )
                # Catch edge case where a single symbol is too large for context
                # This documents symbol based on first chunk only
                # TODO: consider compression loop here? There is some intricacy here to deal with.
                code_chunks = split_text(
                    text=symbol_code,
                    chunk_size=SYMBOL_MAX_CHUNK_SIZE,
                    chunk_overlap=SYMBOL_CHUNK_OVERLAP,
                )
                if len(code_chunks) > 1:
                    symbol_code = code_chunks[0].text
                symbols_dict[s] = data_class.from_llm(
                    llm,
                    system_prompt,
                    user_prompt,
                    s,
                    symbol_code,
                )
                break
        if len(symbols_dict) >= max_symbols_to_document:
            break
    return symbols_dict


def variables_dict_from_llm_multi_prompt(
    system_prompt: str,
    user_prompt: str,
    llm: ChatOpenAI,
    variables_list: list[str],
    code: str,
    root_rel_path: Path,
) -> VariableDict:
    symbols_dict = symbols_dict_from_llm_multi_prompt(
        llm,
        variables_list,
        code,
        root_rel_path,
        VariableData,
        system_prompt,
        user_prompt,
        MAX_VARIABLES_TO_DOCUMENT,
    )
    return VariableDict(data=symbols_dict)


def data_structure_dict_from_llm_multi_prompt(
    system_prompt: str,
    user_prompt: str,
    llm: ChatOpenAI,
    data_structures_list: list[str],
    code: str,
    root_rel_path: Path,
) -> DataStructureDict:
    symbols_dict = symbols_dict_from_llm_multi_prompt(
        llm,
        data_structures_list,
        code,
        root_rel_path,
        DataStructureData,
        system_prompt,
        user_prompt,
        MAX_DATA_STRUCTURES_TO_DOCUMENT,
    )
    return DataStructureDict(data=symbols_dict)


def classes_dict_from_llm_multi_prompt(
    system_prompt: str,
    user_prompt: str,
    llm: ChatOpenAI,
    classes_list: list[str],
    code: str,
    root_rel_path: Path,
) -> ClassDict:
    symbols_dict = symbols_dict_from_llm_multi_prompt(
        llm,
        classes_list,
        code,
        root_rel_path,
        ClassData,
        system_prompt,
        user_prompt,
        MAX_CLASSES_TO_DOCUMENT,
    )
    return ClassDict(data=symbols_dict)


def fn_dict_from_llm_multi_prompt(
    system_prompt: str,
    user_prompt: str,
    llm: ChatOpenAI,
    functions_list: list[str],
    code: str,
    root_rel_path: Path,
) -> FnDict:
    symbols_dict = symbols_dict_from_llm_multi_prompt(
        llm,
        functions_list,
        code,
        root_rel_path,
        FnData,
        system_prompt,
        user_prompt,
        MAX_FUNCTIONS_TO_DOCUMENT,
    )
    return FnDict(data=symbols_dict)
