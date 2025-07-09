from shared.prompts.structured_prompting import (
    GENERAL_STE_STYLE_INSTRUCTION,
    NO_RESTATEMENT_STYLE_INSTRUCTION_FOR_CODE_PURPOSE,
    USE_BACKTICKS_STYLE_INSTRUCTION,
    Component,
    Prompt,
)
from utils.lang_specialization.default import (
    default_imports_checker,
)
from utils.lang_specialization.rust import (
    SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT,
    SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_RUST,
    RustDataStructureCollection,
    RustDataStructureRawSymbolCollection,
    RustFnCollection,
    RustFnRawSymbolCollection,
    RustMacroCollection,
    RustMacroRawSymbolCollection,
    RustTraitCollection,
    RustTraitsRawSymbolCollection,
    RustVariableCollection,
    RustVariablesRawSymbolCollection,
)
from utils.templates import S

SOURCE_CODE_LARGE_TEMPLATE_RUST = [
    (
        S.SINGLE_PROMPT_TEXT,
        "# Purpose",
        Prompt.empty()
        .append(Component(string=SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_RUST))
        .append(GENERAL_STE_STYLE_INSTRUCTION)
        .append(USE_BACKTICKS_STYLE_INSTRUCTION)
        .into_str(),
        Prompt.empty()
        .append(Component(string=SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT))
        .append(NO_RESTATEMENT_STYLE_INSTRUCTION_FOR_CODE_PURPOSE)
        .into_str(),
    ),
    (
        S.LLM_COND_JSON,
        "# Imports and Dependencies",
        default_imports_checker,
        lambda _llm, output, _code: output,
        None,
    ),
    (
        S.FN_COND_JSON,
        "# Global Variables",
        RustVariablesRawSymbolCollection.from_static_analysis,
        RustVariableCollection.from_llm,
        None,
    ),
    (
        S.FN_COND_JSON,
        "# Macros",
        RustMacroRawSymbolCollection.from_static_analysis,
        RustMacroCollection.from_llm,
        None,
    ),
    (
        S.FN_COND_JSON,
        "# Traits",
        RustTraitsRawSymbolCollection.from_static_analysis,
        RustTraitCollection.from_llm,
        None,
    ),
    (
        S.FN_COND_JSON,
        "# Data Structures",
        RustDataStructureRawSymbolCollection.from_static_analysis,
        RustDataStructureCollection.from_llm,
        None,
    ),
    (
        S.FN_COND_JSON,
        "# Functions",
        RustFnRawSymbolCollection.from_static_analysis,
        RustFnCollection.from_llm,
        None,
    ),
]
