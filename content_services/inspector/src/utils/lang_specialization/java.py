from functools import partial
from pathlib import Path
from typing import Self

from utils.codemap_ctags import extract_symbols_w_ctags

from .common_v2 import (
    IrCollection,
    IrData,
    NamedContent,
    NestedIrData,
    RawSymbolCollection,
    RawSymbolData,
    SymbolKind,
    code_requires_multi_prompt,
    create_to_be_documented_raw_symbol_via_ctags,
    create_undocumented_raw_symbol_via_ctags,
)

JAVA_INTERFACES = {"interface"}
JAVA_CLASSES = {"class", "enum"}
JAVA_METHODS = {"method"}
JAVA_FIELDS = {"field"}

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

Interface to document:
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

Class to document:
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

Method to document:
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

Field to document:
"""

FIELDS_NONE_CONTENT = "\n---\nNo fields defined in this file."


class JavaMethodData(IrData):
    single_sentence: str
    modifiers: list[str]
    inputs: list[NamedContent]
    control_flow: list[str]
    output: str


class JavaMethodDict(IrCollection):
    data: dict[str, JavaMethodData | list[JavaMethodData]]


class JavaFieldData(IrData):
    type: str
    description: str
    use: str
    modifiers: list[str]


class JavaFieldDict(IrCollection):
    data: dict[str, list[JavaFieldData]]


class JavaClassBaseData(IrData):
    modifers: list[str]
    interfaces_implemented: list[str]
    classes_extended: list[str]
    description: str


class JavaClassData(NestedIrData):
    base_data: JavaClassBaseData
    methods: dict[str, JavaMethodData | list[JavaMethodData]]
    fields: dict[str, JavaFieldData | list[JavaFieldData]]
    nested_classes: list[str]
    nested_interfaces: list[str]

    @classmethod
    def default_class(cls) -> Self:
        base_data = JavaClassBaseData(
            modifers=[],
            interfaces_implemented=[],
            classes_extended=[],
            description="",
        )
        return cls(
            base_data=base_data,
            methods={},
            fields={},
            nested_classes=[],
            nested_interfaces=[],
        )


class JavaClassDict(IrCollection):
    data: dict[str, list[JavaClassData]]


class JavaInterfaceBaseData(IrData):
    interfaces_extended: list[str]
    description: str


class JavaInterfaceData(NestedIrData):
    base_data: JavaInterfaceBaseData
    methods: dict[str, JavaMethodData | list[JavaMethodData]]
    fields: dict[str, JavaFieldData | list[JavaFieldData]]
    nested_classes: list[str]
    nested_interfaces: list[str]

    @classmethod
    def default_class(cls) -> Self:
        base_data = JavaInterfaceBaseData(
            description="",
            interfaces_extended=[],
        )
        return cls(
            base_data=base_data,
            methods={},
            fields={},
            nested_classes=[],
            nested_interfaces=[],
        )


class JavaInterfaceDict(IrCollection):
    data: dict[str, list[JavaInterfaceData]]


class JavaClassRawSymbolCollection(RawSymbolCollection):
    data: dict[str, RawSymbolData]

    @classmethod
    def from_ctags(cls, code: str, root_rel_path: Path) -> Self | None:
        is_multi_prompt = code_requires_multi_prompt(code)

        symbols = extract_symbols_w_ctags(
            root_rel_path=root_rel_path, file_content=code
        )

        class_raw_symbol_data = {}
        for s in symbols:
            if s["kind"] in JAVA_CLASSES:
                class_raw_symbol_data[s["name"]] = (
                    create_to_be_documented_raw_symbol_via_ctags(
                        ctags_symbol=s,
                        root_rel_path=root_rel_path,
                        code=code,
                        symbol_kind=SymbolKind.DATA_STRUCTURE,
                        ir_kind=JavaClassData,
                        scope_relation=None,
                        delimiter=".",
                        is_multi_prompt=is_multi_prompt,
                    )
                )

        for s in symbols:
            if (
                (s.get("scope"))
                and (s["kind"] in JAVA_METHODS)
                and s["scopeKind"] in JAVA_CLASSES
            ):
                scope = s["scope"].split(".")[-1]
                class_raw_symbol_data[scope].children.append(
                    create_to_be_documented_raw_symbol_via_ctags(
                        ctags_symbol=s,
                        root_rel_path=root_rel_path,
                        code=code,
                        symbol_kind=SymbolKind.CALLABLE,
                        ir_kind=JavaMethodData,
                        scope_relation="methods",
                        delimiter=".",
                        is_multi_prompt=is_multi_prompt,
                    )
                )
            elif (
                (s.get("scope"))
                and not s["name"].startswith("__anon")
                and (s["kind"] in JAVA_CLASSES)
                and (s["scopeKind"] in JAVA_CLASSES)
            ):
                scope = s["scope"].split(".")[-1]
                # No docs generated, just listing this, so text field unnecessary.
                class_raw_symbol_data[scope].children.append(
                    create_undocumented_raw_symbol_via_ctags(
                        ctags_symbol=s,
                        root_rel_path=root_rel_path,
                        symbol_kind=SymbolKind.DATA_STRUCTURE,
                        scope_relation="nested_classes",
                        delimiter=".",
                    )
                )
            elif (
                (s.get("scope"))
                and (s["kind"] in JAVA_INTERFACES)
                and (s["scopeKind"] in JAVA_CLASSES)
            ):
                scope = s["scope"].split(".")[-1]
                # No docs generated, just listing this, so text field unnecessary.
                class_raw_symbol_data[scope].children.append(
                    create_undocumented_raw_symbol_via_ctags(
                        ctags_symbol=s,
                        root_rel_path=root_rel_path,
                        symbol_kind=SymbolKind.DATA_STRUCTURE,
                        scope_relation="nested_interfaces",
                        delimiter=".",
                    )
                )
            elif (
                (s.get("scope"))
                and (s["kind"] in JAVA_FIELDS)
                and (s["scopeKind"] in JAVA_CLASSES)
            ):
                scope = s["scope"].split(".")[-1]
                class_raw_symbol_data[scope].children.append(
                    create_to_be_documented_raw_symbol_via_ctags(
                        ctags_symbol=s,
                        root_rel_path=root_rel_path,
                        code=code,
                        symbol_kind=SymbolKind.VARIABLE,
                        ir_kind=JavaFieldData,
                        scope_relation="fields",
                        delimiter=".",
                        is_multi_prompt=is_multi_prompt,
                    )
                )
        output = (
            None if len(class_raw_symbol_data) == 0 else cls(data=class_raw_symbol_data)
        )
        return output

    @classmethod
    def from_ts(cls, code: str, root_rel_path: str) -> Self:
        pass

    def to_dict(self) -> dict[str, RawSymbolData]:
        return self.data


class JavaInterfaceRawSymbolCollection(RawSymbolCollection):
    data: dict[str, RawSymbolData]

    @classmethod
    def from_ctags(cls, code: str, root_rel_path: Path) -> Self | None:
        is_multi_prompt = code_requires_multi_prompt(code)

        symbols = extract_symbols_w_ctags(
            root_rel_path=root_rel_path, file_content=code
        )

        interface_raw_symbol_data = {}
        for s in symbols:
            if s["kind"] in JAVA_INTERFACES:
                interface_raw_symbol_data[s["name"]] = (
                    create_to_be_documented_raw_symbol_via_ctags(
                        ctags_symbol=s,
                        root_rel_path=root_rel_path,
                        code=code,
                        symbol_kind=SymbolKind.DATA_STRUCTURE,
                        ir_kind=JavaInterfaceData,
                        scope_relation=None,
                        delimiter=".",
                        is_multi_prompt=is_multi_prompt,
                    )
                )

        for s in symbols:
            if (
                (s.get("scope"))
                and (s["kind"] in JAVA_METHODS)
                and s["scopeKind"] in JAVA_INTERFACES
            ):
                scope = s["scope"].split(".")[-1]
                interface_raw_symbol_data[scope].children.append(
                    create_to_be_documented_raw_symbol_via_ctags(
                        ctags_symbol=s,
                        root_rel_path=root_rel_path,
                        code=code,
                        symbol_kind=SymbolKind.CALLABLE,
                        ir_kind=JavaMethodData,
                        scope_relation="methods",
                        delimiter=".",
                        is_multi_prompt=is_multi_prompt,
                    )
                )
            elif (
                (s.get("scope"))
                and not s["name"].startswith("__anon")
                and (s["kind"] in JAVA_CLASSES)
                and (s["scopeKind"] in JAVA_INTERFACES)
            ):
                scope = s["scope"].split(".")[-1]
                # No docs generated, just listing this, so text field unnecessary.
                interface_raw_symbol_data[scope].children.append(
                    create_undocumented_raw_symbol_via_ctags(
                        ctags_symbol=s,
                        root_rel_path=root_rel_path,
                        symbol_kind=SymbolKind.DATA_STRUCTURE,
                        scope_relation="nested_classes",
                        delimiter=".",
                    )
                )
            elif (
                (s.get("scope"))
                and (s["kind"] in JAVA_INTERFACES)
                and (s["scopeKind"] in JAVA_INTERFACES)
            ):
                scope = s["scope"].split(".")[-1]
                # No docs generated, just listing this, so text field unnecessary.
                interface_raw_symbol_data[scope].children.append(
                    create_undocumented_raw_symbol_via_ctags(
                        ctags_symbol=s,
                        root_rel_path=root_rel_path,
                        symbol_kind=SymbolKind.DATA_STRUCTURE,
                        scope_relation="nested_interfaces",
                        delimiter=".",
                    )
                )
            elif (
                (s.get("scope"))
                and (s["kind"] in JAVA_FIELDS)
                and (s["scopeKind"] in JAVA_INTERFACES)
            ):
                scope = s["scope"].split(".")[-1]
                interface_raw_symbol_data[scope].children.append(
                    create_to_be_documented_raw_symbol_via_ctags(
                        ctags_symbol=s,
                        root_rel_path=root_rel_path,
                        code=code,
                        symbol_kind=SymbolKind.VARIABLE,
                        ir_kind=JavaFieldData,
                        scope_relation="fields",
                        delimiter=".",
                        is_multi_prompt=is_multi_prompt,
                    )
                )
        output = (
            None
            if len(interface_raw_symbol_data) == 0
            else cls(data=interface_raw_symbol_data)
        )
        return output

    @classmethod
    def from_ts(cls, code: str, root_rel_path: str) -> Self:
        pass

    def to_dict(self) -> dict[str, RawSymbolData]:
        return self.data


class_dict_from_llm_java = partial(
    JavaClassDict.dict_from_llm,
    {
        "base_data": CLASSES_FOUND_SYSTEM_PROMPT_JSON,
        "methods": METHODS_FOUND_SYSTEM_PROMPT_JSON,
        "fields": FIELDS_FOUND_SYSTEM_PROMPT_JSON,
    },
    {
        "base_data": CLASSES_FOUND_USER_PROMPT,
        "methods": METHODS_FOUND_USER_PROMPT,
        "fields": FIELDS_FOUND_USER_PROMPT,
    },
    JavaClassData,
)

interface_dict_from_llm_java = partial(
    JavaInterfaceDict.dict_from_llm,
    {
        "base_data": INTERFACES_FOUND_SYSTEM_PROMPT_JSON,
        "methods": METHODS_FOUND_SYSTEM_PROMPT_JSON,
        "fields": FIELDS_FOUND_SYSTEM_PROMPT_JSON,
    },
    {
        "base_data": INTERFACES_FOUND_USER_PROMPT,
        "methods": METHODS_FOUND_USER_PROMPT,
        "fields": FIELDS_FOUND_USER_PROMPT,
    },
    JavaInterfaceData,
)
