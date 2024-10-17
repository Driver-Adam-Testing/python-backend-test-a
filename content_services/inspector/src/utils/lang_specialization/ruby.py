from functools import partial
from pathlib import Path
from typing import Any, Self

import openai
from pydantic import BaseModel
from utils.codemap_ctags import extract_symbols_w_ctags
from utils.models import ChatOpenAI, OutputConfig, OutputConfigKind

from .common import (
    FnData,
    VariableData,
    render_function,
)

RUBY_CLASSES = {"class"}
RUBY_MODULES = {"module"}
RUBY_CLASS_AND_MODULE_METHODS = {"singletonMethod"}
RUBY_INSTANCE_METHODS = {"method"}
RUBY_ATTRIBUTES = {"accessor"}

SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_RUBY = """
You are an expert Ruby programmer and a software engineering documentation expert. You write detailed documentation to explain code written in Ruby.

You are skilled at explaining technical details as well as recognize and articulate the key conceptual components and purpose of software.
"""

SOURCE_CODE_SMALL_SYSTEM_PROMPT_GENERAL_RUBY = """
You are an expert Ruby programmer and a software engineering documentation expert. You write detailed documentation to explain code written in Ruby.

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

METHODS_FOUND_SYSTEM_PROMPT_JSON = """
You are an expert Ruby programmer and a software engineering documentation expert. You write detailed documentation to explain code written in Ruby.

You focus on writing technical documentation for methods. You are skilled at explaining technical details as well as recognizing and articulating the key conceptual components and purpose of software.

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
    "output": <description of output>
}

Return JSON according to the schema above. Do not use the format ```json ... ```, just return the JSON data.
"""

METHODS_FOUND_USER_PROMPT = """
Summarize the method in the code provided below. Describe the inputs, control flow and logic, and output.

- When describing a method, provide detail that matches the complexity of the method body. Large and complex method should get longer explanations, while small ones much less.
"""

ATTRIBUTES_FOUND_SYSTEM_PROMPT_JSON = """
You are an expert Ruby programmer and a software engineering documentation expert. You write detailed documentation to explain code written in Ruby.

You focus on writing technical documentation for attributes. You are skilled at explaining technical details as well as recognizing and articulating the key conceptual components and purpose of software.

You will be given the name of a attribute to document and the source code where the data structure is defined.

Your job is to describe the data structure. **Always respond using exactly the following JSON schema**:
{
    "type": <type of the attribute>,
    "description": <1 to 3 sentence description of the attribute>,
    "use": <Terse 1 sentence description of how this attribute is used>,
}

Return JSON according to the schema above. Do not use the format ```json ... ```, just return the JSON data.
"""

ATTRIBUTES_FOUND_USER_PROMPT = """
Summarize the attribute in the code provided below.

- When describing an attribute, provide detail that matches the complexity of the attribute. Large and complex attributes (e.g., containing large struct instances) should get longer explanations, while small ones (e.g., one line definitions) much less.
"""

CLASSES_FOUND_SYSTEM_PROMPT_JSON = """
You are an expert Ruby programmer and a software engineering documentation expert. You write detailed documentation to explain code written in Ruby.

You focus on writing technical documentation for classes in Ruby. You are skilled at explaining technical details as well as recognizing and articulating the key conceptual components and purpose of software.

You will be given the name of an class to document and the source code where the class is defined.

Your job is to describe the class. **Always respond using exactly the following JSON schema**:
{
    "description": <one paragraph description of the class>,
    "inherits_from": [<list of classes this class inherits from. Can be an empty list.>],
    "includes": [<list of modules this class includes. Can be an empty list>],
    "extends": [<list of modules this class extends. Can be an empty list>],
    "prepends": [<list of modules this class prepends. Can be an empty list>],
}
Return JSON according to the schema above. Do not use the format ```json ... ```, just return the JSON data.
"""

CLASSES_FOUND_USER_PROMPT = """
Summarize the class in the code provided below.

- When describing an important class, provide detail that matches the complexity of the class. Large and complex class should get longer explanations, while small ones a single sentence.
"""

CLASSES_NONE_CONTENT = "\n---\nNo classes defined in this file."

MODULES_FOUND_SYSTEM_PROMPT_JSON = """
You are an expert Ruby programmer and a software engineering documentation expert. You write detailed documentation to explain code written in Ruby.

You focus on writing technical documentation for modules in Ruby. You are skilled at explaining technical details as well as recognizing and articulating the key conceptual components and purpose of software.

You will be given the name of a module to document and the source code where the module is defined.

Your job is to describe the module. **Always respond using exactly the following JSON schema**:
{
    "description": <one paragraph description of the module>,
    "includes": [<list of modules this module includes. Can be an empty list>],
    "extends": [<list of modules this module extends. Can be an empty list>],
    "prepends": [<list of modules this module prepends. Can be an empty list>],
}
Return JSON according to the schema above. Do not use the format ```json ... ```, just return the JSON data.
"""

MODULES_FOUND_USER_PROMPT = """
Summarize the module in the code provided below.

- When describing an important module, provide detail that matches the complexity of the module. Large and complex module should get longer explanations, while small ones a single sentence.
"""

MODULES_NONE_CONTENT = "\n---\nNo modules defined in this file."


class RubyClassBaseData(BaseModel):
    description: str
    inherits_from: list[str]
    includes: list[str]
    extends: list[str]
    prepends: list[str]

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


class RubyClassData(BaseModel):
    base_data: RubyClassBaseData
    instance_methods: dict[str, FnData | list[FnData]]
    class_methods: dict[str, FnData | list[FnData]]
    attributes: dict[str, VariableData | list[VariableData]]


def render_class_base_data(class_data: RubyClassData) -> str:
    output = ""
    if len(class_data.base_data.inherits_from) > 0:
        output += "\n- **Inherits From**:\n"
        for i in class_data.base_data.inherits_from:
            output += f"    - `{i}`\n"
    if len(class_data.base_data.includes) > 0:
        output += "\n- **Includes**:\n"
        for i in class_data.base_data.includes:
            output += f"    - `{i}`\n"
    if len(class_data.base_data.extends) > 0:
        output += "\n- **Extends**:\n"
        for i in class_data.base_data.extends:
            output += f"    - `{i}`\n"
    if len(class_data.base_data.prepends) > 0:
        output += "\n- **Prepends**:\n"
        for i in class_data.base_data.prepends:
            output += f"    - `{i}`\n"
    output += f"\n- **Description**: {class_data.base_data.description}\n\n"
    return output


class RubyClassDict(BaseModel):
    data: dict[str, RubyClassData]

    def render_markdown(self) -> str:
        output = "\n---"
        for k, v in self.data.items():
            output += f"\n### {k}\n"
            output += render_class_base_data(v)
            if len(v.attributes) > 0:
                output += "\n**Attributes**\n"
                for n, f in v.attributes.items():
                    output += f"\n---\n#### {n}\n"
                    output += f"- **Type**: `{f.type}`\n"
                    output += f"- **Description**\n{f.description}\n"
                    output += f"- **Use**\n{f.use}\n\n"
            if len(v.class_methods) > 0:
                output += "\n**Class Methods**\n"
                for n, m in v.class_methods.items():
                    # Case of potentially overloaded method.
                    if isinstance(m, list):
                        for sub_m in m:
                            output += render_function(n, sub_m, 4)
                    else:
                        output += render_function(n, m, 4)
            if len(v.instance_methods) > 0:
                output += "\n**Instance Methods**\n"
                for n, m in v.instance_methods.items():
                    # Case of potentially overloaded method.
                    if isinstance(m, list):
                        for sub_m in m:
                            output += render_function(n, sub_m, 4)
                    else:
                        output += render_function(n, m, 4)
            output += "\n---\n---"

        return output

    def __str__(self) -> str:
        return self.render_markdown()


class RubyModuleBaseData(BaseModel):
    description: str
    includes: list[str]
    extends: list[str]
    prepends: list[str]

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
            f"{user_prompt}Module to document: {name}\n\nCode:\n\n{code}"
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


class RubyModuleData(BaseModel):
    base_data: RubyClassBaseData
    instance_methods: dict[str, FnData | list[FnData]]
    module_methods: dict[str, FnData | list[FnData]]
    attributes: dict[str, VariableData | list[VariableData]]


def render_module_base_data(class_data: RubyClassData) -> str:
    output = ""
    if len(class_data.base_data.includes) > 0:
        output += "\n- **Includes**:\n"
        for i in class_data.base_data.includes:
            output += f"    - `{i}`\n"
    if len(class_data.base_data.extends) > 0:
        output += "\n- **Extends**:\n"
        for i in class_data.base_data.extends:
            output += f"    - `{i}`\n"
    if len(class_data.base_data.prepends) > 0:
        output += "\n- **Prepends**:\n"
        for i in class_data.base_data.prepends:
            output += f"    - `{i}`\n"
    output += f"\n- **Description**: {class_data.base_data.description}\n\n"
    return output


class RubyModuleDict(BaseModel):
    data: dict[str, RubyModuleData]

    def render_markdown(self) -> str:
        output = "\n---"
        for k, v in self.data.items():
            output += f"\n### {k}\n"
            output += render_module_base_data(v)
            if len(v.attributes) > 0:
                output += "\n**Attributes**\n"
                for n, f in v.attributes.items():
                    output += f"\n---\n#### {n}\n"
                    output += f"- **Type**: `{f.type}`\n"
                    output += f"- **Description**\n{f.description}\n"
                    output += f"- **Use**\n{f.use}\n\n"
            if len(v.module_methods) > 0:
                output += "\n**Module Methods**\n"
                for n, m in v.module_methods.items():
                    # Case of potentially overloaded method.
                    if isinstance(m, list):
                        for sub_m in m:
                            output += render_function(n, sub_m, 4)
                    else:
                        output += render_function(n, m, 4)
            if len(v.instance_methods) > 0:
                output += "\n**Instance Methods**\n"
                for n, m in v.instance_methods.items():
                    # Case of potentially overloaded method.
                    if isinstance(m, list):
                        for sub_m in m:
                            output += render_function(n, sub_m, 4)
                    else:
                        output += render_function(n, m, 4)
            output += "\n---\n---"

        return output

    def __str__(self) -> str:
        return self.render_markdown()


def ruby_class_checker(
    code: str, root_rel_path: Path, structured_output: bool = True
) -> list[dict] | str | None:
    symbols = extract_symbols_w_ctags(root_rel_path=root_rel_path, file_content=code)
    classes_dict = {
        s["name"]: {
            "instance_methods": [],
            "class_methods": [],
            "attributes": [],
        }
        for s in symbols
        if s["kind"] in RUBY_CLASSES
    }
    for s in symbols:
        if (
            (s.get("scope"))
            and (s["kind"] in RUBY_CLASS_AND_MODULE_METHODS)
            and s["scopeKind"] in RUBY_CLASSES
        ):
            classes_dict[s["scope"].split(".")[-1]]["class_methods"].append(s)
        if (
            (s.get("scope"))
            and (s["kind"] in RUBY_INSTANCE_METHODS)
            and s["scopeKind"] in RUBY_CLASSES
        ):
            classes_dict[s["scope"].split(".")[-1]]["instance_methods"].append(s)
        elif (
            (s.get("scope"))
            and (s["kind"] in RUBY_ATTRIBUTES)
            and (s["scopeKind"] in RUBY_CLASSES)
        ):
            classes_dict[s["scope"].split(".")[-1]]["attributes"].append(s)

    output = None
    if len(classes_dict) > 0:
        if structured_output:
            output = classes_dict
        else:
            output = "\nClasses to document in the code:\n\n"
            for n in classes_dict:
                output += f"- {n}\n"
    return output


def ruby_module_checker(
    code: str, root_rel_path: Path, structured_output: bool = True
) -> list[dict] | str | None:
    symbols = extract_symbols_w_ctags(root_rel_path=root_rel_path, file_content=code)
    classes_dict = {
        s["name"]: {
            "instance_methods": [],
            "module_methods": [],
            "attributes": [],
        }
        for s in symbols
        if s["kind"] in RUBY_MODULES
    }
    for s in symbols:
        if (
            (s.get("scope"))
            and (s["kind"] in RUBY_CLASS_AND_MODULE_METHODS)
            and s["scopeKind"] in RUBY_MODULES
        ):
            classes_dict[s["scope"].split(".")[-1]]["module_methods"].append(s)
        if (
            (s.get("scope"))
            and (s["kind"] in RUBY_INSTANCE_METHODS)
            and s["scopeKind"] in RUBY_MODULES
        ):
            classes_dict[s["scope"].split(".")[-1]]["instance_methods"].append(s)
        elif (
            (s.get("scope"))
            and (s["kind"] in RUBY_ATTRIBUTES)
            and (s["scopeKind"] in RUBY_MODULES)
        ):
            classes_dict[s["scope"].split(".")[-1]]["attributes"].append(s)

    output = None
    if len(classes_dict) > 0:
        if structured_output:
            output = classes_dict
        else:
            output = "\nClasses to document in the code:\n\n"
            for n in classes_dict:
                output += f"- {n}\n"
    return output


def ruby_class_dict_from_llm(
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
) -> RubyClassDict:
    class_dict_documented = {}
    global_method_counts = {}
    for _, cls_data in class_dict_raw.items():
        for m in cls_data["class_methods"]:
            name = m["name"]
            global_method_counts[name] = global_method_counts.get(name, 0) + 1
        for m in cls_data["instance_methods"]:
            name = m["name"]
            global_method_counts[name] = global_method_counts.get(name, 0) + 1
    for cls_name, cls_data in class_dict_raw.items():
        class_base = RubyClassBaseData.from_llm(
            system_prompt=system_prompt_class,
            user_prompt=user_prompt_class,
            llm=llm,
            name=cls_name,
            code=code,
        )
        class_methods = {}
        instance_methods = {}
        attributes = {}
        for m in cls_data["class_methods"]:
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
                if scoped_name not in class_methods:
                    class_methods[scoped_name] = []
                class_methods[scoped_name].append(
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
                class_methods[scoped_name] = m_data
        for m in cls_data["instance_methods"]:
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
                if scoped_name not in instance_methods:
                    instance_methods[scoped_name] = []
                instance_methods[scoped_name].append(
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
                instance_methods[scoped_name] = m_data
        for a in cls_data["attributes"]:
            a_name = a["name"]
            scoped_name = cls_name + class_fn_delimiter + a_name
            f_data = VariableData.from_llm(
                system_prompt=system_prompt_field,
                user_prompt=user_prompt_field,
                llm=llm,
                var_name=a_name,
                code=code,
            )
            attributes[scoped_name] = f_data

        class_data = RubyClassData(
            base_data=class_base,
            class_methods=class_methods,
            instance_methods=instance_methods,
            attributes=attributes,
        )
        class_dict_documented[cls_name] = class_data

    return RubyClassDict(data=class_dict_documented)


def ruby_module_dict_from_llm(
    system_prompt_class: str,
    user_prompt_class: str,
    system_prompt_fn: str,
    user_prompt_fn: str,
    system_prompt_field: str,
    user_prompt_field: str,
    class_fn_delimiter: str,
    llm: ChatOpenAI,
    module_dict_raw: dict[str, dict[str, Any]],
    code: str,
) -> RubyModuleDict:
    module_dict_documented = {}
    global_method_counts = {}
    for _, mod_data in module_dict_raw.items():
        for m in mod_data["module_methods"]:
            name = m["name"]
            global_method_counts[name] = global_method_counts.get(name, 0) + 1
        for m in mod_data["instance_methods"]:
            name = m["name"]
            global_method_counts[name] = global_method_counts.get(name, 0) + 1
    for mod_name, mod_data in module_dict_raw.items():
        class_base = RubyClassBaseData.from_llm(
            system_prompt=system_prompt_class,
            user_prompt=user_prompt_class,
            llm=llm,
            name=mod_name,
            code=code,
        )
        module_methods = {}
        instance_methods = {}
        attributes = {}
        for m in mod_data["module_methods"]:
            m_name = m["name"]
            scoped_name = mod_name + class_fn_delimiter + m_name
            # More than one method with the same name in the file: cut scope for LLM.
            if global_method_counts[m_name] > 1:
                m_start_line = m["line"]
                # TODO: Better solution if end line is not present.
                m_end_line = m.get("end")
                code_lines = code.splitlines()
                m_code = "\n".join(code_lines[m_start_line - 1 : m_end_line + 1])
                # Use list to handle method overloading, if present.
                if scoped_name not in module_methods:
                    module_methods[scoped_name] = []
                module_methods[scoped_name].append(
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
                module_methods[scoped_name] = m_data
        for m in mod_data["instance_methods"]:
            m_name = m["name"]
            scoped_name = mod_name + class_fn_delimiter + m_name
            # More than one method with the same name in the file: cut scope for LLM.
            if global_method_counts[m_name] > 1:
                m_start_line = m["line"]
                # TODO: Better solution if end line is not present.
                m_end_line = m.get("end")
                code_lines = code.splitlines()
                m_code = "\n".join(code_lines[m_start_line - 1 : m_end_line + 1])
                # Use list to handle method overloading, if present.
                if scoped_name not in instance_methods:
                    instance_methods[scoped_name] = []
                instance_methods[scoped_name].append(
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
                instance_methods[scoped_name] = m_data
        for a in mod_data["attributes"]:
            a_name = a["name"]
            scoped_name = mod_name + class_fn_delimiter + a_name
            f_data = VariableData.from_llm(
                system_prompt=system_prompt_field,
                user_prompt=user_prompt_field,
                llm=llm,
                var_name=a_name,
                code=code,
            )
            attributes[scoped_name] = f_data

        module_data = RubyModuleData(
            base_data=class_base,
            module_methods=module_methods,
            instance_methods=instance_methods,
            attributes=attributes,
        )
        module_dict_documented[mod_name] = module_data

    return RubyModuleDict(data=module_dict_documented)


BLIND_ADVANCE_IF_NO_END_LINE = 200
PADDING_LINES_TOP = 100
PADDING_LINES_BOTTOM = 100
SYMBOL_MAX_CHUNK_SIZE = 64_000
SYMBOL_CHUNK_OVERLAP = 1_000


class_dict_from_llm_ruby = partial(
    ruby_class_dict_from_llm,
    CLASSES_FOUND_SYSTEM_PROMPT_JSON,
    CLASSES_FOUND_USER_PROMPT,
    METHODS_FOUND_SYSTEM_PROMPT_JSON,
    METHODS_FOUND_USER_PROMPT,
    ATTRIBUTES_FOUND_SYSTEM_PROMPT_JSON,
    ATTRIBUTES_FOUND_USER_PROMPT,
    ".",
)

module_dict_from_llm_ruby = partial(
    ruby_module_dict_from_llm,
    MODULES_FOUND_SYSTEM_PROMPT_JSON,
    MODULES_FOUND_USER_PROMPT,
    METHODS_FOUND_SYSTEM_PROMPT_JSON,
    METHODS_FOUND_USER_PROMPT,
    ATTRIBUTES_FOUND_SYSTEM_PROMPT_JSON,
    ATTRIBUTES_FOUND_USER_PROMPT,
    ".",
)

# class_dict_from_llm_ruby_multi_prompt = partial(
#     ruby_class_dict_from_llm,
#     CLASSES_FOUND_SYSTEM_PROMPT_JSON,
#     CLASSES_FOUND_USER_PROMPT,
#     METHODS_FOUND_SYSTEM_PROMPT_JSON,
#     METHODS_FOUND_USER_PROMPT,
#     FIELDS_FOUND_SYSTEM_PROMPT_JSON,
#     FIELDS_FOUND_USER_PROMPT,
#     ".",
# )
#
# interface_dict_from_llm_ruby_multi_prompt = partial(
#     ruby_interface_dict_from_llm,
#     INTERFACES_FOUND_SYSTEM_PROMPT_JSON,
#     INTERFACES_FOUND_USER_PROMPT,
#     METHODS_FOUND_SYSTEM_PROMPT_JSON,
#     METHODS_FOUND_USER_PROMPT,
#     FIELDS_FOUND_SYSTEM_PROMPT_JSON,
#     FIELDS_FOUND_USER_PROMPT,
#     ".",
# )
#
