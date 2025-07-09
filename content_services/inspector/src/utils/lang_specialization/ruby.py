from pathlib import Path
from typing import Self

from pydantic import PrivateAttr
from shared.prompts.structured_prompting import (
    GENERAL_STE_STYLE_INSTRUCTION,
    NO_RESTATEMENT_STYLE_INSTRUCTION_FOR_SYMBOLS,
    USE_BACKTICKS_STYLE_INSTRUCTION,
    Component,
    Prompt,
)
from utils.codemap_ctags import extract_symbols_w_ctags
from utils.models import ChatOpenAI

from .ir_common import (
    FieldNameWithRawContent,
    FnData,
    IrCollection,
    IrData,
    ListedRawContentNoNone,
    VariableData,
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

Method to document:
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

Attribute to document:
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

Class to document:
"""


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

Module to document:
"""


# IR Classes
class RubyMethodData(FnData):
    @classmethod
    def system_prompt(cls, symbol: RawSymbolData) -> str:
        return (
            Prompt.empty()
            .append(Component(string=METHODS_FOUND_SYSTEM_PROMPT_JSON))
            .append(GENERAL_STE_STYLE_INSTRUCTION)
            .append(USE_BACKTICKS_STYLE_INSTRUCTION)
            .into_str()
        )

    @classmethod
    def user_prompt(cls, symbol: RawSymbolData) -> str:
        user_prompt = (
            Prompt.empty()
            .append(Component(string=f"{METHODS_FOUND_USER_PROMPT}\n{symbol.name}"))
            .append(NO_RESTATEMENT_STYLE_INSTRUCTION_FOR_SYMBOLS)
            .append(Component(string=f"Method Code:\n\n{symbol.symbol_code}"))
        )
        if symbol.file_code:
            user_prompt.append(
                Component(string=f"\n\nFull File Code:\n\n{symbol.file_code}")
            )
        return user_prompt.into_str()

    @classmethod
    def child_to_ir(cls, symbol: RawSymbolData) -> IrData | None:
        raise NotImplementedError("Methods should not have children")

    @classmethod
    def child_to_field_name(cls, child: RawSymbolData) -> str:
        raise NotImplementedError("Methods should not have children")


class RubyAttributeData(VariableData):
    @classmethod
    def system_prompt(cls, symbol: RawSymbolData) -> str:
        return (
            Prompt.empty()
            .append(Component(string=ATTRIBUTES_FOUND_SYSTEM_PROMPT_JSON))
            .append(GENERAL_STE_STYLE_INSTRUCTION)
            .append(USE_BACKTICKS_STYLE_INSTRUCTION)
            .into_str()
        )

    @classmethod
    def user_prompt(cls, symbol: RawSymbolData) -> str:
        user_prompt = (
            Prompt.empty()
            .append(Component(string=f"{ATTRIBUTES_FOUND_USER_PROMPT}{symbol.name}"))
            .append(NO_RESTATEMENT_STYLE_INSTRUCTION_FOR_SYMBOLS)
            .append(Component(string=f"Attribute Code:\n\n{symbol.symbol_code}"))
        )
        if symbol.file_code:
            user_prompt.append(
                Component(string=f"\n\nFull File Code:\n\n{symbol.file_code}")
            )
        return user_prompt.into_str()

    @classmethod
    def child_to_ir(cls, symbol: RawSymbolData) -> IrData | None:
        raise NotImplementedError("Attributes should not have children")

    @classmethod
    def child_to_field_name(cls, child: RawSymbolData) -> str:
        raise NotImplementedError("Attributes should not have children")


class RubyClassData(IrData):
    description: FieldNameWithRawContent
    inherits_from: ListedRawContentNoNone
    includes: ListedRawContentNoNone
    extends: ListedRawContentNoNone
    prepends: ListedRawContentNoNone
    _supported_child_ordering: list[str] = PrivateAttr(
        default=[
            ScopeRelation.ATTRIBUTE,
            ScopeRelation.CLASS_METHOD,
            ScopeRelation.INSTANCE_METHOD,
        ]
    )

    @classmethod
    def system_prompt(cls, symbol: RawSymbolData) -> str:
        return (
            Prompt.empty()
            .append(Component(string=CLASSES_FOUND_SYSTEM_PROMPT_JSON))
            .append(GENERAL_STE_STYLE_INSTRUCTION)
            .append(USE_BACKTICKS_STYLE_INSTRUCTION)
            .into_str()
        )

    @classmethod
    def user_prompt(cls, symbol: RawSymbolData) -> str:
        user_prompt = (
            Prompt.empty()
            .append(Component(string=f"{CLASSES_FOUND_USER_PROMPT}{symbol.name}"))
            .append(NO_RESTATEMENT_STYLE_INSTRUCTION_FOR_SYMBOLS)
            .append(Component(string=f"Class Code:\n\n{symbol.symbol_code}"))
        )
        if symbol.file_code:
            user_prompt.append(
                Component(string=f"\n\nFull File Code:\n\n{symbol.file_code}")
            )
        return user_prompt.into_str()

    @classmethod
    def child_to_ir(cls, symbol: RawSymbolData) -> IrData | None:
        mapping = {
            SymbolKind.CALLABLE: RubyMethodData,
            SymbolKind.VARIABLE: RubyAttributeData,
        }
        return mapping.get(symbol.symbol_kind)

    @classmethod
    def child_to_field_name(cls, child: RawSymbolData) -> str:
        mapping = {
            ScopeRelation.INSTANCE_METHOD: ScopeRelation.INSTANCE_METHOD,
            ScopeRelation.CLASS_METHOD: ScopeRelation.CLASS_METHOD,
            ScopeRelation.ATTRIBUTE: ScopeRelation.ATTRIBUTE,
        }
        return mapping.get(child.scope_relation)

    @classmethod
    def default_instance(cls, reified_symbol: ReifiedSymbol | None = None) -> Self:
        return cls(
            description=FieldNameWithRawContent(content=""),
            inherits_from=ListedRawContentNoNone(content=[]),
            includes=ListedRawContentNoNone(content=[]),
            extends=ListedRawContentNoNone(content=[]),
            prepends=ListedRawContentNoNone(content=[]),
        )


class RubyClassCollection(IrCollection):
    data: dict[str, RubyClassData | list[RubyClassData]]

    @classmethod
    def from_llm(cls, llm: ChatOpenAI, symbols_list: RawSymbolCollection) -> Self:
        return cls.from_llm_with_ir_data(RubyClassData, llm, symbols_list)


class RubyModuleData(IrData):
    description: FieldNameWithRawContent
    includes: ListedRawContentNoNone
    extends: ListedRawContentNoNone
    prepends: ListedRawContentNoNone
    _supported_child_ordering: list[str] = PrivateAttr(
        default=[
            ScopeRelation.ATTRIBUTE,
            ScopeRelation.MODULE_METHOD,
            ScopeRelation.INSTANCE_METHOD,
        ]
    )

    @classmethod
    def system_prompt(cls, symbol: RawSymbolData) -> str:
        return (
            Prompt.empty()
            .append(Component(string=MODULES_FOUND_SYSTEM_PROMPT_JSON))
            .append(GENERAL_STE_STYLE_INSTRUCTION)
            .append(USE_BACKTICKS_STYLE_INSTRUCTION)
            .into_str()
        )

    @classmethod
    def user_prompt(cls, symbol: RawSymbolData) -> str:
        user_prompt = (
            Prompt.empty()
            .append(Component(string=f"{MODULES_FOUND_USER_PROMPT}{symbol.name}"))
            .append(Component(string=f"Module Code:\n\n{symbol.symbol_code}"))
        )
        if symbol.file_code:
            user_prompt.append(
                Component(string=f"\n\nFull File Code:\n\n{symbol.file_code}")
            )
        return user_prompt.into_str()

    @classmethod
    def child_to_ir(cls, symbol: RawSymbolData) -> IrData | None:
        mapping = {
            SymbolKind.CALLABLE: RubyMethodData,
            SymbolKind.VARIABLE: RubyAttributeData,
        }
        return mapping.get(symbol.symbol_kind)

    @classmethod
    def child_to_field_name(cls, child: RawSymbolData) -> str:
        mapping = {
            ScopeRelation.INSTANCE_METHOD: ScopeRelation.INSTANCE_METHOD,
            ScopeRelation.MODULE_METHOD: ScopeRelation.MODULE_METHOD,
            ScopeRelation.ATTRIBUTE: ScopeRelation.ATTRIBUTE,
        }
        return mapping.get(child.scope_relation)

    @classmethod
    def default_instance(cls, reified_symbol: ReifiedSymbol | None = None) -> Self:
        return cls(
            description=FieldNameWithRawContent(content=""),
            includes=ListedRawContentNoNone(content=[]),
            extends=ListedRawContentNoNone(content=[]),
            prepends=ListedRawContentNoNone(content=[]),
        )


class RubyModuleCollection(IrCollection):
    data: dict[str, RubyModuleData | list[RubyModuleData]]

    @classmethod
    def from_llm(cls, llm: ChatOpenAI, symbols_list: RawSymbolCollection) -> Self:
        return cls.from_llm_with_ir_data(RubyModuleData, llm, symbols_list)


class RubyClassRawSymbolCollection(RawSymbolCollection):
    data: dict[str, RawSymbolData]

    @classmethod
    def from_static_analysis(cls, code: str, root_rel_path: Path) -> Self | None:
        is_multi_prompt = code_requires_multi_prompt(code)

        symbols = extract_symbols_w_ctags(
            root_rel_path=root_rel_path, file_content=code
        )

        class_raw_symbol_data = {}
        for s in symbols:
            if s["kind"] in RUBY_CLASSES:
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
                and (s["kind"] in RUBY_ATTRIBUTES)
                and s["scopeKind"] in RUBY_CLASSES
            ):
                scope = s["scope"].split(".")[-1]
                class_raw_symbol_data[scope].children.append(
                    create_raw_symbol_via_ctags(
                        ctags_symbol=s,
                        root_rel_path=root_rel_path,
                        code=code,
                        symbol_kind=SymbolKind.VARIABLE,
                        scope_relation=ScopeRelation.ATTRIBUTE,
                        delimiter=".",
                        is_multi_prompt=is_multi_prompt,
                    )
                )
            elif (
                (s.get("scope"))
                and (s["kind"] in RUBY_CLASS_AND_MODULE_METHODS)
                and s["scopeKind"] in RUBY_CLASSES
            ):
                scope = s["scope"].split(".")[-1]
                class_raw_symbol_data[scope].children.append(
                    create_raw_symbol_via_ctags(
                        ctags_symbol=s,
                        root_rel_path=root_rel_path,
                        code=code,
                        symbol_kind=SymbolKind.CALLABLE,
                        scope_relation=ScopeRelation.CLASS_METHOD,
                        delimiter=".",
                        is_multi_prompt=is_multi_prompt,
                    )
                )
            elif (
                (s.get("scope"))
                and (s["kind"] in RUBY_INSTANCE_METHODS)
                and s["scopeKind"] in RUBY_CLASSES
            ):
                scope = s["scope"].split(".")[-1]
                class_raw_symbol_data[scope].children.append(
                    create_raw_symbol_via_ctags(
                        ctags_symbol=s,
                        root_rel_path=root_rel_path,
                        code=code,
                        symbol_kind=SymbolKind.CALLABLE,
                        scope_relation=ScopeRelation.INSTANCE_METHOD,
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
        raise NotImplementedError("static analysis should be used for Ruby classes")

    @classmethod
    def to_dict(self) -> dict[str, RawSymbolData]:
        return self.data


class RubyModuleRawSymbolCollection(RawSymbolCollection):
    data: dict[str, RawSymbolData]

    @classmethod
    def from_static_analysis(cls, code: str, root_rel_path: Path) -> Self | None:
        is_multi_prompt = code_requires_multi_prompt(code)

        symbols = extract_symbols_w_ctags(
            root_rel_path=root_rel_path, file_content=code
        )

        module_raw_symbol_data = {}
        for s in symbols:
            if s["kind"] in RUBY_MODULES:
                module_raw_symbol_data[s["name"]] = create_raw_symbol_via_ctags(
                    ctags_symbol=s,
                    root_rel_path=root_rel_path,
                    code=code,
                    symbol_kind=SymbolKind.MODULE,
                    scope_relation=None,
                    delimiter=".",
                    is_multi_prompt=is_multi_prompt,
                )

        for s in symbols:
            if (
                (s.get("scope"))
                and (s["kind"] in RUBY_ATTRIBUTES)
                and s["scopeKind"] in RUBY_MODULES
            ):
                scope = s["scope"].split(".")[-1]
                module_raw_symbol_data[scope].children.append(
                    create_raw_symbol_via_ctags(
                        ctags_symbol=s,
                        root_rel_path=root_rel_path,
                        code=code,
                        symbol_kind=SymbolKind.VARIABLE,
                        scope_relation=ScopeRelation.ATTRIBUTE,
                        delimiter=".",
                        is_multi_prompt=is_multi_prompt,
                    )
                )
            elif (
                (s.get("scope"))
                and (s["kind"] in RUBY_CLASS_AND_MODULE_METHODS)
                and s["scopeKind"] in RUBY_MODULES
            ):
                scope = s["scope"].split(".")[-1]
                module_raw_symbol_data[scope].children.append(
                    create_raw_symbol_via_ctags(
                        ctags_symbol=s,
                        root_rel_path=root_rel_path,
                        code=code,
                        symbol_kind=SymbolKind.CALLABLE,
                        scope_relation=ScopeRelation.MODULE_METHOD,
                        delimiter=".",
                        is_multi_prompt=is_multi_prompt,
                    )
                )
            elif (
                (s.get("scope"))
                and (s["kind"] in RUBY_INSTANCE_METHODS)
                and s["scopeKind"] in RUBY_MODULES
            ):
                scope = s["scope"].split(".")[-1]
                module_raw_symbol_data[scope].children.append(
                    create_raw_symbol_via_ctags(
                        ctags_symbol=s,
                        root_rel_path=root_rel_path,
                        code=code,
                        symbol_kind=SymbolKind.CALLABLE,
                        scope_relation=ScopeRelation.INSTANCE_METHOD,
                        delimiter=".",
                        is_multi_prompt=is_multi_prompt,
                    )
                )

        output = (
            None
            if len(module_raw_symbol_data) == 0
            else cls(data=module_raw_symbol_data)
        )
        return output

    @classmethod
    def from_llm(cls, code: str, root_rel_path: str) -> Self:
        raise NotImplementedError("static analysis should be used for Ruby modules")

    @classmethod
    def to_dict(self) -> dict[str, RawSymbolData]:
        return self.data
