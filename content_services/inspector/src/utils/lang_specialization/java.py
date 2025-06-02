from pathlib import Path
from typing import Self

from pydantic import PrivateAttr
from utils.codemap_ctags import extract_symbols_w_ctags
from utils.models import ChatOpenAI

from .ir_common import (
    FieldNameWithBackTickContent,
    FieldNameWithBulletedContent,
    FieldNameWithRawContent,
    IrCollection,
    IrData,
    ListedBacktickNameRawContentWithNone,
    ListedRawContentNoNone,
    RawContent,
)
from .symbol_common import (
    RawSymbolCollection,
    RawSymbolData,
    ReifiedSymbol,
    ScopeRelation,
    SymbolKind,
    code_requires_multi_prompt,
    create_raw_symbol_via_ctags,
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


class JavaMethodData(IrData):
    single_sentence: RawContent
    modifiers: ListedRawContentNoNone
    inputs: ListedBacktickNameRawContentWithNone
    control_flow: ListedRawContentNoNone
    output: FieldNameWithBulletedContent

    @classmethod
    def system_prompt(cls) -> str:
        return METHODS_FOUND_SYSTEM_PROMPT_JSON

    @classmethod
    def user_prompt(cls, symbol: RawSymbolData) -> str:
        user_prompt = f"{METHODS_FOUND_USER_PROMPT}{symbol.name}\n\nMethod Code:\n\n{symbol.symbol_code}"
        if symbol.file_code:
            user_prompt += f"\n\nFull File Code:\n\n{symbol.file_code}"
        return user_prompt

    @classmethod
    def child_to_ir(cls, symbol: RawSymbolData) -> type[IrData] | None:
        raise NotImplementedError("Methods should not have children")

    @classmethod
    def child_to_field_name(cls, child: RawSymbolData) -> str:
        raise NotImplementedError("Methods should not have children")

    @classmethod
    def default_instance(cls, reified_symbol: ReifiedSymbol | None = None) -> Self:
        return cls(
            single_sentence=RawContent(content=""),
            inputs=ListedBacktickNameRawContentWithNone(content=[]),
            control_flow=ListedRawContentNoNone(content=[]),
            output=FieldNameWithBulletedContent(content=""),
            modifiers=ListedRawContentNoNone(content=[]),
        )


class JavaFieldData(IrData):
    type: FieldNameWithBackTickContent
    description: FieldNameWithRawContent
    use: FieldNameWithRawContent
    modifiers: ListedRawContentNoNone

    @classmethod
    def system_prompt(cls) -> str:
        return FIELDS_FOUND_SYSTEM_PROMPT_JSON

    @classmethod
    def user_prompt(cls, symbol: RawSymbolData) -> str:
        user_prompt = f"{FIELDS_FOUND_USER_PROMPT}{symbol.name}\n\nField Code:\n\n{symbol.symbol_code}"
        if symbol.file_code:
            user_prompt += f"\n\nFull File Code:\n\n{symbol.file_code}"
        return user_prompt

    @classmethod
    def child_to_ir(cls, symbol: RawSymbolData) -> type[IrData] | None:
        raise NotImplementedError("fields should not have children")

    @classmethod
    def child_to_field_name(cls, child: RawSymbolData) -> str:
        raise NotImplementedError("fields should not have children")

    @classmethod
    def default_instance(cls, reified_symbol: ReifiedSymbol | None = None) -> Self:
        return cls(
            type=FieldNameWithBackTickContent(content=""),
            description=FieldNameWithRawContent(content=""),
            use=FieldNameWithRawContent(content=""),
            modifiers=ListedRawContentNoNone(content=[]),
        )


class JavaClassData(IrData):
    modifiers: ListedRawContentNoNone
    interfaces_implemented: ListedRawContentNoNone
    classes_extended: ListedRawContentNoNone
    description: FieldNameWithRawContent
    _supported_child_ordering: list[str] = PrivateAttr(
        default=[
            ScopeRelation.METHOD,
            ScopeRelation.FIELD,
            ScopeRelation.NESTED_CLASS,
            ScopeRelation.NESTED_INTERFACE,
        ]
    )

    @classmethod
    def system_prompt(cls) -> str:
        return CLASSES_FOUND_SYSTEM_PROMPT_JSON

    @classmethod
    def user_prompt(cls, symbol: RawSymbolData) -> str:
        user_prompt = f"{CLASSES_FOUND_USER_PROMPT}{symbol.name}\n\nClass Code:\n\n{symbol.symbol_code}"
        if symbol.file_code:
            user_prompt += f"\n\nFull File Code:\n\n{symbol.file_code}"
        return user_prompt

    @classmethod
    def child_to_ir(cls, symbol: RawSymbolData) -> type[IrData] | None:
        mapping = {
            SymbolKind.CALLABLE: JavaMethodData,
            SymbolKind.CLASS: None,  # for child classes just list them
            SymbolKind.INTERFACE: None,  # for child interfaces just list them
            SymbolKind.VARIABLE: JavaFieldData,
        }
        return mapping.get(symbol.symbol_kind)

    @classmethod
    def child_to_field_name(cls, child: RawSymbolData) -> str:
        mapping = {
            SymbolKind.CALLABLE: ScopeRelation.METHOD,
            SymbolKind.CLASS: ScopeRelation.NESTED_CLASS,
            SymbolKind.INTERFACE: ScopeRelation.NESTED_INTERFACE,
            SymbolKind.VARIABLE: ScopeRelation.FIELD,
        }
        return mapping.get(child.symbol_kind)

    @classmethod
    def default_instance(cls, reified_symbol: ReifiedSymbol | None = None) -> Self:
        return cls(
            modifiers=ListedRawContentNoNone(content=[]),
            interfaces_implemented=ListedRawContentNoNone(content=[]),
            classes_extended=ListedRawContentNoNone(content=[]),
            description=FieldNameWithRawContent(content=""),
        )


class JavaClassCollection(IrCollection):
    data: dict[str, JavaClassData | list[JavaClassData]]

    @classmethod
    def from_llm(cls, llm: ChatOpenAI, symbols_list: RawSymbolCollection) -> Self:
        return cls.from_llm_with_ir_data(JavaClassData, llm, symbols_list)


class JavaInterfaceData(IrData):
    interfaces_extended: ListedRawContentNoNone
    description: FieldNameWithRawContent
    _supported_child_ordering: list[str] = PrivateAttr(
        default=[
            ScopeRelation.METHOD,
            ScopeRelation.FIELD,
            ScopeRelation.NESTED_CLASS,
            ScopeRelation.NESTED_INTERFACE,
        ]
    )

    @classmethod
    def system_prompt(cls) -> str:
        return INTERFACES_FOUND_SYSTEM_PROMPT_JSON

    @classmethod
    def user_prompt(cls, symbol: RawSymbolData) -> str:
        user_prompt = f"{INTERFACES_FOUND_USER_PROMPT}{symbol.name}\n\nInterface Code:\n\n{symbol.symbol_code}"
        if symbol.file_code:
            user_prompt += f"\n\nFull File Code:\n\n{symbol.file_code}"
        return user_prompt

    @classmethod
    def child_to_ir(cls, symbol: RawSymbolData) -> type[IrData] | None:
        mapping = {
            SymbolKind.CALLABLE: JavaMethodData,
            SymbolKind.CLASS: None,  # for child classes just list them
            SymbolKind.INTERFACE: None,  # for child interfaces just list them
            SymbolKind.VARIABLE: JavaFieldData,
        }
        return mapping.get(symbol.symbol_kind)

    @classmethod
    def child_to_field_name(cls, child: RawSymbolData) -> str:
        mapping = {
            SymbolKind.CALLABLE: ScopeRelation.METHOD,
            SymbolKind.CLASS: ScopeRelation.NESTED_CLASS,
            SymbolKind.INTERFACE: ScopeRelation.NESTED_INTERFACE,
            SymbolKind.VARIABLE: ScopeRelation.FIELD,
        }
        return mapping.get(child.symbol_kind)

    @classmethod
    def default_instance(cls, reified_symbol: ReifiedSymbol | None = None) -> Self:
        return cls(
            interfaces_extended=ListedRawContentNoNone(content=[]),
            description=FieldNameWithRawContent(content=""),
        )


class JavaInterfaceCollection(IrCollection):
    data: dict[str, JavaInterfaceData | list[JavaInterfaceData]]

    @classmethod
    def from_llm(cls, llm: ChatOpenAI, symbols_list: RawSymbolCollection) -> Self:
        return cls.from_llm_with_ir_data(JavaInterfaceData, llm, symbols_list)


class JavaClassRawSymbolCollection(RawSymbolCollection):
    data: dict[str, RawSymbolData]

    @classmethod
    def from_static_analysis(cls, code: str, root_rel_path: Path) -> Self | None:
        is_multi_prompt = code_requires_multi_prompt(code)

        symbols = extract_symbols_w_ctags(
            root_rel_path=root_rel_path, file_content=code
        )

        class_raw_symbol_data = {}
        for s in symbols:
            if s["kind"] in JAVA_CLASSES:
                class_raw_symbol_data[s["name"]] = create_raw_symbol_via_ctags(
                    ctags_symbol=s,
                    root_rel_path=root_rel_path,
                    code=code,
                    symbol_kind=SymbolKind.CLASS,
                    scope_relation=None,
                    delimiter=".",
                    is_multi_prompt=is_multi_prompt,
                )

        for s in symbols:
            if (
                (s.get("scope"))
                and (s["kind"] in JAVA_METHODS)
                and s["scopeKind"] in JAVA_CLASSES
            ):
                scope = s["scope"].split(".")[-1]
                class_raw_symbol_data[scope].children.append(
                    create_raw_symbol_via_ctags(
                        ctags_symbol=s,
                        root_rel_path=root_rel_path,
                        code=code,
                        symbol_kind=SymbolKind.CALLABLE,
                        scope_relation=ScopeRelation.METHOD,
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
                    create_raw_symbol_via_ctags(
                        ctags_symbol=s,
                        root_rel_path=root_rel_path,
                        code=code,
                        symbol_kind=SymbolKind.CLASS,
                        scope_relation=ScopeRelation.NESTED_CLASS,
                        delimiter=".",
                        is_multi_prompt=is_multi_prompt,
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
                    create_raw_symbol_via_ctags(
                        ctags_symbol=s,
                        root_rel_path=root_rel_path,
                        code=code,
                        symbol_kind=SymbolKind.INTERFACE,
                        scope_relation=ScopeRelation.NESTED_INTERFACE,
                        delimiter=".",
                        is_multi_prompt=is_multi_prompt,
                    )
                )
            elif (
                (s.get("scope"))
                and (s["kind"] in JAVA_FIELDS)
                and (s["scopeKind"] in JAVA_CLASSES)
            ):
                scope = s["scope"].split(".")[-1]
                class_raw_symbol_data[scope].children.append(
                    create_raw_symbol_via_ctags(
                        ctags_symbol=s,
                        root_rel_path=root_rel_path,
                        code=code,
                        symbol_kind=SymbolKind.VARIABLE,
                        scope_relation=ScopeRelation.FIELD,
                        delimiter=".",
                        is_multi_prompt=is_multi_prompt,
                    )
                )
        output = (
            None if len(class_raw_symbol_data) == 0 else cls(data=class_raw_symbol_data)
        )
        return output

    @classmethod
    def from_llm(cls, code: str, root_rel_path: str) -> Self:
        raise NotImplementedError("Static analysis should be used for Java classes")

    def to_dict(self) -> dict[str, RawSymbolData]:
        return self.data


class JavaInterfaceRawSymbolCollection(RawSymbolCollection):
    data: dict[str, RawSymbolData]

    @classmethod
    def from_static_analysis(cls, code: str, root_rel_path: Path) -> Self | None:
        is_multi_prompt = code_requires_multi_prompt(code)

        symbols = extract_symbols_w_ctags(
            root_rel_path=root_rel_path, file_content=code
        )

        interface_raw_symbol_data = {}
        for s in symbols:
            if s["kind"] in JAVA_INTERFACES:
                interface_raw_symbol_data[s["name"]] = create_raw_symbol_via_ctags(
                    ctags_symbol=s,
                    root_rel_path=root_rel_path,
                    code=code,
                    symbol_kind=SymbolKind.INTERFACE,
                    scope_relation=None,
                    delimiter=".",
                    is_multi_prompt=is_multi_prompt,
                )

        for s in symbols:
            if (
                (s.get("scope"))
                and (s["kind"] in JAVA_METHODS)
                and s["scopeKind"] in JAVA_INTERFACES
            ):
                scope = s["scope"].split(".")[-1]
                interface_raw_symbol_data[scope].children.append(
                    create_raw_symbol_via_ctags(
                        ctags_symbol=s,
                        root_rel_path=root_rel_path,
                        code=code,
                        symbol_kind=SymbolKind.CALLABLE,
                        scope_relation=ScopeRelation.METHOD,
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
                    create_raw_symbol_via_ctags(
                        ctags_symbol=s,
                        root_rel_path=root_rel_path,
                        code=code,
                        symbol_kind=SymbolKind.CLASS,
                        scope_relation=ScopeRelation.NESTED_CLASS,
                        delimiter=".",
                        is_multi_prompt=is_multi_prompt,
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
                    create_raw_symbol_via_ctags(
                        ctags_symbol=s,
                        root_rel_path=root_rel_path,
                        code=code,
                        symbol_kind=SymbolKind.INTERFACE,
                        scope_relation=ScopeRelation.NESTED_INTERFACE,
                        delimiter=".",
                        is_multi_prompt=is_multi_prompt,
                    )
                )
            elif (
                (s.get("scope"))
                and (s["kind"] in JAVA_FIELDS)
                and (s["scopeKind"] in JAVA_INTERFACES)
            ):
                scope = s["scope"].split(".")[-1]
                interface_raw_symbol_data[scope].children.append(
                    create_raw_symbol_via_ctags(
                        ctags_symbol=s,
                        root_rel_path=root_rel_path,
                        code=code,
                        symbol_kind=SymbolKind.VARIABLE,
                        scope_relation=ScopeRelation.FIELD,
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
    def from_llm(cls, code: str, root_rel_path: str) -> Self:
        raise NotImplementedError("Static analysis should be used for Java interfaces")

    def to_dict(self) -> dict[str, RawSymbolData]:
        return self.data
