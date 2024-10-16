from functools import partial
from pathlib import Path
from typing import Any, Self

import openai
from pydantic import BaseModel
from utils.codemap_ctags import extract_symbols_w_ctags
from utils.models import ChatOpenAI, OutputConfig, OutputConfigKind

from .common import (
    NamedContent,
)

JAVA_INTERFACES = {"interface"}
JAVA_CLASSES = {"class"}
JAVA_METHODS = {"method"}
JAVA_FIELDS = {"field"}
JAVA_ENUMS = {"enum"}

SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_JAVA = """
You are an expert Java programmer and a software engineering documentation expert. You write detailed documentation to explain code written in Java.

You are skilled at explaining technical details as well as recognize and articulate the key conceptual components and purpose of software.
"""

SOURCE_CODE_SMALL_SYSTEM_PROMPT_GENERAL_JAVA = """
You are an expert Java programmer and a software engineering documentation expert. You write detailed documentation to explain code written in Java.

You are skilled at explaining technical details as well as recognize and articulate the key conceptual components and purpose of software.

You specialize in effectively describing small and short source code files. Your goal is to be terse and clear, since the source code you are describing is small and simple.
"""

SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT = """
You will be given the content of a source code file. In 1 or 2 paragraphs, explain the purpose of the file.

When writing your paragraphs, do not use speculative language.

When writing your paragraphs, consider questions like the following. You do not need to explicitly state these ideas, they are just given as examples of the kind of information to provide:

- Does this code provide narrow or broad functionality?
- What are the most important technical components?
- Is this code a collection of many different components? If so, what is the common theme or purpose?
- Does it define public APIs or external interfaces?
"""

SOURCE_CODE_SMALL_PURPOSE_USER_PROMPT = """
In a single paragraph of 3 to 5 sentences, explain the purpose of the code provided below. Consider questions such as the following when providing your output:

- Does this code provide narrow or broad functionality?
"""

INTERFACES_FOUND_SYSTEM_PROMPT_JSON = """
You are an expert Java programmer and a software engineering documentation expert. You write detailed documentation to explain code written in Java.

You focus on writing technical documentation for interfaces in Java. You are skilled at explaining technical details as well as recognizing and articulating the key conceptual components and purpose of software.

You will be given the name of an interface to document and the source code where the interface is defined.

Your job is to describe the interface. **Always respond using exactly the following JSON schema**:
{
    "description": <one paragraph description of the interface>,
    "interfaces_extended": [<list of interfaces this interface extends if any>],
}

Return JSON according to the schema above. Do not use the format ```json ... ```, just return the JSON data.
"""

INTERFACES_FOUND_USER_PROMPT = """
Summarize the interface in the code provided below.

- When describing an important interface, provide detail that matches the complexity of the interface. Large and complex interfaces should get longer explanations, while small ones a single sentence.
"""

INTERFACES_NONE_CONTENT = "\n---\nNo interfaces defined in this file."

CLASSES_FOUND_SYSTEM_PROMPT_JSON = """
You are an expert Java programmer and a software engineering documentation expert. You write detailed documentation to explain code written in Java.

You focus on writing technical documentation for classes in Java. You are skilled at explaining technical details as well as recognizing and articulating the key conceptual components and purpose of software.

You will be given the name of an class to document and the source code where the class is defined.

Your job is to describe the class. **Always respond using exactly the following JSON schema**:
{
    "description": <one paragraph description of the class>,
    "interfaces_implemented": [<list of interfaces this class implements if any>],
    "classes_extended": [<list of classes this class extends if any>],
    "modifiers": [<list of modifiers of the class, e.g. public, private, protected, abstract, or final. Can be an empty list.>],
}

Return JSON according to the schema above. Do not use the format ```json ... ```, just return the JSON data.
"""

CLASSES_FOUND_USER_PROMPT = """
Summarize the class in the code provided below.

- When describing an important class, provide detail that matches the complexity of the class. Large and complex class should get longer explanations, while small ones a single sentence.
"""

CLASSES_NONE_CONTENT = "\n---\nNo classes defined in this file."

METHODS_FOUND_SYSTEM_PROMPT_JSON = """
You are an expert Java programmer and a software engineering documentation expert. You write detailed documentation to explain code written in Java.

You focus on writing technical documentation for class methods. You are skilled at explaining technical details as well as recognizing and articulating the key conceptual components and purpose of software.

You will be given the name of a method to document and the source code where the method is defined.

Your job is to describe the method. **Always respond using exactly the following JSON schema**:
{
    "single_sentence": <terse single sentence description of the method>,
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
    "output": <description of output>,
    "modifiers": [<list of modifiers of the method, e.g. public, private, protected, abstract, final, static, transient, synchronized, or volatile. Can be an empty list.>],
}

Return JSON according to the schema above. Do not use the format ```json ... ```, just return the JSON data.
"""

METHODS_FOUND_USER_PROMPT = """
Summarize the method in the code provided below. Describe the inputs, control flow and logic, and output.

- When describing a method, provide detail that matches the complexity of the method body. Large and complex method should get longer explanations, while small ones much less.
"""

METHODS_NONE_CONTENT = "\n---\nNo methods defined in this file."

FIELDS_FOUND_SYSTEM_PROMPT_JSON = """
You are an expert Java programmer and a software engineering documentation expert. You write detailed documentation to explain code written in Java.

You focus on writing technical documentation for fields. You are skilled at explaining technical details as well as recognizing and articulating the key conceptual components and purpose of software.

You will be given the name of a field to document and the source code where the field is defined.

Your job is to describe the field. **Always respond using exactly the following JSON schema**:
{
    "type": <type of the field>,
    "description": <1 to 3 sentence description of the field>,
    "use": <Terse 1 sentence description of how this field is used>,
    "modifiers": [<list of modifiers of the method, e.g. public, private, protected, abstract, final, static, transient, synchronized, or volatile. Can be an empty list.>],
}

Return JSON according to the schema above. Do not use the format ```json ... ```, just return the JSON data.
"""

FIELDS_FOUND_USER_PROMPT = """
Summarize the field in the code provided below.

- When describing a field, provide detail that matches the complexity of the field. Large and complex global fields should get longer explanations, while small ones much less.
"""

FIELDS_NONE_CONTENT = "\n---\nNo fields defined in this file."


class JavaMethodData(BaseModel):
    single_sentence: str
    inputs: list[NamedContent]
    control_flow: list[str]
    output: str
    modifiers: list[str]

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
            f"{user_prompt}Method to document: {fn_name}\n\nCode:\n\n{code}"
        )
        try:
            content_raw = llm.generate_response(
                system_prompt=system_prompt,
                user_prompt=user_prompt_complete,
                output_cfg=OutputConfig(kind=OutputConfigKind.JSON_STRICT, payload=cls),
            )
        except openai.LengthFinishReasonError as _:
            print("LengthFinishReasonError caught")
            return cls(
                single_sentence="Method too large to process",
                inputs=[],
                control_flow=[],
                output="",
            )

        return cls.parse_raw(content_raw)


def render_method(
    method_name: str, method_data: JavaMethodData, markdown_header_level: int
) -> str:
    header = "#" * markdown_header_level
    output = ""
    output += f"\n---\n{header} {method_name}\n"
    output += f"{method_data.single_sentence}\n"
    if len(method_data.modifiers) > 0:
        output += "\n- **Modifiers**:\n"
        for m in method_data.modifiers:
            output += f"    - {m}\n"

    output += "\n- **Inputs**:\n"
    if len(method_data.inputs) > 0:
        for i in method_data.inputs:
            output += f"    - `{i.name}`: {i.content}\n"
    else:
        output += "    - None\n"
    output += "\n- **Output**:\n"
    output += f"    - {method_data.output}\n"
    output += "\n- **Logic and Control Flow**:\n"
    for item in method_data.control_flow:
        output += f"    - {item}\n"
    output += "\n"
    return output


class JavaMethodDict(BaseModel):
    data: dict[str, JavaMethodData | list[JavaMethodData]]

    def render_markdown(self) -> str:
        output = ""
        for k, v in self.data.items():
            if isinstance(v, list):
                for fn in v:
                    output += render_method(k, fn, 3)
            else:
                output += render_method(k, v, 3)
        return output

    def __str__(self) -> str:
        return self.render_markdown()


class JavaFieldData(BaseModel):
    type: str
    description: str
    use: str
    modifiers: list[str]

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
            f"{user_prompt}Field to document: {var_name}\n\nCode:\n\n{code}"
        )
        content_raw = llm.generate_response(
            system_prompt=system_prompt,
            user_prompt=user_prompt_complete,
            output_cfg=OutputConfig(kind=OutputConfigKind.JSON_STRICT, payload=cls),
        )

        return cls.parse_raw(content_raw)


class JavaFieldDict(BaseModel):
    data: dict[str, JavaFieldData]

    def render_markdown(self) -> str:
        output = ""
        for k, v in self.data.items():
            output += f"\n---\n## {k}\n"
            output += f"- **Type**: `{v.type}`\n"
            output += f"- **Description**\n{v.description}\n"
            output += f"- **Use**\n{v.use}\n\n"
            if len(v.modifiers) > 0:
                output += "- **Modifiers**:\n"
                for m in v.modifiers:
                    output += f"    - {m}\n"

        return output

    def __str__(self) -> str:
        return self.render_markdown()


class JavaClassBaseData(BaseModel):
    description: str
    interfaces_implemented: list[str]
    classes_extended: list[str]
    modifers: list[str]

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
        try:
            content_raw = llm.generate_response(
                system_prompt=system_prompt,
                user_prompt=user_prompt_complete,
                output_cfg=OutputConfig(kind=OutputConfigKind.JSON_STRICT, payload=cls),
            )
        except openai.LengthFinishReasonError as _:
            print("LengthFinishReasonError caught")
            return cls(
                type="",
                members=[],
                description="Object too large to process",
                inherits_from=[],
            )

        return cls.parse_raw(content_raw)


class JavaClassData(BaseModel):
    base_data: JavaClassBaseData
    methods: dict[str, JavaMethodData | list[JavaMethodData]]
    fields: dict[str, JavaFieldData | list[JavaFieldData]]
    nested_classes: list[str]
    nested_interfaces: list[str]


def render_class_base_data(class_data: JavaClassData) -> str:
    output = ""
    if len(class_data.base_data.modifers) > 0:
        output += "- **Modifiers**:\n"
        for m in class_data.base_data.modifers:
            output += f"    - {m}\n"
    if len(class_data.base_data.classes_extended) > 0:
        output += "\n- **Extends**:\n"
        for i in class_data.base_data.classes_extended:
            output += f"    - `{i}`\n"
    if len(class_data.base_data.interfaces_implemented) > 0:
        output += "\n- **Implements**:\n"
        for i in class_data.base_data.interfaces_implemented:
            output += f"    - `{i}`\n"
    output += f"\n- **Description**: {class_data.base_data.description}\n\n"
    return output


class JavaClassDict(BaseModel):
    data: dict[str, JavaClassData]

    def render_markdown(self) -> str:
        output = "\n---"
        for k, v in self.data.items():
            output += f"\n### {k}\n"
            output += render_class_base_data(v)
            if len(v.methods) > 0:
                output += "\n**Methods**\n"
                for n, m in v.methods.items():
                    # Case of potentially overloaded method.
                    if isinstance(m, list):
                        for sub_m in m:
                            output += render_method(n, sub_m, 4)
                    else:
                        output += render_method(n, m, 4)
            if len(v.fields) > 0:
                output += "\n**Fields**\n"
                for n, f in v.fields.items():
                    output += f"\n---\n#### {n}\n"
                    output += f"- **Type**: `{f.type}`\n"
                    if len(f.modifiers) > 0:
                        output += "- **Modifiers**:\n"
                        for m in f.modifiers:
                            output += f"    - {m}\n"
                    output += f"- **Description**\n{f.description}\n"
                    output += f"- **Use**\n{f.use}\n\n"
            if len(v.nested_classes) > 0:
                output += "\n**Nested Classes**:\n"
                for n in v.nested_classes:
                    output += f"    - {n}\n"
            if len(v.nested_interfaces) > 0:
                output += "\n**Nested Interfaces**:\n"
                for n in v.nested_interfaces:
                    output += f"    - {n}\n"
            output += "\n---\n---"

        return output

    def __str__(self) -> str:
        return self.render_markdown()


class JavaInterfaceBaseData(BaseModel):
    description: str
    interfaces_extended: list[str]

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
            f"{user_prompt}Interface to document: {name}\n\nCode:\n\n{code}"
        )
        try:
            content_raw = llm.generate_response(
                system_prompt=system_prompt,
                user_prompt=user_prompt_complete,
                output_cfg=OutputConfig(kind=OutputConfigKind.JSON_STRICT, payload=cls),
            )
        except openai.LengthFinishReasonError as _:
            print("LengthFinishReasonError caught")
            return cls(
                type="",
                members=[],
                description="Object too large to process",
                inherits_from=[],
            )

        return cls.parse_raw(content_raw)


class JavaInterfaceData(BaseModel):
    base_data: JavaInterfaceBaseData
    methods: dict[str, JavaMethodData | list[JavaMethodData]]
    fields: dict[str, JavaFieldData | list[JavaFieldData]]
    nested_classes: list[str]
    nested_interfaces: list[str]


def render_interface_base_data(interface_data: JavaInterfaceData) -> str:
    output = ""
    if len(interface_data.base_data.interfaces_extended) > 0:
        output += "\n- **Extends**:\n"
        for i in interface_data.base_data.interfaces_extended:
            output += f"    - `{i}`\n"
    output += f"\n- **Description**: {interface_data.base_data.description}\n\n"
    return output


class JavaInterfaceDict(BaseModel):
    data: dict[str, JavaInterfaceData]

    def render_markdown(self) -> str:
        output = "\n---"
        for k, v in self.data.items():
            output += f"\n### {k}\n"
            output += render_interface_base_data(v)
            if len(v.methods) > 0:
                # TODO: perhaps don't give much documentation
                # for methods in interface as they are abstract, unless default...
                output += "\n**Methods**\n"
                for n, m in v.methods.items():
                    # Case of potentially overloaded method.
                    if isinstance(m, list):
                        for sub_m in m:
                            output += render_method(n, sub_m, 4)
                    else:
                        output += render_method(n, m, 4)
            if len(v.fields) > 0:
                output += "\n**Fields**\n"
                for n, f in v.fields.items():
                    output += f"\n---\n#### {n}\n"
                    output += f"- **Type**: `{f.type}`\n"
                    if len(f.modifiers) > 0:
                        output += "- **Modifiers**:\n"
                        for m in f.modifiers:
                            output += f"    - {m}\n"
                    output += f"- **Description**\n{f.description}\n"
                    output += f"- **Use**\n{f.use}\n\n"
            if len(v.nested_classes) > 0:
                output += "\n**Nested Classes**:\n"
                for n in v.nested_classes:
                    output += f"    - {n}\n"
            if len(v.nested_interfaces) > 0:
                output += "\n**Nested Interfaces**:\n"
                for n in v.nested_interfaces:
                    output += f"    - {n}\n"
            output += "\n---\n---"

        return output

    def __str__(self) -> str:
        return self.render_markdown()


def java_class_checker(
    code: str, root_rel_path: Path, structured_output: bool = True
) -> list[dict] | str | None:
    symbols = extract_symbols_w_ctags(root_rel_path=root_rel_path, file_content=code)
    classes_dict = {
        s["name"]: {
            "methods": [],
            "nested_classes": [],
            "nested_interfaces": [],
            "fields": [],
        }
        for s in symbols
        if s["kind"] in JAVA_CLASSES
    }
    for s in symbols:
        if (
            (s.get("scope"))
            and (s["kind"] in JAVA_METHODS)
            and s["scopeKind"] in JAVA_CLASSES
        ):
            classes_dict[s["scope"].split(".")[-1]]["methods"].append(s)
        elif (
            (s.get("scope"))
            and not s["name"].startswith("__anon")
            and (s["kind"] in JAVA_CLASSES)
            and (s["scopeKind"] in JAVA_CLASSES)
        ):
            classes_dict[s["scope"].split(".")[-1]]["nested_classes"].append(s)
        elif (
            (s.get("scope"))
            and (s["kind"] in JAVA_INTERFACES)
            and (s["scopeKind"] in JAVA_CLASSES)
        ):
            classes_dict[s["scope"].split(".")[-1]]["nested_interfaces"].append(s)
        elif (
            (s.get("scope"))
            and (s["kind"] in JAVA_FIELDS)
            and (s["scopeKind"] in JAVA_CLASSES)
        ):
            classes_dict[s["scope"].split(".")[-1]]["fields"].append(s)

    output = None
    if len(classes_dict) > 0:
        if structured_output:
            output = classes_dict
        else:
            output = "\nClasses to document in the code:\n\n"
            for n in classes_dict:
                output += f"- {n}\n"
    return output


def java_interface_checker(
    code: str, root_rel_path: Path, structured_output: bool = True
) -> list[dict] | str | None:
    symbols = extract_symbols_w_ctags(root_rel_path=root_rel_path, file_content=code)
    interfaces_dict = {
        s["name"]: {
            "methods": [],
            "nested_classes": [],
            "nested_interfaces": [],
            "fields": [],
        }
        for s in symbols
        if s["kind"] in JAVA_INTERFACES
    }
    for s in symbols:
        if (
            (s.get("scope"))
            and (s["kind"] in JAVA_METHODS)
            and s["scopeKind"] in JAVA_INTERFACES
        ):
            interfaces_dict[s["scope"].split(".")[-1]]["methods"].append(s)
        elif (
            (s.get("scope"))
            and not s["name"].startswith("__anon")
            and (s["kind"] in JAVA_INTERFACES)
            and (s["scopeKind"] in JAVA_INTERFACES)
        ):
            interfaces_dict[s["scope"].split(".")[-1]]["nested_classes"].append(s)
        elif (
            (s.get("scope"))
            and (s["kind"] in JAVA_INTERFACES)
            and (s["scopeKind"] in JAVA_INTERFACES)
        ):
            interfaces_dict[s["scope"].split(".")[-1]]["nested_interfaces"].append(s)
        elif (
            (s.get("scope"))
            and (s["kind"] in JAVA_FIELDS)
            and (s["scopeKind"] in JAVA_INTERFACES)
        ):
            interfaces_dict[s["scope"].split(".")[-1]]["fields"].append(s)

    output = None
    if len(interfaces_dict) > 0:
        if structured_output:
            output = interfaces_dict
        else:
            output = "\nClasses to document in the code:\n\n"
            for n in interfaces_dict:
                output += f"- {n}\n"
    return output


def java_class_dict_from_llm(
    system_prompt_class: str,
    user_prompt_class: str,
    system_prompt_fn: str,
    user_prompt_fn: str,
    system_prompt_field: str,
    user_prompt_field: str,
    class_fn_delimiter: str,
    llm: ChatOpenAI,
    class_dict_raw: dict[str, dict[str, Any]],
    code: str,
) -> JavaClassDict:
    class_dict_documented = {}
    global_method_counts = {}
    for _, cls_data in class_dict_raw.items():
        for m in cls_data["methods"]:
            name = m["name"]
            global_method_counts[name] = global_method_counts.get(name, 0) + 1
    for cls_name, cls_data in class_dict_raw.items():
        class_base = JavaClassBaseData.from_llm(
            system_prompt=system_prompt_class,
            user_prompt=user_prompt_class,
            llm=llm,
            name=cls_name,
            code=code,
        )
        methods = {}
        fields = {}
        nested_classes = []
        nested_interfaces = []
        for m in cls_data["methods"]:
            m_name = m["name"]
            scoped_name = cls_name + class_fn_delimiter + m_name
            # More than one method with the same name in the file: cut scope for LLM.
            if global_method_counts[m_name] > 1:
                m_start_line = m["line"]
                # TODO: Better solution if end line is not present.
                m_end_line = m.get("end")
                code_lines = code.splitlines()
                m_code = "\n".join(code_lines[m_start_line - 1 : m_end_line + 1])
                # Use list to handle method overloading, if present.
                if scoped_name not in methods:
                    methods[scoped_name] = []
                methods[scoped_name].append(
                    JavaMethodData.from_llm(
                        system_prompt=system_prompt_fn,
                        user_prompt=user_prompt_fn,
                        llm=llm,
                        fn_name=m_name,
                        code=m_code,
                    )
                )
            else:
                m_data = JavaMethodData.from_llm(
                    system_prompt=system_prompt_fn,
                    user_prompt=user_prompt_fn,
                    llm=llm,
                    fn_name=m_name,
                    code=code,
                )
                methods[scoped_name] = m_data
        for f in cls_data["fields"]:
            f_name = f["name"]
            scoped_name = cls_name + class_fn_delimiter + f_name
            f_data = JavaFieldData.from_llm(
                system_prompt=system_prompt_field,
                user_prompt=user_prompt_field,
                llm=llm,
                var_name=f_name,
                code=code,
            )
            fields[scoped_name] = f_data

        for nested_class in cls_data["nested_classes"]:
            nested_classes.append(nested_class["name"])

        for nested_interface in cls_data["nested_interfaces"]:
            nested_interfaces.append(nested_interface["name"])

        class_data = JavaClassData(
            base_data=class_base,
            methods=methods,
            fields=fields,
            nested_classes=nested_classes,
            nested_interfaces=nested_interfaces,
        )
        class_dict_documented[cls_name] = class_data

    return JavaClassDict(data=class_dict_documented)


BLIND_ADVANCE_IF_NO_END_LINE = 200
PADDING_LINES_TOP = 100
PADDING_LINES_BOTTOM = 100
SYMBOL_MAX_CHUNK_SIZE = 64_000
SYMBOL_CHUNK_OVERLAP = 1_000


def java_class_dict_from_llm_multi_prompt(
    system_prompt_class: str,
    user_prompt_class: str,
    system_prompt_fn: str,
    user_prompt_fn: str,
    system_prompt_field: str,
    user_prompt_field: str,
    class_fn_delimiter: str,
    llm: ChatOpenAI,
    class_dict_raw: dict[str, dict[str, Any]],
    code: str,
    root_rel_path: Path,
) -> JavaClassDict:
    from shared.chunking.text_splitter import split_text

    symbols = extract_symbols_w_ctags(root_rel_path=root_rel_path, file_content=code)
    class_dict_documented = {}
    global_method_counts = {}
    for _, cls_data in class_dict_raw.items():
        for m in cls_data["methods"]:
            name = m["name"]
            global_method_counts[name] = global_method_counts.get(name, 0) + 1

    for symbol in symbols:
        for cls_name, cls_data in class_dict_raw.items():
            if symbol["name"] == cls_name:
                start_line = symbol["line"]
                end_line = symbol.get(
                    "end", symbol["line"] + BLIND_ADVANCE_IF_NO_END_LINE
                )
                class_code = "\n".join(code.splitlines()[start_line - 1 : end_line])
                code_chunks = split_text(
                    text=class_code,
                    chunk_size=SYMBOL_MAX_CHUNK_SIZE,
                    chunk_overlap=SYMBOL_CHUNK_OVERLAP,
                )
                if len(code_chunks) == 1:
                    class_dict_documented = java_class_dict_from_llm(
                        system_prompt_class=system_prompt_class,
                        user_prompt_class=user_prompt_class,
                        system_prompt_fn=system_prompt_fn,
                        user_prompt_fn=user_prompt_fn,
                        system_prompt_field=system_prompt_field,
                        user_prompt_field=user_prompt_field,
                        class_fn_delimiter=class_fn_delimiter,
                        llm=llm,
                        class_dict_raw={cls_name: cls_data},
                        code=class_code,
                    ).data[cls_name]
                elif len(code_chunks) > 1:
                    class_base = JavaClassBaseData.from_llm(
                        system_prompt=system_prompt_class,
                        user_prompt=user_prompt_class,
                        llm=llm,
                        name=cls_name,
                        code=code_chunks[0].text,
                    )
                    methods = {}
                    fields = {}
                    nested_classes = []
                    nested_interfaces = []
                    for m in cls_data["methods"]:
                        m_name = m["name"]
                        scoped_name = cls_name + class_fn_delimiter + m_name
                        m_start_line = m["line"]
                        m_end_line = m.get(
                            "end", m_start_line + BLIND_ADVANCE_IF_NO_END_LINE
                        )
                        m_code = "\n".join(
                            code.splitlines()[m_start_line - 1 : m_end_line]
                        )
                        # More than one method with the same name in the file: cut scope for LLM.
                        if global_method_counts[m_name] > 1:
                            # Use list to handle method overloading, if present.
                            if scoped_name not in methods:
                                methods[scoped_name] = []
                            methods[scoped_name].append(
                                JavaMethodData.from_llm(
                                    system_prompt=system_prompt_fn,
                                    user_prompt=user_prompt_fn,
                                    llm=llm,
                                    fn_name=m_name,
                                    code=m_code,
                                )
                            )
                        else:
                            m_data = JavaMethodData.from_llm(
                                system_prompt=system_prompt_fn,
                                user_prompt=user_prompt_fn,
                                llm=llm,
                                fn_name=m_name,
                                code=m_code,
                            )
                            methods[scoped_name] = m_data
                    for f in cls_data["fields"]:
                        f_name = f["name"]
                        f_start_line = f["line"] - PADDING_LINES_TOP
                        f_end_line = f.get("end", f["line"] + PADDING_LINES_BOTTOM)
                        f_code = "\n".join(code.splitlines()[f_start_line:f_end_line])
                        scoped_name = cls_name + class_fn_delimiter + f_name
                        f_data = JavaFieldData.from_llm(
                            system_prompt=system_prompt_field,
                            user_prompt=user_prompt_field,
                            llm=llm,
                            var_name=f_name,
                            code=f_code,
                        )
                        fields[scoped_name] = f_data

                    for nested_class in cls_data["nested_classes"]:
                        nested_classes.append(nested_class["name"])

                    for nested_interface in cls_data["nested_interfaces"]:
                        nested_interfaces.append(nested_interface["name"])

                    class_data = JavaClassData(
                        base_data=class_base,
                        methods=methods,
                        fields=fields,
                        nested_classes=nested_classes,
                        nested_interfaces=nested_interfaces,
                    )
                    class_dict_documented[cls_name] = class_data

    return JavaClassDict(data=class_dict_documented)


def java_interface_dict_from_llm(
    system_prompt_class: str,
    user_prompt_class: str,
    system_prompt_fn: str,
    user_prompt_fn: str,
    system_prompt_field: str,
    user_prompt_field: str,
    class_fn_delimiter: str,
    llm: ChatOpenAI,
    interface_dict_raw: dict[str, dict[str, Any]],
    code: str,
) -> JavaInterfaceDict:
    interface_dict_documented = {}
    global_method_counts = {}
    for _, cls_data in interface_dict_raw.items():
        for m in cls_data["methods"]:
            name = m["name"]
            global_method_counts[name] = global_method_counts.get(name, 0) + 1
    for cls_name, cls_data in interface_dict_raw.items():
        class_base = JavaInterfaceBaseData.from_llm(
            system_prompt=system_prompt_class,
            user_prompt=user_prompt_class,
            llm=llm,
            name=cls_name,
            code=code,
        )
        methods = {}
        fields = {}
        nested_classes = []
        nested_interfaces = []
        for m in cls_data["methods"]:
            m_name = m["name"]
            scoped_name = cls_name + class_fn_delimiter + m_name
            # More than one method with the same name in the file: cut scope for LLM.
            if global_method_counts[m_name] > 1:
                m_start_line = m["line"]
                # TODO: Better solution if end line is not present.
                m_end_line = m.get("end")
                code_lines = code.splitlines()
                m_code = "\n".join(code_lines[m_start_line - 1 : m_end_line + 1])
                # Use list to handle method overloading, if present.
                if scoped_name not in methods:
                    methods[scoped_name] = []
                methods[scoped_name].append(
                    JavaMethodData.from_llm(
                        system_prompt=system_prompt_fn,
                        user_prompt=user_prompt_fn,
                        llm=llm,
                        fn_name=m_name,
                        code=m_code,
                    )
                )
            else:
                m_data = JavaMethodData.from_llm(
                    system_prompt=system_prompt_fn,
                    user_prompt=user_prompt_fn,
                    llm=llm,
                    fn_name=m_name,
                    code=code,
                )
                methods[scoped_name] = m_data
        for f in cls_data["fields"]:
            f_name = f["name"]
            scoped_name = cls_name + class_fn_delimiter + m_name
            f_data = JavaFieldData.from_llm(
                system_prompt=system_prompt_field,
                user_prompt=user_prompt_field,
                llm=llm,
                var_name=f_name,
                code=code,
            )
            fields[scoped_name] = f_data

        for nested_class in cls_data["nested_classes"]:
            nested_classes.append(nested_class["name"])

        for nested_interface in cls_data["nested_interfaces"]:
            nested_interfaces.append(nested_interface["name"])

        class_data = JavaInterfaceData(
            base_data=class_base,
            methods=methods,
            fields=fields,
            nested_classes=nested_classes,
            nested_interfaces=nested_interfaces,
        )
        interface_dict_documented[cls_name] = class_data

    return JavaInterfaceDict(data=interface_dict_documented)


def java_interface_dict_from_llm_multi_prompt(
    system_prompt_class: str,
    user_prompt_class: str,
    system_prompt_fn: str,
    user_prompt_fn: str,
    system_prompt_field: str,
    user_prompt_field: str,
    class_fn_delimiter: str,
    llm: ChatOpenAI,
    interface_dict_raw: dict[str, dict[str, Any]],
    code: str,
    root_rel_path: Path,
) -> JavaInterfaceDict:
    from shared.chunking.text_splitter import split_text

    symbols = extract_symbols_w_ctags(root_rel_path=root_rel_path, file_content=code)
    interface_dict_documented = {}
    global_method_counts = {}
    for _, cls_data in interface_dict_raw.items():
        for m in cls_data["methods"]:
            name = m["name"]
            global_method_counts[name] = global_method_counts.get(name, 0) + 1
    for symbol in symbols:
        for cls_name, cls_data in interface_dict_raw.items():
            if symbol["name"] == cls_name:
                start_line = symbol["line"]
                end_line = symbol.get(
                    "end", symbol["line"] + BLIND_ADVANCE_IF_NO_END_LINE
                )
                interface_code = "\n".join(code.splitlines()[start_line - 1 : end_line])
                code_chunks = split_text(
                    text=interface_code,
                    chunk_size=SYMBOL_MAX_CHUNK_SIZE,
                    chunk_overlap=SYMBOL_CHUNK_OVERLAP,
                )
                if len(code_chunks) == 1:
                    interface_dict_documented = java_interface_dict_from_llm(
                        system_prompt_class=system_prompt_class,
                        user_prompt_class=user_prompt_class,
                        system_prompt_fn=system_prompt_fn,
                        user_prompt_fn=user_prompt_fn,
                        system_prompt_field=system_prompt_field,
                        user_prompt_field=user_prompt_field,
                        class_fn_delimiter=class_fn_delimiter,
                        llm=llm,
                        interface_dict_raw={cls_name: cls_data},
                        code=interface_code,
                    ).data[cls_name]
                elif len(code_chunks) > 1:
                    class_base = JavaInterfaceBaseData.from_llm(
                        system_prompt=system_prompt_class,
                        user_prompt=user_prompt_class,
                        llm=llm,
                        name=cls_name,
                        code=code_chunks[0].text,
                    )
                    methods = {}
                    fields = {}
                    nested_classes = []
                    nested_interfaces = []
                    for m in cls_data["methods"]:
                        m_name = m["name"]
                        scoped_name = cls_name + class_fn_delimiter + m_name
                        m_start_line = m["line"]
                        m_end_line = m.get(
                            "end", m_start_line + BLIND_ADVANCE_IF_NO_END_LINE
                        )
                        m_code = "\n".join(
                            code.splitlines()[m_start_line - 1 : m_end_line]
                        )
                        # More than one method with the same name in the file: cut scope for LLM.
                        if global_method_counts[m_name] > 1:
                            # Use list to handle method overloading, if present.
                            if scoped_name not in methods:
                                methods[scoped_name] = []
                            methods[scoped_name].append(
                                JavaMethodData.from_llm(
                                    system_prompt=system_prompt_fn,
                                    user_prompt=user_prompt_fn,
                                    llm=llm,
                                    fn_name=m_name,
                                    code=m_code,
                                )
                            )
                        else:
                            m_data = JavaMethodData.from_llm(
                                system_prompt=system_prompt_fn,
                                user_prompt=user_prompt_fn,
                                llm=llm,
                                fn_name=m_name,
                                code=m_code,
                            )
                            methods[scoped_name] = m_data
                    for f in cls_data["fields"]:
                        f_name = f["name"]
                        f_start_line = f["line"] - PADDING_LINES_TOP
                        f_end_line = f.get("end", f["line"] + PADDING_LINES_BOTTOM)
                        f_code = "\n".join(code.splitlines()[f_start_line:f_end_line])
                        scoped_name = cls_name + class_fn_delimiter + m_name
                        f_data = JavaFieldData.from_llm(
                            system_prompt=system_prompt_field,
                            user_prompt=user_prompt_field,
                            llm=llm,
                            var_name=f_name,
                            code=f_code,
                        )
                        fields[scoped_name] = f_data

                    for nested_class in cls_data["nested_classes"]:
                        nested_classes.append(nested_class["name"])

                    for nested_interface in cls_data["nested_interfaces"]:
                        nested_interfaces.append(nested_interface["name"])

                    class_data = JavaInterfaceData(
                        base_data=class_base,
                        methods=methods,
                        fields=fields,
                        nested_classes=nested_classes,
                        nested_interfaces=nested_interfaces,
                    )
                    interface_dict_documented[cls_name] = class_data

    return JavaInterfaceDict(data=interface_dict_documented)


class_dict_from_llm_java = partial(
    java_class_dict_from_llm,
    CLASSES_FOUND_SYSTEM_PROMPT_JSON,
    CLASSES_FOUND_USER_PROMPT,
    METHODS_FOUND_SYSTEM_PROMPT_JSON,
    METHODS_FOUND_USER_PROMPT,
    FIELDS_FOUND_SYSTEM_PROMPT_JSON,
    FIELDS_FOUND_USER_PROMPT,
    ".",
)

interface_dict_from_llm_java = partial(
    java_interface_dict_from_llm,
    INTERFACES_FOUND_SYSTEM_PROMPT_JSON,
    INTERFACES_FOUND_USER_PROMPT,
    METHODS_FOUND_SYSTEM_PROMPT_JSON,
    METHODS_FOUND_USER_PROMPT,
    FIELDS_FOUND_SYSTEM_PROMPT_JSON,
    FIELDS_FOUND_USER_PROMPT,
    ".",
)

class_dict_from_llm_java_multi_prompt = partial(
    java_class_dict_from_llm,
    CLASSES_FOUND_SYSTEM_PROMPT_JSON,
    CLASSES_FOUND_USER_PROMPT,
    METHODS_FOUND_SYSTEM_PROMPT_JSON,
    METHODS_FOUND_USER_PROMPT,
    FIELDS_FOUND_SYSTEM_PROMPT_JSON,
    FIELDS_FOUND_USER_PROMPT,
    ".",
)

interface_dict_from_llm_java_multi_prompt = partial(
    java_interface_dict_from_llm,
    INTERFACES_FOUND_SYSTEM_PROMPT_JSON,
    INTERFACES_FOUND_USER_PROMPT,
    METHODS_FOUND_SYSTEM_PROMPT_JSON,
    METHODS_FOUND_USER_PROMPT,
    FIELDS_FOUND_SYSTEM_PROMPT_JSON,
    FIELDS_FOUND_USER_PROMPT,
    ".",
)
