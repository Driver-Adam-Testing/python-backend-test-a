from pathlib import Path
from typing import Self

from pydantic import Field, PrivateAttr
from shared.agent.chat_openai import ChatOpenAI
from shared.inspector.utils.treesitter_drivers.ruby_driver import (
    RubyCallableBespokeMarker,
    RubyClassModuleBespokeMarker,
    RubyDriverTree,
    RubyMethodKind,
    RubyRequireBespokeMarker,
    RubyVariableBespokeMarker,
    RubyVariableKind,
)
from shared.prompts.structured_prompting import (
    GENERAL_STE_STYLE_INSTRUCTION,
    NO_RESTATEMENT_STYLE_INSTRUCTION_FOR_SYMBOLS,
    USE_BACKTICKS_STYLE_INSTRUCTION,
    Component,
    Prompt,
)

from .ir_common import (
    FieldNameWithBackTickContent,
    FieldNameWithRawContent,
    FnData,
    IrCollection,
    IrData,
    ListedBacktickNameRawContentWithNone,
    ListedRawContentNoNone,
    ListedRawContentWithNone,
    RawContent,
)
from .symbol_common import (
    RawSymbolCollection,
    RawSymbolData,
    ReifiedSymbol,
    SymbolKind,
    code_requires_multi_prompt,
)

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

VARIABLES_FOUND_SYSTEM_PROMPT_JSON = """
You are an expert Ruby programmer and a software engineering documentation expert. You write detailed documentation to explain code written in Ruby.

You focus on writing technical documentation for variable and constant symbols. You are skilled at explaining technical details as well as recognizing and articulating the key conceptual components and purpose of software.

You will be given the name of a variable or constant to document and the source code where the symbol is defined.

Your job is to describe the symbol. **Always respond using exactly the following JSON schema**:
{
    "description": <1 to 3 sentence description of the variable or constant>,
    "use": <Terse 1 sentence description of how this variable or constant is used>,
}

Return JSON according to the schema above. Do not use the format ```json ... ```, just return the JSON data.
"""

VARIABLES_FOUND_USER_PROMPT = """
Summarize the variable or constant in the code provided below.

- When describing a variable or constant, provide detail that matches the complexity of the symbol. Large and complex symbols (e.g., containing large struct instances) should get longer explanations, while small ones (e.g., one line definitions) much less.

Variable or constant to document:
"""

CLASSES_FOUND_SYSTEM_PROMPT_JSON = """
You are an expert Ruby programmer and a software engineering documentation expert. You write detailed documentation to explain code written in Ruby.

You focus on writing technical documentation for classes in Ruby. You are skilled at explaining technical details as well as recognizing and articulating the key conceptual components and purpose of software.

You will be given the name of an class to document and the source code where the class is defined.

Your job is to describe the class. **Always respond using exactly the following JSON schema**:
{
    "description": <one paragraph description of the class>,
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
}
Return JSON according to the schema above. Do not use the format ```json ... ```, just return the JSON data.
"""

MODULES_FOUND_USER_PROMPT = """
Summarize the module in the code provided below.

- When describing an important module, provide detail that matches the complexity of the module. Large and complex module should get longer explanations, while small ones a single sentence.

Module to document:
"""


class RubyVariableData(IrData):
    description: FieldNameWithRawContent
    use: FieldNameWithRawContent
    _access: FieldNameWithBackTickContent

    @classmethod
    def system_prompt(cls, symbol: RawSymbolData) -> str:
        return (
            Prompt.empty()
            .append(Component(string=VARIABLES_FOUND_SYSTEM_PROMPT_JSON))
            .append(GENERAL_STE_STYLE_INSTRUCTION)
            .append(USE_BACKTICKS_STYLE_INSTRUCTION)
            .into_str()
        )

    @classmethod
    def user_prompt(cls, symbol: RawSymbolData) -> str:
        user_prompt = (
            Prompt.empty()
            .append(Component(string=f"{VARIABLES_FOUND_USER_PROMPT}{symbol.name}"))
            .append(NO_RESTATEMENT_STYLE_INSTRUCTION_FOR_SYMBOLS)
            .append(
                Component(string=f"Variable or Constant Code:\n\n{symbol.symbol_code}")
            )
        )
        if symbol.file_code:
            user_prompt.append(
                Component(string=f"\n\nFull File Code:\n\n{symbol.file_code}")
            )
        return user_prompt.into_str()

    @classmethod
    def child_to_ir(cls, symbol: RawSymbolData) -> IrData | None:
        raise NotImplementedError("Variables and constants should not have children")

    @classmethod
    def child_to_field_name(cls, child: RawSymbolData) -> str:
        raise NotImplementedError("Variables and constants should not have children")

    @classmethod
    def default_instance(cls, reified_symbol: ReifiedSymbol | None = None) -> Self:
        return cls(
            description=FieldNameWithRawContent(content=""),
            use=FieldNameWithRawContent(content=""),
            _access=FieldNameWithBackTickContent(content=""),
        )

    def _apply_bespoke_data(self) -> None:
        bespoke_data: RubyVariableBespokeMarker = self._reified_symbol.raw.bespoke_data
        if bespoke_data.access:
            self._access = FieldNameWithBackTickContent(
                content=bespoke_data.access.value
            )


class RubyMethodData(FnData):
    single_sentence: RawContent
    _kind: FieldNameWithRawContent
    inputs: ListedBacktickNameRawContentWithNone
    logic_and_control_flow: ListedRawContentWithNone
    output: FieldNameWithRawContent
    _visibility: FieldNameWithBackTickContent

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

    def _apply_bespoke_data(self) -> None:
        bespoke_data: RubyCallableBespokeMarker = self._reified_symbol.raw.bespoke_data

        if bespoke_data.kind == RubyMethodKind.TOP_LEVEL:
            self._visibility = FieldNameWithBackTickContent(content="")
            self._kind = FieldNameWithRawContent(content="")
        elif (
            bespoke_data.kind == RubyMethodKind.CLASS_METHOD
            or bespoke_data.kind == RubyMethodKind.MODULE_METHOD
            or bespoke_data.kind == RubyMethodKind.INSTANCE_METHOD
        ):
            if bespoke_data.visibility:
                self._visibility = FieldNameWithBackTickContent(
                    content=bespoke_data.visibility.value
                )
            else:
                self._visibility = FieldNameWithBackTickContent(content="")
            self._kind = FieldNameWithRawContent(content=bespoke_data.kind.value)
        else:
            raise ValueError(f"Unexpected method kind: {bespoke_data.kind}")

    @classmethod
    def default_instance(cls, reified_symbol: ReifiedSymbol | None = None) -> Self:
        from .ir_common import ListedRawContentWithNone

        return cls(
            single_sentence=RawContent(content=""),
            _kind=FieldNameWithRawContent(content=""),
            inputs=ListedBacktickNameRawContentWithNone(content=[]),
            logic_and_control_flow=ListedRawContentWithNone(content=[]),
            output=FieldNameWithRawContent(content=""),
            _visibility=FieldNameWithBackTickContent(content=""),
        )


class RubyClassData(IrData):
    description: FieldNameWithRawContent
    _prepends: ListedRawContentNoNone
    _includes: ListedRawContentNoNone
    _extends: ListedRawContentNoNone

    _supported_child_ordering: list[str] = PrivateAttr(
        default=[
            "Constants",
            "Variables",
            "Attributes",
            "Class Methods",
            "Instance Methods",
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
            SymbolKind.VARIABLE_DEFINITION: RubyVariableData,
        }
        return mapping.get(symbol.symbol_kind)

    @classmethod
    def child_to_field_name(cls, child: RawSymbolData) -> str:
        if child.symbol_kind == SymbolKind.VARIABLE_DEFINITION:
            bespoke_data: RubyVariableBespokeMarker = (
                child.reified_symbol.raw.bespoke_data
            )
            match bespoke_data.kind:
                case RubyVariableKind.CONSTANT:
                    return "Constants"
                case RubyVariableKind.VARIABLE:
                    return "Variables"
                case RubyVariableKind.ATTRIBUTE:
                    return "Attributes"
                case _:
                    raise ValueError(f"Unexpected variable kind: {bespoke_data.kind}")

        elif child.symbol_kind == SymbolKind.CALLABLE:
            bespoke_data: RubyCallableBespokeMarker = (
                child.reified_symbol.raw.bespoke_data
            )
            match bespoke_data.kind:
                case RubyMethodKind.CLASS_METHOD:
                    return "Class Methods"
                case RubyMethodKind.INSTANCE_METHOD:
                    return "Instance Methods"
                case _:
                    raise ValueError(f"Unexpected method kind: {bespoke_data.kind}")
        else:
            raise ValueError(f"Unexpected child symbol kind: {child.symbol_kind}")

    def _apply_bespoke_data(self) -> None:
        """Apply bespoke data from tree-sitter extraction to populate includes/extends/prepends."""
        bespoke_data: RubyClassModuleBespokeMarker = (
            self._reified_symbol.raw.bespoke_data
        )

        if bespoke_data.prepended_modules:
            self._prepends = ListedRawContentNoNone(
                content=list(bespoke_data.prepended_modules)
            )

        if bespoke_data.included_modules:
            self._includes = ListedRawContentNoNone(
                content=list(bespoke_data.included_modules)
            )

        if bespoke_data.extended_modules:
            self._extends = ListedRawContentNoNone(
                content=list(bespoke_data.extended_modules)
            )

    @classmethod
    def default_instance(cls, reified_symbol: ReifiedSymbol | None = None) -> Self:
        return cls(
            description=FieldNameWithRawContent(content=""),
            _prepends=ListedRawContentNoNone(content=[]),
            _includes=ListedRawContentNoNone(content=[]),
            _extends=ListedRawContentNoNone(content=[]),
        )


class RubyModuleData(IrData):
    description: FieldNameWithRawContent
    _prepends: ListedRawContentNoNone
    _includes: ListedRawContentNoNone
    _extends: ListedRawContentNoNone

    _supported_child_ordering: list[str] = PrivateAttr(
        default=[
            "Constants",
            "Variables",
            "Attributes",
            "Module Methods",
            "Instance Methods",
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
            SymbolKind.VARIABLE_DEFINITION: RubyVariableData,
        }
        return mapping.get(symbol.symbol_kind)

    @classmethod
    def child_to_field_name(cls, child: RawSymbolData) -> str:
        if child.symbol_kind == SymbolKind.VARIABLE_DEFINITION:
            bespoke_data: RubyVariableBespokeMarker = (
                child.reified_symbol.raw.bespoke_data
            )
            match bespoke_data.kind:
                case RubyVariableKind.CONSTANT:
                    return "Constants"
                case RubyVariableKind.VARIABLE:
                    return "Variables"
                case RubyVariableKind.ATTRIBUTE:
                    return "Attributes"
                case _:
                    raise ValueError(f"Unexpected variable kind: {bespoke_data.kind}")

        elif child.symbol_kind == SymbolKind.CALLABLE:
            bespoke_data: RubyCallableBespokeMarker = (
                child.reified_symbol.raw.bespoke_data
            )
            match bespoke_data.kind:
                case RubyMethodKind.MODULE_METHOD:
                    return "Module Methods"
                case RubyMethodKind.INSTANCE_METHOD:
                    return "Instance Methods"
                case _:
                    raise ValueError(
                        f"Unexpected method kind in module: {bespoke_data.kind}"
                    )
        else:
            raise ValueError(f"Unexpected child symbol kind: {child.symbol_kind}")

    def _apply_bespoke_data(self) -> None:
        bespoke_data: RubyClassModuleBespokeMarker = (
            self._reified_symbol.raw.bespoke_data
        )

        if bespoke_data.prepended_modules:
            self._prepends = ListedRawContentNoNone(
                content=list(bespoke_data.prepended_modules)
            )

        if bespoke_data.included_modules:
            self._includes = ListedRawContentNoNone(
                content=list(bespoke_data.included_modules)
            )

        if bespoke_data.extended_modules:
            self._extends = ListedRawContentNoNone(
                content=list(bespoke_data.extended_modules)
            )

    @classmethod
    def default_instance(cls, reified_symbol: ReifiedSymbol | None = None) -> Self:
        return cls(
            description=FieldNameWithRawContent(content=""),
            prepends=ListedRawContentNoNone(content=[]),
            includes=ListedRawContentNoNone(content=[]),
            extends=ListedRawContentNoNone(content=[]),
        )


class RubyImportRawSymbolCollection(RawSymbolCollection):
    data: dict[str, RawSymbolData]
    relative_requires: set[str] = Field(default_factory=set)

    @classmethod
    def from_static_analysis(cls, code: str, root_rel_path: Path) -> Self | None:
        driver_tree = RubyDriverTree.from_code(code, root_rel_path)
        is_large_file = code_requires_multi_prompt(code)
        import_symbols = driver_tree._extract_requires()

        if not import_symbols:
            return None

        import_dict = {}
        relative_set = set()

        for import_symbol in import_symbols:
            if import_symbol.name:
                bespoke_data: RubyRequireBespokeMarker = import_symbol.bespoke_data
                if bespoke_data.is_relative:
                    relative_set.add(import_symbol.name)

                raw_symbol_data = RawSymbolData.from_tree_sitter_raw_symbol(
                    ts_symbol=import_symbol,
                    path=root_rel_path,
                    scope=None,
                    scope_relation=None,
                    children=[],
                    reference_code=None,
                    delimiter=None,
                    is_large_file=is_large_file,
                    is_overloaded=False,
                    use_padding=False,
                    code=code,
                    reified_symbol=None,
                )
                import_dict[import_symbol.name] = raw_symbol_data

        return cls(data=import_dict, relative_requires=relative_set)

    @classmethod
    def from_llm(cls, code: str, root_rel_path: str) -> Self:
        raise NotImplementedError("Static analysis should be used for Ruby requires")

    def to_dict(self) -> dict[str, RawSymbolData]:
        return self.data


class RubyTopLevelConstantRawSymbolCollection(RawSymbolCollection):
    data: dict[str, RawSymbolData]

    @classmethod
    def from_static_analysis(
        cls, code: str, root_rel_path: Path, reified_symbols: list[ReifiedSymbol]
    ) -> Self | None:
        top_level_constants = [
            reified_symbol
            for reified_symbol in reified_symbols
            if reified_symbol.raw.symbol_kind == SymbolKind.VARIABLE_DEFINITION
            and reified_symbol.raw.bespoke_data.is_top_level
            and reified_symbol.raw.bespoke_data.kind == RubyVariableKind.CONSTANT
        ]

        constant_raw_symbol_data = {}
        is_large_file = code_requires_multi_prompt(code)

        for top_level_constant in top_level_constants:
            if top_level_constant.raw.name is not None:
                raw_symbol_data = RawSymbolData.from_tree_sitter_raw_symbol(
                    ts_symbol=top_level_constant.raw,
                    path=root_rel_path,
                    scope=None,
                    scope_relation=None,
                    children=[],
                    reference_code=None,
                    delimiter="::",
                    is_large_file=is_large_file,
                    is_overloaded=False,
                    use_padding=False,
                    code=code,
                    reified_symbol=top_level_constant,
                )
                constant_raw_symbol_data[top_level_constant.raw.name] = raw_symbol_data

        return (
            None
            if len(constant_raw_symbol_data) == 0
            else cls(data=constant_raw_symbol_data)
        )

    @classmethod
    def from_llm(cls, code: str, root_rel_path: str) -> Self:
        raise NotImplementedError(
            "Static analysis should be used for Ruby top-level constants"
        )

    def to_dict(self) -> dict[str, RawSymbolData]:
        return self.data


class RubyTopLevelVariableRawSymbolCollection(RawSymbolCollection):
    data: dict[str, RawSymbolData]

    @classmethod
    def from_static_analysis(
        cls, code: str, root_rel_path: Path, reified_symbols: list[ReifiedSymbol]
    ) -> Self | None:
        from utils.treesitter_drivers.ruby_driver import RubyVariableKind

        top_level_variables = [
            reified_symbol
            for reified_symbol in reified_symbols
            if reified_symbol.raw.symbol_kind == SymbolKind.VARIABLE_DEFINITION
            and reified_symbol.is_definition
            and reified_symbol.raw.bespoke_data.is_top_level
            and reified_symbol.raw.bespoke_data.kind == RubyVariableKind.VARIABLE
        ]

        variable_raw_symbol_data = {}
        is_large_file = code_requires_multi_prompt(code)

        for top_level_variable in top_level_variables:
            if top_level_variable.raw.name is not None:
                raw_symbol_data = RawSymbolData.from_tree_sitter_raw_symbol(
                    ts_symbol=top_level_variable.raw,
                    path=root_rel_path,
                    scope=None,
                    scope_relation=None,
                    children=[],
                    reference_code=None,
                    delimiter="::",
                    is_large_file=is_large_file,
                    is_overloaded=False,
                    use_padding=False,
                    code=code,
                    reified_symbol=top_level_variable,
                )
                variable_raw_symbol_data[top_level_variable.raw.name] = raw_symbol_data

        return (
            None
            if len(variable_raw_symbol_data) == 0
            else cls(data=variable_raw_symbol_data)
        )

    @classmethod
    def from_llm(cls, code: str, root_rel_path: str) -> Self:
        raise NotImplementedError(
            "Static analysis should be used for Ruby top-level variables"
        )

    def to_dict(self) -> dict[str, RawSymbolData]:
        return self.data


class RubyTopLevelMethodRawSymbolCollection(RawSymbolCollection):
    data: dict[str, RawSymbolData]

    @classmethod
    def from_static_analysis(
        cls, code: str, root_rel_path: Path, reified_symbols: list[ReifiedSymbol]
    ) -> Self | None:
        top_level_methods = [
            reified_symbol
            for reified_symbol in reified_symbols
            if reified_symbol.raw.symbol_kind == SymbolKind.CALLABLE
            and reified_symbol.is_definition
            and reified_symbol.raw.bespoke_data.kind == RubyMethodKind.TOP_LEVEL
        ]

        method_raw_symbol_data = {}
        for top_level_method in top_level_methods:
            if top_level_method.raw.name is not None:
                raw_symbol_data = RawSymbolData.from_tree_sitter_raw_symbol(
                    ts_symbol=top_level_method.raw,
                    path=root_rel_path,
                    scope=None,
                    scope_relation=None,
                    children=[],
                    reference_code=None,
                    delimiter="::",
                    is_large_file=code_requires_multi_prompt(code),
                    is_overloaded=False,
                    use_padding=False,
                    code=code,
                    reified_symbol=top_level_method,
                )
                method_raw_symbol_data[top_level_method.raw.name] = raw_symbol_data

        return (
            None
            if len(method_raw_symbol_data) == 0
            else cls(data=method_raw_symbol_data)
        )

    @classmethod
    def from_llm(cls, code: str, root_rel_path: str) -> Self:
        raise NotImplementedError("Static analysis should be used for Ruby methods")

    @classmethod
    def to_dict(self) -> dict[str, RawSymbolData]:
        return self.data


class RubyClassRawSymbolCollection(RawSymbolCollection):
    data: dict[str, RawSymbolData]

    @classmethod
    def from_static_analysis(
        cls, code: str, root_rel_path: Path, reified_symbols: list[ReifiedSymbol]
    ) -> Self | None:
        class_symbols = [
            reified_symbol
            for reified_symbol in reified_symbols
            if reified_symbol.raw.symbol_kind == SymbolKind.CLASS
            and reified_symbol.is_definition
            and not reified_symbol.raw.bespoke_data.is_module
        ]

        class_raw_symbol_data = {}
        is_large_file = code_requires_multi_prompt(code)

        for class_symbol in class_symbols:
            if class_symbol.raw.name is not None:
                raw_symbol_data = RawSymbolData.from_tree_sitter_raw_symbol(
                    ts_symbol=class_symbol.raw,
                    path=root_rel_path,
                    scope=None,
                    scope_relation=None,
                    children=[],
                    reference_code=None,
                    delimiter="::",
                    is_large_file=is_large_file,
                    is_overloaded=False,
                    use_padding=False,
                    code=code,
                    reified_symbol=class_symbol,
                )

                for child in class_symbol.children:
                    if (
                        child.raw.symbol_kind == SymbolKind.CALLABLE
                        or child.raw.symbol_kind == SymbolKind.VARIABLE_DEFINITION
                    ) and child.raw.file_path == class_symbol.raw.file_path:
                        raw_symbol_data.children.append(
                            RawSymbolData.from_tree_sitter_raw_symbol(
                                ts_symbol=child.raw,
                                path=root_rel_path,
                                scope=class_symbol.raw.name,
                                scope_relation=None,
                                children=[],
                                reference_code=None,
                                delimiter="::",
                                is_large_file=is_large_file,
                                is_overloaded=False,
                                use_padding=False,
                                code=code,
                                reified_symbol=child,
                            )
                        )

                class_raw_symbol_data[class_symbol.raw.name] = raw_symbol_data

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
    def from_static_analysis(
        cls, code: str, root_rel_path: Path, reified_symbols: list[ReifiedSymbol]
    ) -> Self | None:
        module_symbols = [
            reified_symbol
            for reified_symbol in reified_symbols
            if reified_symbol.raw.symbol_kind
            == SymbolKind.CLASS  # CLASS is used for both classes and modules
            and reified_symbol.is_definition
            and reified_symbol.raw.bespoke_data.is_module
        ]

        module_raw_symbol_data = {}
        is_large_file = code_requires_multi_prompt(code)

        for module_symbol in module_symbols:
            if module_symbol.raw.name is not None:
                raw_symbol_data = RawSymbolData.from_tree_sitter_raw_symbol(
                    ts_symbol=module_symbol.raw,
                    path=root_rel_path,
                    scope=None,
                    scope_relation=None,
                    children=[],
                    reference_code=None,
                    delimiter="::",
                    is_large_file=is_large_file,
                    is_overloaded=False,
                    use_padding=False,
                    code=code,
                    reified_symbol=module_symbol,
                )

                for child in module_symbol.children:
                    if (
                        child.raw.symbol_kind == SymbolKind.CALLABLE
                        or child.raw.symbol_kind == SymbolKind.VARIABLE_DEFINITION
                    ) and child.raw.file_path == module_symbol.raw.file_path:
                        raw_symbol_data.children.append(
                            RawSymbolData.from_tree_sitter_raw_symbol(
                                ts_symbol=child.raw,
                                path=root_rel_path,
                                scope=module_symbol.raw.name,
                                scope_relation=None,
                                children=[],
                                reference_code=None,
                                delimiter="::",
                                is_large_file=is_large_file,
                                is_overloaded=False,
                                use_padding=False,
                                code=code,
                                reified_symbol=child,
                            )
                        )

                module_raw_symbol_data[module_symbol.raw.name] = raw_symbol_data

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


class RubyTopLevelConstantCollection(IrCollection):
    data: dict[str, RubyVariableData | list[RubyVariableData]]

    @classmethod
    def from_llm(cls, llm: ChatOpenAI, symbols_list: RawSymbolCollection) -> Self:
        return cls.from_llm_with_ir_data(RubyVariableData, llm, symbols_list)


class RubyTopLevelVariableCollection(IrCollection):
    data: dict[str, RubyVariableData | list[RubyVariableData]]

    @classmethod
    def from_llm(cls, llm: ChatOpenAI, symbols_list: RawSymbolCollection) -> Self:
        return cls.from_llm_with_ir_data(RubyVariableData, llm, symbols_list)


class RubyMethodCollection(IrCollection):
    data: dict[str, RubyMethodData | list[RubyMethodData]]

    @classmethod
    def from_llm(cls, llm: ChatOpenAI, symbols_list: RawSymbolCollection) -> Self:
        return cls.from_llm_with_ir_data(RubyMethodData, llm, symbols_list)


class RubyClassCollection(IrCollection):
    data: dict[str, RubyClassData | list[RubyClassData]]

    @classmethod
    def from_llm(cls, llm: ChatOpenAI, symbols_list: RawSymbolCollection) -> Self:
        return cls.from_llm_with_ir_data(RubyClassData, llm, symbols_list)


class RubyModuleCollection(IrCollection):
    data: dict[str, RubyModuleData | list[RubyModuleData]]

    @classmethod
    def from_llm(cls, llm: ChatOpenAI, symbols_list: RawSymbolCollection) -> Self:
        return cls.from_llm_with_ir_data(RubyModuleData, llm, symbols_list)


def render_ruby_imports(collection: "RubyImportRawSymbolCollection") -> str:
    markdown = "\n---\n"

    absolute = [
        name for name in collection.data if name not in collection.relative_requires
    ]
    relative = [
        name for name in collection.data if name in collection.relative_requires
    ]

    if absolute:
        markdown += "**Requires**\n"
        for req in sorted(absolute):
            markdown += f"- `{req}`\n"
        markdown += "\n"

    if relative:
        markdown += "**Relative Requires**\n"
        for req in sorted(relative):
            markdown += f"- `{req}`\n"
        markdown += "\n"

    return markdown
