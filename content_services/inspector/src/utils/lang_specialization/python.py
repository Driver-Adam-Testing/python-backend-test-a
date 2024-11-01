from functools import partial
from pathlib import Path
from typing import Self

from utils.codemap_ctags import extract_symbols_w_ctags

from .common_v2 import (
    ClassData,
    FnData,
    IrCollection,
    IrData,
    RawSymbolCollection,
    RawSymbolData,
    ScopeRelation,
    SymbolKind,
    VariableData,
    code_requires_multi_prompt,
    create_raw_symbol_via_ctags,
    default_ctags_analysis,
)

PY_CLASS = {"class"}
PY_FUNCTIONS = {"function"}
PY_METHODS = {"member"}
PY_VARIABLES = {"variable"}


SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_PY = """
You are an expert Python programmer and a software engineering documentation expert. You write detailed documentation to explain code written in Python.

You are skilled at explaining technical details as well as recognizing and articulating the key conceptual components and purpose of software.
"""

SOURCE_CODE_SMALL_SYSTEM_PROMPT_GENERAL_PY = """
You are an expert Python programmer and a software engineering documentation expert. You write detailed documentation to explain code written in Python.

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

TECHNICAL_CONCEPTS = """
You will be given the content of a source code file. In a single paragraph of 3 to 5 sentences, describe the important technical features and their interactions in the file.

In writing your description, write about about the conceptual use cases, applications, logic, and component interactions instead of focusing on particular classes, functions, variables, etc.
"""

CLASSES_FOUND_SYSTEM_PROMPT_JSON = """
You are an expert Python programmer and a software engineering documentation expert. You write detailed documentation to explain code written in Python.

You focus on writing technical documentation for classes in Python. You are skilled at explaining technical details as well as recognizing and articulating the key conceptual components and purpose of software.

You will be given the name of a class to document and the source code where the class is defined.

When listing parent classes the class inherits from, only include classes explicitly inherited from and do not include decorators such as the dataclass decorator.

Your job is to describe the class. **Always respond using exactly the following JSON schema**:
{
    "type": <class, dataclass, etc.>,
    "members": [
        {"name": <member_name1>, "content": <Terse 1 sentence description of the first instance or class variable>},
        {"name": <member_name2>, "content": <Terse 1 sentence description of the second instance or class variable>},
        ...
    ],
    "description": <one paragraph description of the class>,
    "inherits_from": [<list of classes explicitly inherited from, does not include decorators>],
}

Return JSON according to the schema above. Do not use the format ```json ... ```, just return the JSON data.
"""

CLASSES_FOUND_USER_PROMPT = """
Summarize the class in the code provided below.

- When describing a class, provide detail that matches the complexity of the class. Large and complex classes with many members should get longer explanations, while small ones a single sentence.

Class to document:
"""

METHODS_FOUND_SYSTEM_PROMPT_JSON = """
You are an expert Python programmer and a software engineering documentation expert. You write detailed documentation to explain code written in Python.

You focus on writing technical documentation for class methods. You are skilled at explaining technical details as well as recognizing and articulating the key conceptual components and purpose of software.

You will be given the name of a class method to document and the source code where the function is defined.

Identify the associated class in your description and always include any `self` or `cls` arguments that exist in a given method as an input.

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

METHODS_FOUND_USER_PROMPT = """
Summarize the class method in the code provided below. Describe the inputs, control flow and logic, and output.

- When describing a class method, provide detail that matches the complexity of the function body. Large and complex functions should get longer explanations, while small ones much less.

Method to document:
"""

DATA_STRUCTURES_FOUND_SYSTEM_PROMPT_JSON = """
You are an expert Python programmer and a software engineering documentation expert. You write detailed documentation to explain code written in Python.

You focus on writing technical documentation for data structures, typically classes in Python. You are skilled at explaining technical details as well as recognizing and articulating the key conceptual components and purpose of software.

You will be given the name of a data structure to document and the source code where the data structure is defined.

Your job is to describe the data structure. **Always respond using exactly the following JSON schema**:
{
    "type": <type of the data structure>,
    "members": [
        {"name": <member_name1>, "content": <Terse 1 sentence description of the first member, field, or attribute>},
        {"name": <member_name2>, "content": <Terse 1 sentence description of the second member, field, or attribute>},
        ...
    ],
    "description": <one paragraph description of the data structure>,
}

Return JSON according to the schema above. Do not use the format ```json ... ```, just return the JSON data.
"""

DATA_STRUCTURES_FOUND_USER_PROMPT = """
Summarize the data structure in the code provided below.

- A data structure is custom or compound type in a given programming language, such as structs, classes, or enums. Functions, methods, and variables are not data structures. In Python, custom data structures are typically defined as classes.
- When describing an important data structure, provide detail that matches the complexity of the data structure. Large and complex data structures should get longer explanations, while small ones a single sentence.

Data structure to document:
"""


FUNCTIONS_FOUND_SYSTEM_PROMPT_JSON = """
You are an expert Python programmer and a software engineering documentation expert. You write detailed documentation to explain code written in Python.

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

Function to document:
"""


VARIABLES_FOUND_SYSTEM_PROMPT_JSON = """
You are an expert Python programmer and a software engineering documentation expert. You write detailed documentation to explain code written in Python.

You focus on writing technical documentation for variables. You are skilled at explaining technical details as well as recognizing and articulating the key conceptual components and purpose of software.

You will be given the name of a variable to document and the source code where the data structure is defined.

Your job is to describe the data structure. **Always respond using exactly the following JSON schema**:
{
    "type": <type of the variable>,
    "description": <1 to 3 sentence description of the variable>,
    "use": <Terse 1 sentence description of how this variable is used>,
}

Return JSON according to the schema above. Do not use the format ```json ... ```, just return the JSON data.
"""

VARIABLES_FOUND_USER_PROMPT = """
Summarize the variable in the code provided below.

- A global variable is declared at the top level scope. Local variables declared and used inside of functions are not global variables. You will be describing a global variable.
- When describing a variable, provide detail that matches the complexity of the variable. Large and complex global variables (e.g., containing large class instances) should get longer explanations, while small ones (e.g., one line definitions) much less.

Variable to document:
"""


# IR data classes
class PyVariableData(VariableData):
    @classmethod
    def system_prompt(cls) -> str:
        return VARIABLES_FOUND_SYSTEM_PROMPT_JSON

    @classmethod
    def user_prompt(cls, symbol: RawSymbolData) -> str:
        user_prompt = f"{VARIABLES_FOUND_USER_PROMPT}{symbol.name}\n\nVariable Code:\n\n{symbol.symbol_code}"
        if symbol.file_code:
            user_prompt += f"\n\nFull File Code:\n\n{symbol.file_code}"
        return user_prompt

    @classmethod
    def child_to_ir(cls, symbol: RawSymbolData) -> type[IrData] | None:
        raise NotImplementedError("Variables should not have children")

    @classmethod
    def child_to_field_name(cls, child: RawSymbolData) -> str:
        raise NotImplementedError("Variables should not have children")


class PyVariableCollection(IrCollection):
    data: dict[str, PyVariableData | list[PyVariableData]]


class PyFnData(FnData):
    @classmethod
    def system_prompt(cls) -> str:
        return FUNCTIONS_FOUND_SYSTEM_PROMPT_JSON

    @classmethod
    def user_prompt(cls, symbol: RawSymbolData) -> str:
        user_prompt = f"{FUNCTIONS_FOUND_USER_PROMPT}{symbol.name}\n\nFunction Code:\n\n{symbol.symbol_code}"
        if symbol.file_code:
            user_prompt += f"\n\nFull File Code:\n\n{symbol.file_code}"
        return user_prompt

    @classmethod
    def child_to_ir(cls, symbol: RawSymbolData) -> type[IrData] | None:
        raise NotImplementedError("Functions should not have children")

    @classmethod
    def child_to_field_name(cls, child: RawSymbolData) -> str:
        raise NotImplementedError("Functions should not have children")


class PyFnCollection(IrCollection):
    data: dict[str, PyFnData | list[PyFnData]]


class PyClassData(ClassData):
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
            SymbolKind.CALLABLE: PyFnData,
            SymbolKind.CLASS: None,  # for child classes and structs we just list them
        }
        return mapping.get(symbol.symbol_kind)

    @classmethod
    def child_to_field_name(cls, child: RawSymbolData) -> str:
        mapping = {
            SymbolKind.CALLABLE: ScopeRelation.METHOD,
            SymbolKind.CLASS: ScopeRelation.NESTED_CLASS,
        }
        return mapping.get(child.symbol_kind)


class PyClassCollection(IrCollection):
    data: dict[str, PyClassData | list[PyClassData]]


# Symbol extraction classes
class PyVariableRawSymbolCollection(RawSymbolCollection):
    data: dict[str, RawSymbolData]

    @classmethod
    def from_static_analysis(cls, code: str, root_rel_path: Path) -> Self | None:
        return default_ctags_analysis(
            collection_cls=cls,
            code=code,
            root_rel_path=root_rel_path,
            symbol_kind=SymbolKind.VARIABLE,
            ctags_kinds=PY_VARIABLES,
            delimiter=".",
            add_symbol_padding=True,
        )

    @classmethod
    def from_llm(cls, code: str, root_rel_path: str) -> Self:
        raise NotImplementedError("Static analysis should be used for Py variables")

    def to_dict(self) -> dict[str, RawSymbolData]:
        return self.data


class PyFnRawSymbolCollection(RawSymbolCollection):
    data: dict[str, RawSymbolData]

    @classmethod
    def from_static_analysis(cls, code: str, root_rel_path: Path) -> Self | None:
        return default_ctags_analysis(
            collection_cls=cls,
            code=code,
            root_rel_path=root_rel_path,
            symbol_kind=SymbolKind.CALLABLE,
            ctags_kinds=PY_FUNCTIONS,
            delimiter=".",
            add_symbol_padding=False,
        )

    @classmethod
    def from_llm(cls, code: str, root_rel_path: str) -> Self:
        raise NotImplementedError("Static analysis should be used for Py functions")

    def to_dict(self) -> dict[str, RawSymbolData]:
        return self.data


class PyClassRawSymbolCollection(RawSymbolCollection):
    data: dict[str, RawSymbolData]

    @classmethod
    def from_static_analysis(cls, code: str, root_rel_path: Path) -> Self | None:
        is_multi_prompt = code_requires_multi_prompt(code)

        symbols = extract_symbols_w_ctags(
            root_rel_path=root_rel_path, file_content=code
        )

        class_raw_symbol_data = {}
        for s in symbols:
            if s["kind"] in PY_CLASS:
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
                (s.get("scope") is not None)
                and not s["name"].startswith("__anon")
                and s.get("scopeKind") in PY_CLASS
            ):
                scope_split = s["scope"].split(".")[-1]
                if scope_split in class_raw_symbol_data:
                    if s["kind"] in PY_METHODS:
                        class_raw_symbol_data[scope_split].children.append(
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
                    elif s["kind"] in PY_CLASS:
                        class_raw_symbol_data[scope_split].children.append(
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
        output = (
            None if len(class_raw_symbol_data) == 0 else cls(data=class_raw_symbol_data)
        )
        return output

    @classmethod
    def from_llm(cls, code: str, root_rel_path: str) -> Self:
        raise NotImplementedError("Static analysis should be used for Py classes")

    def to_dict(self) -> dict[str, RawSymbolData]:
        return self.data


variables_dict_from_llm_py = partial(
    PyVariableCollection.dict_from_llm,
    PyVariableData,
)

class_dict_from_llm_py = partial(
    PyClassCollection.dict_from_llm,
    PyClassData,
)

fn_dict_from_llm_py = partial(
    PyFnCollection.dict_from_llm,
    PyFnData,
)
